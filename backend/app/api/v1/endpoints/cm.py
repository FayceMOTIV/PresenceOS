"""
PresenceOS - Community Manager API

Endpoints for managing AI-powered community interactions:
reviews, comments, DMs across Google, Instagram, Facebook.
"""
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.brand import Brand
from app.models.cm_interaction import CMInteraction
from app.workers.cm_tasks import publish_google_reply

logger = structlog.get_logger()
router = APIRouter()


# ── Request/Response Models ──────────────────────────────────────────────────


class ApproveRequest(BaseModel):
    final_response: str | None = Field(
        default=None,
        description="Edited response text. If empty, uses ai_response_draft.",
    )


class RateRequest(BaseModel):
    rating: int = Field(..., ge=-1, le=1, description="1 (thumbs up) or -1 (thumbs down)")


class GoogleConnectRequest(BaseModel):
    brand_id: UUID
    access_token: str = Field(..., min_length=10)
    account_id: str = Field(..., min_length=1)
    location_id: str = Field(..., min_length=1)


class InteractionResponse(BaseModel):
    id: str
    brand_id: str
    platform: str
    interaction_type: str
    external_id: str
    commenter_name: str
    content: str
    rating: int | None
    sentiment_score: float
    classification: str
    confidence_score: float
    ai_response_draft: str | None
    ai_reasoning: str | None
    final_response: str | None
    response_status: str
    human_rating: int | None
    published_at: str | None
    created_at: str
    updated_at: str
    extra_metadata: dict | None

    @classmethod
    def from_orm(cls, obj: CMInteraction) -> "InteractionResponse":
        return cls(
            id=str(obj.id),
            brand_id=str(obj.brand_id),
            platform=obj.platform,
            interaction_type=obj.interaction_type,
            external_id=obj.external_id,
            commenter_name=obj.commenter_name,
            content=obj.content,
            rating=obj.rating,
            sentiment_score=obj.sentiment_score,
            classification=obj.classification,
            confidence_score=obj.confidence_score,
            ai_response_draft=obj.ai_response_draft,
            ai_reasoning=obj.ai_reasoning,
            final_response=obj.final_response,
            response_status=obj.response_status,
            human_rating=obj.human_rating,
            published_at=obj.published_at.isoformat() if obj.published_at else None,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat(),
            extra_metadata=obj.extra_metadata,
        )


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _get_interaction(
    interaction_id: UUID,
    current_user,
    db: AsyncSession,
) -> CMInteraction:
    """Load an interaction and verify the user has access to its brand."""
    result = await db.execute(
        select(CMInteraction).where(CMInteraction.id == interaction_id)
    )
    interaction = result.scalar_one_or_none()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")

    # Verify brand access
    await get_brand(interaction.brand_id, current_user, db)
    return interaction


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/interactions")
async def list_interactions(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    platform: str | None = None,
    response_status: str | None = None,
    classification: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List interactions with filtering and pagination."""
    # Verify brand access
    await get_brand(brand_id, current_user, db)

    conditions = [CMInteraction.brand_id == brand_id]
    if platform:
        conditions.append(CMInteraction.platform == platform)
    if response_status:
        conditions.append(CMInteraction.response_status == response_status)
    if classification:
        conditions.append(CMInteraction.classification == classification)

    # Count total
    count_result = await db.execute(
        select(func.count(CMInteraction.id)).where(and_(*conditions))
    )
    total = count_result.scalar()

    # Fetch page
    result = await db.execute(
        select(CMInteraction)
        .where(and_(*conditions))
        .order_by(CMInteraction.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    interactions = result.scalars().all()

    return {
        "interactions": [InteractionResponse.from_orm(i) for i in interactions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/interactions/{interaction_id}")
async def get_interaction(
    interaction_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> InteractionResponse:
    """Get detail of a single interaction."""
    interaction = await _get_interaction(interaction_id, current_user, db)
    return InteractionResponse.from_orm(interaction)


@router.post("/interactions/{interaction_id}/approve")
async def approve_interaction(
    interaction_id: UUID,
    body: ApproveRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> InteractionResponse:
    """Approve an interaction's AI response (or provide an edited version).

    If final_response is provided, uses that. Otherwise, uses ai_response_draft.
    Then dispatches the reply for publishing on the platform.
    """
    interaction = await _get_interaction(interaction_id, current_user, db)

    if interaction.response_status in ("auto_published", "approved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This interaction has already been approved/published.",
        )

    final_text = body.final_response or interaction.ai_response_draft
    if not final_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No response text available to publish.",
        )

    status_value = "edited" if body.final_response else "approved"
    interaction.final_response = final_text
    interaction.response_status = status_value

    await db.commit()
    await db.refresh(interaction)

    # Dispatch publishing task
    if interaction.platform == "google":
        publish_google_reply.delay(str(interaction.id))

    logger.info(
        "Interaction approved",
        interaction_id=str(interaction_id),
        status=status_value,
    )
    return InteractionResponse.from_orm(interaction)


@router.post("/interactions/{interaction_id}/reject")
async def reject_interaction(
    interaction_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> InteractionResponse:
    """Reject an interaction's AI response."""
    interaction = await _get_interaction(interaction_id, current_user, db)
    interaction.response_status = "rejected"
    await db.commit()
    await db.refresh(interaction)
    return InteractionResponse.from_orm(interaction)


@router.post("/interactions/{interaction_id}/rate")
async def rate_interaction(
    interaction_id: UUID,
    body: RateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> InteractionResponse:
    """Submit human feedback (thumbs up/down) on an AI response."""
    interaction = await _get_interaction(interaction_id, current_user, db)
    interaction.human_rating = body.rating
    await db.commit()
    await db.refresh(interaction)
    return InteractionResponse.from_orm(interaction)


@router.post("/google/connect")
async def connect_google(
    body: GoogleConnectRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Connect a brand to Google Business Profile.

    Stores the OAuth access token and GBP identifiers in the brand's
    constraints JSON field.
    """
    brand = await get_brand(body.brand_id, current_user, db)

    constraints = brand.constraints or {}
    constraints["google_business"] = {
        "access_token": body.access_token,
        "account_id": body.account_id,
        "location_id": body.location_id,
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }
    brand.constraints = constraints
    await db.commit()

    logger.info("Google Business Profile connected", brand_id=str(brand.id))
    return {"success": True, "message": "Google Business Profile connected"}


@router.get("/stats")
async def get_cm_stats(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    days: int = 7,
) -> dict:
    """Get Community Manager stats for a brand."""
    await get_brand(brand_id, current_user, db)

    since = datetime.now(timezone.utc) - timedelta(days=days)
    base_conditions = [
        CMInteraction.brand_id == brand_id,
        CMInteraction.created_at >= since,
    ]

    # Total interactions
    total_result = await db.execute(
        select(func.count(CMInteraction.id)).where(and_(*base_conditions))
    )
    total = total_result.scalar() or 0

    # By status
    status_result = await db.execute(
        select(
            CMInteraction.response_status,
            func.count(CMInteraction.id),
        )
        .where(and_(*base_conditions))
        .group_by(CMInteraction.response_status)
    )
    status_counts = {row[0]: row[1] for row in status_result.all()}

    # By classification
    class_result = await db.execute(
        select(
            CMInteraction.classification,
            func.count(CMInteraction.id),
        )
        .where(and_(*base_conditions))
        .group_by(CMInteraction.classification)
    )
    classification_counts = {row[0]: row[1] for row in class_result.all()}

    # Average sentiment
    avg_result = await db.execute(
        select(func.avg(CMInteraction.sentiment_score)).where(and_(*base_conditions))
    )
    avg_sentiment = avg_result.scalar()

    # Response rate
    published_count = (
        status_counts.get("auto_published", 0)
        + status_counts.get("approved", 0)
        + status_counts.get("edited", 0)
    )
    response_rate = (published_count / total * 100) if total > 0 else 0

    # Pending count (needs attention)
    pending = status_counts.get("pending", 0)

    return {
        "period_days": days,
        "total_interactions": total,
        "pending_count": pending,
        "published_count": published_count,
        "response_rate": round(response_rate, 1),
        "avg_sentiment": round(float(avg_sentiment or 0.5), 2),
        "by_status": status_counts,
        "by_classification": classification_counts,
    }
