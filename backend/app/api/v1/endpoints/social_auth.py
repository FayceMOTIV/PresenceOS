"""
PresenceOS — Social Auth OAuth endpoints.

Handles OAuth initiation and callback for Instagram, Facebook, TikTok.
Uses Upload-Post integration for token management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional
import hmac
import hashlib
import time
import httpx
import structlog

from app.core.config import settings
from app.api.v1.deps import CurrentUser, DBSession, get_brand

logger = structlog.get_logger()

router = APIRouter()


class OAuthInitiateResponse(BaseModel):
    url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    success: bool
    platform: str
    message: str


class SelectPageRequest(BaseModel):
    page_id: str


class FacebookPage(BaseModel):
    id: str
    name: str
    instagram_business_id: Optional[str] = None
    category: Optional[str] = None


class FacebookPagesResponse(BaseModel):
    pages: list[FacebookPage]


def _sign_state(state: str) -> str:
    """HMAC-sign the OAuth state to prevent CSRF."""
    ts = str(int(time.time()))
    payload = f"{state}:{ts}"
    sig = hmac.new(
        settings.secret_key.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}:{sig}"


def _verify_state(signed_state: str) -> bool:
    """Verify an HMAC-signed OAuth state. Reject if older than 10 min."""
    parts = signed_state.split(":")
    if len(parts) != 3:
        return False
    state, ts, sig = parts
    expected = hmac.new(
        settings.secret_key.encode(), f"{state}:{ts}".encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False
    # Reject states older than 600 s (10 min)
    try:
        if abs(time.time() - int(ts)) > 600:
            return False
    except ValueError:
        return False
    return True


@router.get("/{brand_id}/{platform}/initiate", response_model=OAuthInitiateResponse)
async def initiate_oauth(
    brand_id: str,
    platform: str,
    current_user: CurrentUser,
    db: DBSession,
    redirect_url: str = Query(...),
):
    """
    Generate an OAuth URL for the given platform.
    The mobile app opens this URL with expo-web-browser.openAuthSessionAsync().
    """
    from uuid import UUID as _UUID
    await get_brand(_UUID(brand_id), current_user, db)

    supported = {"instagram", "facebook", "tiktok"}
    if platform not in supported:
        raise HTTPException(400, f"Platform '{platform}' not supported. Use: {supported}")

    import uuid
    state = _sign_state(str(uuid.uuid4()))

    # Build OAuth URL based on platform
    if platform in ("instagram", "facebook"):
        # Facebook/Instagram use the same Facebook Login OAuth flow
        client_id = getattr(settings, "facebook_app_id", None)
        if not client_id:
            raise HTTPException(500, "Facebook App ID not configured")

        scopes = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish"
        oauth_url = (
            f"https://www.facebook.com/v19.0/dialog/oauth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_url}"
            f"&state={state}"
            f"&scope={scopes}"
            f"&response_type=code"
        )
    elif platform == "tiktok":
        client_key = getattr(settings, "tiktok_client_key", None)
        if not client_key:
            raise HTTPException(500, "TikTok Client Key not configured")

        scopes = "user.info.basic,video.publish"
        oauth_url = (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={client_key}"
            f"&scope={scopes}"
            f"&response_type=code"
            f"&redirect_uri={redirect_url}"
            f"&state={state}"
        )
    else:
        raise HTTPException(400, f"No OAuth flow for {platform}")

    logger.info("OAuth initiated", platform=platform, brand_id=brand_id, state=state)
    return OAuthInitiateResponse(url=oauth_url, state=state)


@router.get("/callback", response_model=OAuthCallbackResponse)
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    platform: str = Query("facebook"),
):
    """
    Handle OAuth callback after user authorizes.
    Exchanges code for access token and stores connection.
    """
    # Verify HMAC-signed state to prevent CSRF
    if not _verify_state(state):
        raise HTTPException(403, "Invalid or expired OAuth state")

    logger.info("OAuth callback received", platform=platform)

    # In production, this would exchange the code for a long-lived token
    # and store the social connection in the database.
    # For now, the Upload-Post integration handles token exchange.

    return OAuthCallbackResponse(
        success=True,
        platform=platform,
        message=f"{platform} connected successfully",
    )


@router.get("/facebook-pages/{brand_id}", response_model=FacebookPagesResponse)
async def list_facebook_pages(brand_id: str, current_user: CurrentUser, db: DBSession):
    """
    List Facebook Pages accessible by the authenticated user.
    Used for the page picker modal in the mobile app.
    """
    from uuid import UUID as _UUID
    await get_brand(_UUID(brand_id), current_user, db)
    logger.info("Listing Facebook pages", brand_id=brand_id)

    # In production, this would use the stored Facebook access token
    # to call the Facebook Graph API /me/accounts endpoint.
    # For now, return empty list (Upload-Post handles page selection).

    return FacebookPagesResponse(pages=[])


@router.post("/select-page/{brand_id}")
async def select_facebook_page(
    brand_id: str,
    req: SelectPageRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Select a Facebook Page (and its linked Instagram Business account)
    as the publishing target for this brand.
    """
    from uuid import UUID as _UUID
    await get_brand(_UUID(brand_id), current_user, db)
    logger.info(
        "Selecting Facebook page",
        brand_id=brand_id,
        page_id=req.page_id,
    )

    # In production, store the selected page_id and instagram_business_id
    # on the brand record for publishing.

    return {"success": True, "page_id": req.page_id}
