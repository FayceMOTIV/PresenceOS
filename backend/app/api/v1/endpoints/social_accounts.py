"""
PresenceOS - Social Accounts API (Late / getlate.dev integration)

Endpoints for connecting, listing, and managing social media accounts
via the Late unified social media API.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.core.config import settings
from app.services.late_service import get_late_service

logger = structlog.get_logger()
router = APIRouter()


def _ensure_late_configured() -> None:
    if not settings.late_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Late API non configuree (LATE_API_KEY manquante).",
        )


@router.get("/accounts/{brand_id}")
async def list_connected_accounts(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """List social accounts connected via Late for this brand."""
    _ensure_late_configured()
    await get_brand(brand_id, current_user, db)

    late = get_late_service()
    try:
        raw_accounts = await late.list_accounts()
    except Exception as exc:
        logger.error("late.accounts_fetch_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur Late: {str(exc)[:200]}",
        )

    # Normalize to the format the mobile app expects
    accounts = [
        {
            "platform": a.get("platform", ""),
            "username": a.get("username", ""),
            "display_name": a.get("displayName", ""),
            "connected": a.get("isActive", False),
            "avatar_url": a.get("profilePicture", ""),
            "account_id": a.get("_id", ""),
        }
        for a in raw_accounts
    ]

    return {"accounts": accounts, "brand_id": str(brand_id)}


@router.get("/connect-url/{brand_id}")
async def get_connect_url(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    platform: str = Query(..., description="Platform: instagram, facebook, tiktok, linkedin, twitter, youtube"),
    redirect_url: str = Query("", description="Deep link redirect URL for mobile"),
) -> dict:
    """Generate Late OAuth URL to connect a social account."""
    _ensure_late_configured()
    await get_brand(brand_id, current_user, db)

    late = get_late_service()
    try:
        auth_url = await late.get_connect_url(
            platform=platform.lower(),
            redirect_url=redirect_url or "https://presenceos.dev/callback",
        )
    except Exception as exc:
        logger.error("late.connect_url_failed", platform=platform, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur Late: {str(exc)[:200]}",
        )

    return {"url": auth_url, "brand_id": str(brand_id)}


# Keep legacy endpoint for backward compat — redirects to connect-url
@router.get("/link-url/{brand_id}")
async def get_social_link_url_legacy(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    platform: str = Query(None, description="Platform"),
    redirect_url: str = Query(None, description="Redirect URL"),
) -> dict:
    """Legacy Upload-Post endpoint — now proxied to Late."""
    _ensure_late_configured()
    await get_brand(brand_id, current_user, db)

    if not platform:
        platform = "instagram"

    late = get_late_service()
    try:
        auth_url = await late.get_connect_url(
            platform=platform.lower(),
            redirect_url=redirect_url or "https://presenceos.dev/callback",
        )
    except Exception as exc:
        logger.error("late.link_url_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur Late: {str(exc)[:200]}",
        )

    return {"url": auth_url, "brand_id": str(brand_id)}


class PublishRequest(BaseModel):
    content: str
    platforms: list[dict]  # [{"platform": "instagram", "accountId": "..."}]
    media_urls: list[str] = []


@router.post("/publish/{brand_id}")
async def publish_now(
    brand_id: UUID,
    body: PublishRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Publish a post immediately via Late."""
    _ensure_late_configured()
    await get_brand(brand_id, current_user, db)

    late = get_late_service()
    try:
        result = await late.publish_now(
            content=body.content,
            account_ids=body.platforms,
            media_urls=body.media_urls or None,
        )
    except Exception as exc:
        logger.error("late.publish_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur publication: {str(exc)[:200]}",
        )

    return {"success": True, "post": result.get("post", {})}


class ScheduleRequest(BaseModel):
    content: str
    platforms: list[dict]
    scheduled_for: str  # ISO 8601
    timezone: str = "Europe/Paris"
    media_urls: list[str] = []


@router.post("/schedule/{brand_id}")
async def schedule_post(
    brand_id: UUID,
    body: ScheduleRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Schedule a post for later via Late."""
    _ensure_late_configured()
    await get_brand(brand_id, current_user, db)

    late = get_late_service()
    try:
        result = await late.schedule_post(
            content=body.content,
            account_ids=body.platforms,
            scheduled_for=body.scheduled_for,
            timezone=body.timezone,
            media_urls=body.media_urls or None,
        )
    except Exception as exc:
        logger.error("late.schedule_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur planification: {str(exc)[:200]}",
        )

    return {"success": True, "post": result.get("post", {})}


@router.delete("/disconnect/{brand_id}/{account_id}")
async def disconnect_account(
    brand_id: UUID,
    account_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Disconnect a social account via Late."""
    _ensure_late_configured()
    await get_brand(brand_id, current_user, db)

    late = get_late_service()
    ok = await late.disconnect_account(account_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible de deconnecter ce compte.",
        )

    return {"success": True}
