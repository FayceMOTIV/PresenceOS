"""
PresenceOS - AI Proposals API

Endpoints for listing, approving, rejecting, editing, and regenerating
AI-generated content proposals.

On approve:
  - If UPLOAD_POST_API_KEY is set → publish immediately via Upload-Post
  - Otherwise → just set status to approved (no real publish)
"""
from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, and_

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.core.config import settings
from app.models.ai_proposal import AIProposal, ProposalStatus

logger = structlog.get_logger()
router = APIRouter()


# ── Request/Response Models ──────────────────────────────────────────────


class ProposalResponse(BaseModel):
    id: str
    brand_id: str
    proposal_type: str
    platform: str
    caption: str | None
    hashtags: list[str] | None
    image_url: str | None
    video_url: str | None
    improved_image_url: str | None
    source: str
    source_id: str | None
    status: str
    scheduled_at: str | None
    published_at: str | None
    rejection_reason: str | None
    kb_version: int
    confidence_score: float
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, obj: AIProposal) -> "ProposalResponse":
        return cls(
            id=str(obj.id),
            brand_id=str(obj.brand_id),
            proposal_type=obj.proposal_type,
            platform=obj.platform,
            caption=obj.caption,
            hashtags=obj.hashtags,
            image_url=obj.image_url,
            video_url=obj.video_url,
            improved_image_url=obj.improved_image_url,
            source=obj.source,
            source_id=obj.source_id,
            status=obj.status,
            scheduled_at=obj.scheduled_at.isoformat() if obj.scheduled_at else None,
            published_at=obj.published_at.isoformat() if obj.published_at else None,
            rejection_reason=obj.rejection_reason,
            kb_version=obj.kb_version,
            confidence_score=obj.confidence_score,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat(),
        )


class ApproveProposalRequest(BaseModel):
    scheduled_at: str | None = Field(
        default=None,
        description="ISO datetime string to schedule. If empty, approve immediately.",
    )


class RejectProposalRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class EditCaptionRequest(BaseModel):
    caption: str = Field(..., min_length=1, max_length=5000)
    hashtags: list[str] | None = None


# ── Helpers ──────────────────────────────────────────────────────────────


