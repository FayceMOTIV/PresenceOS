"""
PresenceOS - Daily Brief API

Endpoints for getting today's brief and submitting responses.
"""
from datetime import date, datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.daily_brief import DailyBrief, BriefStatus

logger = structlog.get_logger()
router = APIRouter()


# ── Request/Response Models ──────────────────────────────────────────────


class BriefResponse(BaseModel):
    id: str
    brand_id: str
    date: str
    response: str | None
    status: str
    responded_at: str | None
    generated_proposal_id: str | None
    notif_sent_at: str | None
    created_at: str

    @classmethod
    def from_orm(cls, obj: DailyBrief) -> "BriefResponse":
        return cls(
            id=str(obj.id),
            brand_id=str(obj.brand_id),
            date=obj.date.isoformat(),
            response=obj.response,
            status=obj.status,
            responded_at=obj.responded_at.isoformat() if obj.responded_at else None,
            generated_proposal_id=str(obj.generated_proposal_id) if obj.generated_proposal_id else None,
            notif_sent_at=obj.notif_sent_at.isoformat() if obj.notif_sent_at else None,
            created_at=obj.created_at.isoformat(),
        )


class BriefRespondRequest(BaseModel):
    response: str = Field(..., min_length=1, max_length=2000)


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/{brand_id}/today")
async def get_today_brief(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> BriefResponse | dict:
    """Get today's brief status for a brand."""
    await get_brand(brand_id, current_user, db)

    today = date.today()
    stmt = select(DailyBrief).where(
        DailyBrief.brand_id == brand_id,
        DailyBrief.date == today,
    )
    result = await db.execute(stmt)
    brief = result.scalar_one_or_none()

    if not brief:
        # Create one on the fly if not yet created (before 8 AM beat)
        brief = DailyBrief(
            brand_id=brand_id,
            date=today,
            status=BriefStatus.PENDING.value,
        )
        db.add(brief)
        await db.commit()
        await db.refresh(brief)

    return BriefResponse.from_orm(brief)


@router.post("/{brand_id}/respond")
async def respond_to_brief(
    brand_id: UUID,
    body: BriefRespondRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> BriefResponse:
    """Submit a response to today's daily brief.

    Triggers AI proposal generation from the brief response.
    """
    await get_brand(brand_id, current_user, db)

    today = date.today()
    stmt = select(DailyBrief).where(
        DailyBrief.brand_id == brand_id,
        DailyBrief.date == today,
    )
    result = await db.execute(stmt)
    brief = result.scalar_one_or_none()

    if not brief:
        brief = DailyBrief(
            brand_id=brand_id,
            date=today,
            status=BriefStatus.PENDING.value,
        )
        db.add(brief)
        await db.flush()

    if brief.status == BriefStatus.ANSWERED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Today's brief has already been answered.",
        )

    brief.response = body.response
    brief.status = BriefStatus.ANSWERED.value
    brief.responded_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(brief)

    # Dispatch async proposal generation
    from app.workers.content_tasks import generate_proposal_task
    generate_proposal_task.delay(
        str(brand_id),
        "brief",
        {"response": body.response},
    )

    logger.info(
        "Brief responded",
        brand_id=str(brand_id),
        brief_id=str(brief.id),
    )
    return BriefResponse.from_orm(brief)
