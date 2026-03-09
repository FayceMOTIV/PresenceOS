"""
PresenceOS — Headless Social Publishing via Postiz (v2)

The restaurant owner never sees Postiz. They see only native
OAuth popups (Meta, TikTok, LinkedIn) and come back to the RS3 app.

OAuth flow:
  GET /connect/{platform} → returns OAuth URL
  Mobile opens URL in expo-web-browser → native popup
  Callback → rs3://social-callback deep link → back in RS3

Publishing flow:
  POST /publish → immediate publish
  POST /schedule → scheduled publish
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.postiz_service import PostizService, SUPPORTED_PLATFORMS

logger = logging.getLogger(__name__)

router = APIRouter()

# Deep link scheme for OAuth callback (matches app.json scheme)
RS3_CALLBACK = "rs3://social-callback"


# ── Request Models ───────────────────────────────────────────────────────


class PublishNowRequest(BaseModel):
    integration_ids: list[str] = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=2200)
    media_urls: list[str] = Field(default_factory=list)


class SchedulePostRequest(BaseModel):
    integration_ids: list[str] = Field(..., min_length=1)
    content: str = Field(..., min_length=1, max_length=2200)
    publish_at: datetime
    media_urls: list[str] = Field(default_factory=list)


# ── OAuth Connect Flow (headless) ───────────────────────────────────────


@router.get(
    "/brands/{brand_id}/connect/{platform}",
    summary="Get OAuth URL for connecting a social account",
)
@limiter.limit("20/minute")
async def get_connect_url(
    request: Request,
    brand_id: str,
    platform: str,
    user: FirebaseUser,
    db: DBSession,
):
    """
    Returns the OAuth URL to connect a social network.

    The mobile app opens this URL in expo-web-browser.
    The user sees ONLY the native Meta/TikTok/LinkedIn popup — never Postiz.
    After OAuth, the user is redirected back to the RS3 app via deep link.
    """
    await verify_brand_access(brand_id, user, db)

    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform must be one of: {', '.join(sorted(SUPPORTED_PLATFORMS))}",
        )

    callback_url = f"{RS3_CALLBACK}?brand_id={brand_id}&platform={platform}&success=true"
    connect_url = PostizService.get_connect_url(
        platform=platform,
        brand_id=brand_id,
        callback_url=callback_url,
    )

    return {"connect_url": connect_url, "platform": platform}


@router.get(
    "/callback",
    summary="OAuth callback (redirects to mobile deep link)",
)
async def oauth_callback(
    request: Request,
    brand_id: str = "",
    platform: str = "",
    error: Optional[str] = None,
):
    """
    Server-side OAuth callback from Postiz.
    Redirects to the RS3 mobile app via deep link.
    """
    if error:
        return RedirectResponse(
            f"{RS3_CALLBACK}?success=false&error={error}&platform={platform}"
        )
    return RedirectResponse(
        f"{RS3_CALLBACK}?success=true&platform={platform}&brand_id={brand_id}"
    )


# ── Integrations ────────────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/integrations",
    summary="List connected social accounts for this brand",
)
@limiter.limit("30/minute")
async def list_integrations(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """List social accounts connected for this brand (filtered by customer)."""
    await verify_brand_access(brand_id, user, db)
    try:
        return await PostizService.list_brand_integrations(brand_id)
    except Exception as exc:
        logger.error("list_integrations failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Postiz unreachable")


@router.delete(
    "/brands/{brand_id}/integrations/{integration_id}",
    summary="Disconnect a social account",
)
@limiter.limit("10/minute")
async def disconnect_integration(
    request: Request,
    brand_id: str,
    integration_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Disconnect a social account from Postiz."""
    await verify_brand_access(brand_id, user, db)
    try:
        return await PostizService.disconnect_integration(integration_id)
    except Exception as exc:
        logger.error("disconnect failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Disconnect failed")


# ── Publishing ──────────────────────────────────────────────────────────


@router.post(
    "/brands/{brand_id}/publish",
    summary="Publish now to social platforms",
)
@limiter.limit("10/minute")
async def publish_now(
    request: Request,
    brand_id: str,
    body: PublishNowRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Publish immediately to the selected platforms."""
    await verify_brand_access(brand_id, user, db)
    try:
        return await PostizService.publish_now(
            integration_ids=body.integration_ids,
            content=body.content,
            media_urls=body.media_urls or [],
        )
    except Exception as exc:
        logger.error("publish_now failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=502, detail=f"Publish failed: {str(exc)[:200]}")


@router.post(
    "/brands/{brand_id}/schedule",
    summary="Schedule a post for later",
)
@limiter.limit("10/minute")
async def schedule_post(
    request: Request,
    brand_id: str,
    body: SchedulePostRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Schedule a post for a future datetime."""
    await verify_brand_access(brand_id, user, db)

    if body.publish_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="publish_at must be in the future",
        )

    try:
        return await PostizService.schedule_post(
            integration_ids=body.integration_ids,
            content=body.content,
            publish_at=body.publish_at,
            media_urls=body.media_urls or [],
        )
    except Exception as exc:
        logger.error("schedule_post failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=502, detail=f"Schedule failed: {str(exc)[:200]}")


@router.get(
    "/brands/{brand_id}/posts",
    summary="List scheduled and published posts",
)
@limiter.limit("30/minute")
async def list_posts(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """List posts (scheduled + published)."""
    await verify_brand_access(brand_id, user, db)
    try:
        return await PostizService.list_posts()
    except Exception as exc:
        logger.error("list_posts failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Postiz unreachable")


@router.delete(
    "/brands/{brand_id}/posts/{post_id}",
    summary="Delete a scheduled post",
)
@limiter.limit("10/minute")
async def delete_post(
    request: Request,
    brand_id: str,
    post_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Delete a scheduled post."""
    await verify_brand_access(brand_id, user, db)
    try:
        return await PostizService.delete_post(post_id)
    except Exception as exc:
        logger.error("delete_post failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Delete failed")


# ── Analytics ───────────────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/analytics/{integration_id}",
    summary="Platform analytics",
)
@limiter.limit("20/minute")
async def platform_analytics(
    request: Request,
    brand_id: str,
    integration_id: str,
    user: FirebaseUser,
    db: DBSession,
    days: int = 30,
):
    """Analytics for a social platform over N days."""
    await verify_brand_access(brand_id, user, db)
    try:
        return await PostizService.get_platform_analytics(integration_id, days)
    except Exception as exc:
        logger.error("platform_analytics failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Analytics unavailable")


# ── Health ──────────────────────────────────────────────────────────────


@router.get(
    "/health",
    summary="Postiz health check",
)
async def postiz_health():
    """Check if Postiz is reachable."""
    ok = await PostizService.health_check()
    return {"postiz": "ok" if ok else "unreachable"}
