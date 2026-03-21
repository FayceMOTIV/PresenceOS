"""
PresenceOS - Validation v2 Endpoints (Sprint 8)

Approval queue for autopilot-generated pending posts.
Endpoints:
  GET  /brands/{brand_id}/validation/pending           — List pending posts
  POST /brands/{brand_id}/validation/{post_id}/approve  — Approve a post
  POST /brands/{brand_id}/validation/{post_id}/reject   — Reject a post
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.models.autopilot import PendingPost, PendingPostStatus

logger = structlog.get_logger()
router = APIRouter()


# ── Response / Request Schemas ─────────────────────────────────────


class PendingPostV2Response(BaseModel):
    id: UUID
    caption: str
    platform: str
    image_url: Optional[str] = None  # First media_url for backward compat
    media_urls: Optional[list[str]] = None
    hashtags: Optional[list[str]] = None
    status: str
    scheduled_at: Optional[datetime] = None  # expires_at used as proxy
    ai_reasoning: Optional[str] = None
    virality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional reason for rejection",
    )


# ── Helpers ────────────────────────────────────────────────────────


def _to_response(post: PendingPost) -> dict:
    """Convert PendingPost ORM to response dict with image_url convenience field."""
    return {
        "id": post.id,
        "caption": post.caption,
        "platform": post.platform,
        "image_url": post.media_urls[0] if post.media_urls else None,
        "media_urls": post.media_urls,
        "hashtags": post.hashtags,
        "status": post.status.value if hasattr(post.status, "value") else post.status,
        "scheduled_at": post.expires_at,  # expires_at serves as scheduled_at proxy
        "ai_reasoning": post.ai_reasoning,
        "virality_score": post.virality_score,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


# ── Endpoints ──────────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/validation/pending",
    response_model=list[PendingPostV2Response],
)
@limiter.limit("60/minute")
async def list_pending_posts(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List pending posts for a brand's approval queue.

    Returns posts with status=PENDING, ordered by creation date (newest first).
    """
    brand = await verify_brand_access(str(brand_id), current_user, db)

    query = (
        select(PendingPost)
        .where(
            PendingPost.brand_id == brand.id,
            PendingPost.status == PendingPostStatus.PENDING,
        )
        .order_by(PendingPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    posts = result.scalars().all()

    return [_to_response(p) for p in posts]


@router.post(
    "/brands/{brand_id}/validation/{post_id}/approve",
    response_model=PendingPostV2Response,
)
@limiter.limit("30/minute")
async def approve_post(
    request: Request,
    brand_id: UUID,
    post_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
):
    """Approve a pending post. Changes status from PENDING to APPROVED."""
    brand = await verify_brand_access(str(brand_id), current_user, db)

    # Fetch post
    result = await db.execute(
        select(PendingPost).where(PendingPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending post not found",
        )

    # Ownership check: post must belong to this brand
    if post.brand_id != brand.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: post does not belong to this brand",
        )

    # Status guard: only PENDING can be approved
    if post.status != PendingPostStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post already processed: {post.status.value}",
        )

    post.status = PendingPostStatus.APPROVED
    post.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(post)

    logger.info(
        "Post approved via validation v2",
        brand_id=str(brand.id),
        post_id=str(post.id),
    )

    return _to_response(post)


@router.post(
    "/brands/{brand_id}/validation/{post_id}/reject",
    response_model=PendingPostV2Response,
)
@limiter.limit("30/minute")
async def reject_post(
    request: Request,
    brand_id: UUID,
    post_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
    body: Optional[RejectRequest] = None,
):
    """Reject a pending post with optional reason."""
    brand = await verify_brand_access(str(brand_id), current_user, db)

    # Fetch post
    result = await db.execute(
        select(PendingPost).where(PendingPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending post not found",
        )

    # Ownership check
    if post.brand_id != brand.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: post does not belong to this brand",
        )

    # Status guard
    if post.status != PendingPostStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post already processed: {post.status.value}",
        )

    post.status = PendingPostStatus.REJECTED
    post.reviewed_at = datetime.now(timezone.utc)

    # Log rejection reason (stored in ai_reasoning field as supplemental info)
    rejection_reason = body.reason if body else None
    if rejection_reason:
        existing = post.ai_reasoning or ""
        post.ai_reasoning = f"{existing}\n[REJECTED] {rejection_reason}".strip()

    await db.commit()
    await db.refresh(post)

    logger.info(
        "Post rejected via validation v2",
        brand_id=str(brand.id),
        post_id=str(post.id),
        reason=rejection_reason,
    )

    return _to_response(post)
