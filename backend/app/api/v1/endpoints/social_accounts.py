"""
PresenceOS - Social Accounts API (Upload-Post integration)

Single-call endpoints — auto-creates profile if needed.
"""
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.core.config import settings

VALID_PLATFORMS = {"instagram", "facebook", "tiktok"}

logger = structlog.get_logger()
router = APIRouter()


def _get_upload_username(brand: object, brand_id: UUID) -> str:
    """Get stable Upload-Post username from brand or fallback to brand_id."""
    return getattr(brand, "upload_post_username", None) or str(brand_id)


@router.get("/link-url/{brand_id}")
async def get_social_link_url(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    platform: Optional[str] = Query(None, description="Single platform: instagram, facebook, or tiktok"),
    redirect_url: Optional[str] = Query(None, description="Deep link redirect URL for mobile"),
) -> dict:
    """
    Generate Upload-Post OAuth URL in a single call.
    Auto-creates profile if it doesn't exist yet.
    Accepts optional `platform` to scope to a single network,
    and optional `redirect_url` for mobile deep link callback.
    """
    brand = await get_brand(brand_id, current_user, db)

    if not settings.upload_post_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload-Post API non configuree (UPLOAD_POST_API_KEY manquante).",
        )

    # Validate platform if provided
    if platform and platform.lower() not in VALID_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Plateforme invalide: {platform}. Valides: {', '.join(VALID_PLATFORMS)}",
        )

    platforms = [platform.lower()] if platform else list(VALID_PLATFORMS)

    from app.services.social_publisher import SocialPublisher

    publisher = SocialPublisher()
    upload_username = _get_upload_username(brand, brand_id)

    try:
        # Auto-create profile (idempotent — skips if exists)
        await publisher.create_brand_profile(upload_username)

        # Save username on brand if model supports it and not saved yet
        if hasattr(brand, "upload_post_username") and not brand.upload_post_username:  # type: ignore[union-attr]
            brand.upload_post_username = upload_username  # type: ignore[attr-defined]
            await db.commit()

        # Generate JWT link — pass platform list and optional redirect URL
        access_url = await publisher.get_social_link_url(
            brand_id=upload_username,
            platforms=platforms,
            redirect_url=redirect_url,
        )
    except Exception as exc:
        logger.error("Upload-Post link-url failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur Upload-Post: {str(exc)[:200]}",
        )

    return {"url": access_url, "brand_id": str(brand_id)}


@router.get("/accounts/{brand_id}")
async def list_connected_accounts(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """List social accounts connected via Upload-Post for this brand."""
    brand = await get_brand(brand_id, current_user, db)

    if not settings.upload_post_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload-Post API non configuree.",
        )

    from app.services.social_publisher import SocialPublisher

    publisher = SocialPublisher()
    upload_username = _get_upload_username(brand, brand_id)

    try:
        accounts = await publisher.get_connected_accounts(upload_username)
    except Exception as exc:
        logger.error("Upload-Post accounts fetch failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erreur Upload-Post: {str(exc)[:200]}",
        )

    return {"accounts": accounts, "brand_id": str(brand_id)}