async def _get_proposal(
    brand_id: UUID,
    proposal_id: UUID,
    current_user,
    db,
) -> AIProposal:
    """Load a proposal and verify brand access."""
    await get_brand(brand_id, current_user, db)

    result = await db.execute(
        select(AIProposal).where(
            AIProposal.id == proposal_id,
            AIProposal.brand_id == brand_id,
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found",
        )
    return proposal


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/{brand_id}")
async def list_proposals(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    proposal_status: str | None = None,
    platform: str | None = None,
    proposal_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List AI proposals for a brand with optional filters."""
    await get_brand(brand_id, current_user, db)

    conditions = [AIProposal.brand_id == brand_id]
    if proposal_status:
        conditions.append(AIProposal.status == proposal_status)
    if platform:
        conditions.append(AIProposal.platform == platform)
    if proposal_type:
        conditions.append(AIProposal.proposal_type == proposal_type)

    # Count
    count_result = await db.execute(
        select(func.count(AIProposal.id)).where(and_(*conditions))
    )
    total = count_result.scalar()

    # Fetch
    result = await db.execute(
        select(AIProposal)
        .where(and_(*conditions))
        .order_by(AIProposal.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    proposals = result.scalars().all()

    return {
        "proposals": [ProposalResponse.from_orm(p) for p in proposals],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{brand_id}/{proposal_id}/approve")
async def approve_proposal(
    brand_id: UUID,
    proposal_id: UUID,
    body: ApproveProposalRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ProposalResponse:
    """Approve a proposal and publish via Upload-Post if configured."""
    proposal = await _get_proposal(brand_id, proposal_id, current_user, db)

    if proposal.status not in (ProposalStatus.PENDING.value,):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve a proposal with status '{proposal.status}'",
        )

    if body.scheduled_at:
        proposal.scheduled_at = datetime.fromisoformat(body.scheduled_at)
        proposal.status = ProposalStatus.SCHEDULED.value
    else:
        proposal.status = ProposalStatus.APPROVED.value

    await db.commit()
    await db.refresh(proposal)

    # ── Trigger real publishing via Upload-Post ────────────────────────
    if settings.upload_post_api_key and proposal.status == ProposalStatus.APPROVED.value:
        try:
            from app.services.social_publisher import SocialPublisher

            publisher = SocialPublisher()

            # Determine media URL (prefer improved, then original)
            image_url = proposal.improved_image_url or proposal.image_url

            # Determine platforms (default to proposal.platform)
            platforms = [proposal.platform] if proposal.platform else ["instagram"]

            # Resolve brand Upload-Post username
            brand = await get_brand(brand_id, current_user, db)
            upload_username = getattr(brand, "upload_post_username", None) or str(brand_id)

            if image_url:
                result = await publisher.publish_photo(
                    brand_id=upload_username,
                    image_url=image_url,
                    caption=proposal.caption or "",
                    platforms=platforms,
                    hashtags=proposal.hashtags,
                )

                # Update proposal with publish result
                proposal.status = ProposalStatus.PUBLISHED.value
                proposal.published_at = datetime.now(timezone.utc)
                if hasattr(proposal, "published_url"):
                    proposal.published_url = result.get("post_url")  # type: ignore[attr-defined]
                await db.commit()
                await db.refresh(proposal)

                logger.info(
                    "Proposal published via Upload-Post",
                    proposal_id=str(proposal_id),
                    post_url=result.get("post_url"),
                    platforms=platforms,
                )

        except Exception as exc:
            # Publishing failed — keep as approved, log error
            logger.error(
                "Upload-Post publish failed, keeping as approved",
                proposal_id=str(proposal_id),
                error=str(exc),
            )

    logger.info("Proposal approved", proposal_id=str(proposal_id), status=proposal.status)
    return ProposalResponse.from_orm(proposal)


@router.post("/{brand_id}/{proposal_id}/reject")
async def reject_proposal(
    brand_id: UUID,
    proposal_id: UUID,
    body: RejectProposalRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ProposalResponse:
    """Reject a proposal with an optional reason."""
    proposal = await _get_proposal(brand_id, proposal_id, current_user, db)

    if proposal.status not in (ProposalStatus.PENDING.value,):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject a proposal with status '{proposal.status}'",
        )

    proposal.status = ProposalStatus.REJECTED.value
    proposal.rejection_reason = body.reason
    await db.commit()
    await db.refresh(proposal)

    logger.info("Proposal rejected", proposal_id=str(proposal_id))
    return ProposalResponse.from_orm(proposal)


@router.put("/{brand_id}/{proposal_id}/caption")
async def edit_caption(
    brand_id: UUID,
    proposal_id: UUID,
    body: EditCaptionRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ProposalResponse:
    """Edit a proposal's caption and/or hashtags."""
    proposal = await _get_proposal(brand_id, proposal_id, current_user, db)

    proposal.caption = body.caption
    if body.hashtags is not None:
        proposal.hashtags = body.hashtags

    await db.commit()
    await db.refresh(proposal)

    logger.info("Proposal caption edited", proposal_id=str(proposal_id))
    return ProposalResponse.from_orm(proposal)


@router.post("/{brand_id}/{proposal_id}/regenerate", status_code=status.HTTP_201_CREATED)
async def regenerate_proposal(
    brand_id: UUID,
    proposal_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ProposalResponse:
    """Generate a new variant of an existing proposal."""
    proposal = await _get_proposal(brand_id, proposal_id, current_user, db)

    from app.services.proposal_generator import ProposalGenerator
    generator = ProposalGenerator(db)

    try:
        new_proposal = await generator.regenerate_variant(str(proposal_id))
    except Exception as exc:
        logger.error("Regeneration failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate proposal",
        )

    return ProposalResponse.from_orm(new_proposal)
