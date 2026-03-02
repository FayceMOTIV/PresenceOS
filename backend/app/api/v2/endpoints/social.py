"""
PresenceOS - Social v2 Endpoints

Blotato-first social account management + publishing.
Falls back to Upload-Post if Blotato is not configured.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, get_brand
from app.core.config import settings
from app.services.blotato_client import BlotatoClient, BlotatoError

logger = structlog.get_logger()
router = APIRouter()


# ── Request / Response Models ──


class SocialAccount(BaseModel):
    id: str
    platform: str
    username: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    connected: bool = True


class AccountsResponse(BaseModel):
    accounts: list[SocialAccount]
    provider: str  # "blotato" or "upload_post"


class SubaccountResponse(BaseModel):
    subaccounts: list[dict]


class PublishRequest(BaseModel):
    account_id: str = Field(..., description="Blotato account ID")
    platform: str = Field(..., description="Target platform")
    text: str = Field(..., min_length=1, max_length=5000)
    media_urls: list[str] | None = None
    page_id: str | None = None
    scheduled_at: str | None = None


class PublishResponse(BaseModel):
    success: bool
    post_id: str | None = None
    post_url: str | None = None
    provider: str
    error: str | None = None


# ── Endpoints ──


@router.get("/accounts")
async def get_accounts(
    current_user: FirebaseUser,
    db: DBSession,
    platform: str | None = None,
) -> AccountsResponse:
    """Get connected social accounts (Blotato-first, Upload-Post fallback)."""
    client = BlotatoClient()

    if client.is_configured:
        try:
            raw = await client.get_accounts(platform)
            accounts = [
                SocialAccount(
                    id=str(a.get("id", "")),
                    platform=a.get("platform", ""),
                    username=a.get("username"),
                    display_name=a.get("display_name") or a.get("name"),
                    avatar_url=a.get("avatar_url") or a.get("picture"),
                    connected=True,
                )
                for a in raw
            ]
            return AccountsResponse(accounts=accounts, provider="blotato")
        except BlotatoError as exc:
            logger.warning("Blotato get_accounts failed, trying Upload-Post", error=str(exc))

    # Fallback: Upload-Post (return empty — Upload-Post doesn't list accounts)
    return AccountsResponse(accounts=[], provider="upload_post")


@router.get("/accounts/{account_id}/subaccounts")
async def get_subaccounts(
    account_id: str,
    current_user: FirebaseUser,
    db: DBSession,
) -> SubaccountResponse:
    """Get subaccounts (pages) for a Blotato account."""
    client = BlotatoClient()
    if not client.is_configured:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blotato not configured — subaccounts not available.",
        )

    try:
        subs = await client.get_subaccounts(account_id)
        return SubaccountResponse(subaccounts=subs)
    except BlotatoError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


@router.post("/publish")
async def publish_post(
    body: PublishRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> PublishResponse:
    """Publish a post (Blotato-first, Upload-Post fallback on error)."""
    client = BlotatoClient()

    # Try Blotato first
    if client.is_configured:
        try:
            result = await client.publish_post(
                account_id=body.account_id,
                platform=body.platform,
                text=body.text,
                media_urls=body.media_urls,
                page_id=body.page_id,
                scheduled_at=body.scheduled_at,
            )
            return PublishResponse(
                success=True,
                post_id=str(result.get("id", "")),
                post_url=result.get("url"),
                provider="blotato",
            )
        except BlotatoError as exc:
            logger.warning("Blotato publish failed, falling back to Upload-Post", error=str(exc))

    # Fallback: Upload-Post
    if not settings.upload_post_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No publishing provider configured (Blotato + Upload-Post both unavailable).",
        )

    try:
        from app.connectors.upload_post import UploadPostConnector

        connector = UploadPostConnector(platform=body.platform)
        result = await connector.publish(
            access_token=settings.upload_post_api_key,
            content={
                "caption": body.text,
                "platform": body.platform,
                "account_username": body.account_id,
            },
            media_urls=body.media_urls,
        )
        return PublishResponse(
            success=True,
            post_id=result.get("post_id"),
            post_url=result.get("post_url"),
            provider="upload_post",
        )
    except Exception as exc:
        logger.error("Upload-Post fallback failed", error=str(exc))
        return PublishResponse(
            success=False,
            provider="upload_post",
            error=str(exc)[:200],
        )
