"""
PostizService — Headless social publishing engine.

Postiz is completely invisible to the restaurant owner.
Each brand = 1 Postiz customer (isolated OAuth tokens).

Headless OAuth flow:
1. get_connect_url(platform, brand_id) → OAuth URL
2. Mobile opens URL in expo-web-browser
3. User sees native Meta/TikTok/LinkedIn popup (NOT Postiz)
4. Callback → deep link back to RS3 app
5. Postiz publishes silently via publish_now() / schedule_post()

API docs: https://docs.postiz.com/api/public
Auth: Header "Authorization: {POSTIZ_API_KEY}"
"""
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = {"instagram", "facebook", "tiktok", "linkedin", "x", "youtube"}


def _base_url() -> str:
    """Build Postiz API base URL (lazy — avoids import-time settings read)."""
    return f"{settings.postiz_url}/public/v1"


def _headers() -> dict[str, str]:
    """Auth headers for Postiz API."""
    return {
        "Authorization": settings.postiz_api_key,
        "Content-Type": "application/json",
    }


class PostizService:
    """Async client for the Postiz public API (headless, multi-tenant)."""

    # ── Multi-tenant: 1 customer per brand ───────────────────────────────

    @staticmethod
    def get_customer_id(brand_id: str) -> str:
        """Deterministic customer ID for a brand. No DB mapping needed."""
        return f"presenceos-brand-{brand_id}"

    # ── OAuth Connect Flow (headless) ────────────────────────────────────

    @staticmethod
    def get_connect_url(
        platform: str,
        brand_id: str,
        callback_url: str,
    ) -> str:
        """
        Generate the OAuth URL for connecting a social account.

        The mobile app opens this URL in expo-web-browser.
        The user sees ONLY the native Meta/TikTok/LinkedIn popup — never Postiz.

        Args:
            platform: "instagram" | "facebook" | "tiktok" | "linkedin" | "x" | "youtube"
            brand_id: UUID string of the brand
            callback_url: Deep link back to RS3 app (rs3://social-callback)
        """
        customer_id = PostizService.get_customer_id(brand_id)
        encoded_callback = quote(callback_url, safe="")
        return (
            f"{settings.postiz_url}/integrations/{platform}"
            f"?customer={customer_id}"
            f"&redirect={encoded_callback}"
        )

    # ── Integrations (connected social accounts) ─────────────────────────

    @staticmethod
    async def list_integrations() -> list[dict]:
        """List ALL connected social accounts in Postiz (all brands)."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_base_url()}/integrations",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def list_brand_integrations(brand_id: str) -> list[dict]:
        """List connected social accounts for a specific brand (filtered by customer)."""
        all_integrations = await PostizService.list_integrations()
        customer_id = PostizService.get_customer_id(brand_id)
        return [
            integ for integ in all_integrations
            if integ.get("customer", {}).get("id") == customer_id
            and not integ.get("disabled", False)
        ]

    @staticmethod
    async def get_integration_by_platform(
        brand_id: str, platform: str
    ) -> Optional[dict]:
        """Return the integration for a given brand + platform."""
        integrations = await PostizService.list_brand_integrations(brand_id)
        for integ in integrations:
            if integ.get("identifier", "").lower() == platform.lower():
                return integ
        return None

    @staticmethod
    async def disconnect_integration(integration_id: str) -> dict:
        """Disconnect a social account."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(
                f"{_base_url()}/integrations/{integration_id}",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Publishing ───────────────────────────────────────────────────────

    @staticmethod
    async def publish_now(
        integration_ids: list[str],
        content: str,
        media_urls: Optional[list[str]] = None,
    ) -> dict:
        """Publish immediately to one or more platforms."""
        media = []
        if media_urls:
            for url in media_urls:
                uploaded = await PostizService.upload_from_url(url)
                media.append({"id": uploaded["id"], "path": uploaded["path"]})

        payload = {
            "type": "now",
            "posts": [
                {
                    "integration": {"id": integ_id},
                    "value": [{"content": content, "image": media}],
                }
                for integ_id in integration_ids
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{_base_url()}/posts",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def schedule_post(
        integration_ids: list[str],
        content: str,
        publish_at: datetime,
        media_urls: Optional[list[str]] = None,
    ) -> dict:
        """Schedule a post for a future datetime (UTC)."""
        media = []
        if media_urls:
            for url in media_urls:
                uploaded = await PostizService.upload_from_url(url)
                media.append({"id": uploaded["id"], "path": uploaded["path"]})

        payload = {
            "type": "schedule",
            "date": publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "posts": [
                {
                    "integration": {"id": integ_id},
                    "value": [{"content": content, "image": media}],
                }
                for integ_id in integration_ids
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{_base_url()}/posts",
                headers=_headers(),
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def list_posts(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """List scheduled and published posts."""
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date.isoformat() + "Z"
        if end_date:
            params["endDate"] = end_date.isoformat() + "Z"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_base_url()}/posts",
                headers=_headers(),
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def delete_post(post_id: str) -> dict:
        """Delete a scheduled post."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(
                f"{_base_url()}/posts/{post_id}",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    # ── Media ────────────────────────────────────────────────────────────

    @staticmethod
    async def upload_from_url(media_url: str) -> dict:
        """Upload media from an S3 URL to Postiz. Returns {"id", "path"}."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{_base_url()}/uploads/upload-from-url",
                headers=_headers(),
                json={"url": media_url},
            )
            resp.raise_for_status()
            return resp.json()

    # ── Analytics ────────────────────────────────────────────────────────

    @staticmethod
    async def get_platform_analytics(
        integration_id: str,
        days: int = 30,
    ) -> dict:
        """Platform analytics for the last N days."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_base_url()}/analytics/{integration_id}",
                headers=_headers(),
                params={"days": days},
            )
            resp.raise_for_status()
            return resp.json()

    # ── Health ───────────────────────────────────────────────────────────

    @staticmethod
    async def health_check() -> bool:
        """Check if Postiz is reachable."""
        if not settings.postiz_url:
            return False
        try:
            await PostizService.list_integrations()
            return True
        except Exception as exc:
            logger.warning("Postiz health check failed: %s", exc)
            return False
