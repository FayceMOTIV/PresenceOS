"""
PresenceOS - Editorial Calendar v2 Endpoints

Swipe approve/reject, generate month, editorial rules.
"""
from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.editorial_calendar import editorial_calendar

logger = structlog.get_logger()
router = APIRouter()


# ── Request models ──


class GenerateRequest(BaseModel):
    posts_per_day: int = Field(default=3, ge=1, le=10)
    stories_per_day: int = Field(default=2, ge=0, le=5)
    platforms: list[str] = Field(default=["instagram", "facebook", "tiktok"])
    month: str | None = Field(
        default=None,
        description="Target month YYYY-MM. Defaults to current month.",
    )


# ── Endpoints ──


@router.post("/{brand_id}/generate")
@limiter.limit("5/minute")
async def generate_calendar(
    request: Request,
    brand_id: UUID,
    body: GenerateRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Génère 1 mois de contenu éditorial. Appelé par l'app ou Morpheus."""
    await verify_brand_access(str(brand_id), current_user, db)

    target_month = (
        datetime.strptime(body.month, "%Y-%m")
        if body.month
        else datetime.now().replace(day=1)
    )

    result = await editorial_calendar.generate_month(
        brand_id=brand_id,
        posts_per_day=body.posts_per_day,
        stories_per_day=body.stories_per_day,
        platforms=body.platforms,
        month=target_month,
        db=db,
    )
    return result


@router.get("/{brand_id}")
@limiter.limit("60/minute")
async def get_calendar(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
    month: str | None = None,
    platform: str | None = None,
    status: str | None = None,
) -> dict:
    """Récupère le calendrier d'un brand. Utilisé par l'app mobile."""
    await verify_brand_access(str(brand_id), current_user, db)

    return await editorial_calendar.get_calendar(
        brand_id=brand_id,
        db=db,
        month=month,
        platform=platform,
        status=status,
    )


@router.post("/{brand_id}/posts/{post_id}/approve")
@limiter.limit("60/minute")
async def approve_post(
    request: Request,
    brand_id: UUID,
    post_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Approuve un post → prêt à être publié."""
    await verify_brand_access(str(brand_id), current_user, db)

    try:
        return await editorial_calendar.approve_post(post_id, brand_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{brand_id}/posts/{post_id}/reject")
@limiter.limit("60/minute")
async def reject_post(
    request: Request,
    brand_id: UUID,
    post_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Rejette un post du calendrier."""
    await verify_brand_access(str(brand_id), current_user, db)

    try:
        return await editorial_calendar.reject_post(post_id, brand_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{brand_id}/approve-all")
@limiter.limit("10/minute")
async def approve_all_pending(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Approuve tous les posts en attente d'un coup."""
    await verify_brand_access(str(brand_id), current_user, db)
    return await editorial_calendar.approve_all_pending(brand_id, db)
