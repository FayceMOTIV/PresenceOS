"""
PresenceOS — Engage API v2 (Sprint 5)

Unified inbox: comments, DMs, classification, reply generation.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.engager.inbox_manager import InboxManager
from app.services.engager.comment_fetcher import MetaCommentFetcher, MockCommentFetcher

router = APIRouter()


# ── Request / Response models ──


class ScanRequest(BaseModel):
    since_hours: int = Field(default=24, ge=1, le=8760, description="Lookback window in hours (max 1 year)")


class ScanResponse(BaseModel):
    fetched: int
    classified: int
    replies_generated: int
    stored: int = 0


class ApproveRequest(BaseModel):
    final_reply: str | None = Field(
        default=None,
        max_length=2000,
        description="Edited reply (uses suggested_reply if null)",
    )


class CommentResponse(BaseModel):
    id: str
    platform: str
    author_name: str
    text: str
    sentiment: str
    urgency_score: float
    suggested_reply: str
    reply_status: str
    final_reply: str
    created_at: str
    is_dm: bool


class StatsResponse(BaseModel):
    brand_id: str
    total: int
    pending: int
    classified: int
    approved: int
    published: int
    skipped: int
    avg_urgency: float
    last_scan: str | None


# ── Endpoints ──


@router.post(
    "/{brand_id}/scan",
    response_model=ScanResponse,
    summary="Scan & process new comments",
)
@limiter.limit("10/minute")
async def scan_comments(
    request: Request,
    brand_id: str,
    body: ScanRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Fetch new comments, classify them, generate replies, store in Firestore."""
    await verify_brand_access(brand_id, user, db)
    # Use real Meta Graph API when token is configured, else mock
    from app.services.meta_token_manager import MetaTokenManager
    manager = MetaTokenManager()
    meta_token = await manager.get_token()
    if meta_token:
        fetcher = MetaCommentFetcher(
            instagram_account_id=settings.meta_instagram_account_id,
        )
    else:
        fetcher = MockCommentFetcher()

    manager = InboxManager(fetcher=fetcher)
    result = await manager.scan_and_process(
        brand_id=brand_id,
        access_token=meta_token,
        since_hours=body.since_hours,
    )
    return result


@router.get(
    "/{brand_id}/inbox",
    response_model=list[CommentResponse],
    summary="Get inbox items",
)
@limiter.limit("60/minute")
async def get_inbox(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    status_filter: str | None = None,
    limit: int = 50,
):
    """Get comments/DMs from the inbox, optionally filtered by status."""
    await verify_brand_access(brand_id, user, db)
    manager = InboxManager()
    comments = await manager.get_inbox(
        brand_id=brand_id,
        status=status_filter,
        limit=limit,
    )
    return [c.to_dict() for c in comments]


@router.post(
    "/{brand_id}/inbox/{comment_id}/approve",
    response_model=CommentResponse,
    summary="Approve a reply",
)
@limiter.limit("30/minute")
async def approve_reply(
    request: Request,
    brand_id: str,
    comment_id: str,
    body: ApproveRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Approve a suggested reply, optionally editing it before publishing."""
    await verify_brand_access(brand_id, user, db)
    manager = InboxManager()
    comment = await manager.approve_reply(
        brand_id=brand_id,
        comment_id=comment_id,
        final_reply=body.final_reply,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment {comment_id} not found",
        )
    return comment.to_dict()


@router.post(
    "/{brand_id}/inbox/{comment_id}/reject",
    summary="Reject a reply",
)
@limiter.limit("30/minute")
async def reject_reply(
    request: Request,
    brand_id: str,
    comment_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Reject a suggested reply."""
    await verify_brand_access(brand_id, user, db)
    manager = InboxManager()
    comment = await manager.reject_reply(
        brand_id=brand_id,
        comment_id=comment_id,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment {comment_id} not found",
        )
    return comment.to_dict()


@router.get(
    "/{brand_id}/stats",
    response_model=StatsResponse,
    summary="Get inbox stats",
)
@limiter.limit("60/minute")
async def get_stats(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Get engagement statistics for the brand inbox."""
    await verify_brand_access(brand_id, user, db)
    manager = InboxManager()
    stats = await manager.get_stats(brand_id)
    return stats
