"""
Late (getlate.dev) — Unified Social Media API Service

Handles: OAuth connect, account listing, publishing, scheduling.
API docs: https://docs.getlate.dev
"""

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()

BASE_URL = "https://getlate.dev/api/v1"
TIMEOUT = 30


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.late_api_key}",
        "Content-Type": "application/json",
    }


def _profile_id() -> str:
    pid = settings.late_profile_id
    if not pid:
        raise RuntimeError("LATE_PROFILE_ID not configured")
    return pid


class LateService:
    """Service for Late social media API."""

    async def list_accounts(self) -> list[dict]:
        """List all connected social accounts."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{BASE_URL}/accounts",
                headers=_headers(),
                params={"profileId": _profile_id()},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("accounts", [])

    async def get_connect_url(
        self, platform: str, redirect_url: str
    ) -> str:
        """Get OAuth URL to connect a new social account.

        Args:
            platform: e.g. 'instagram', 'facebook', 'tiktok', 'linkedin', 'twitter', 'youtube'
            redirect_url: URL to redirect after OAuth (e.g. rs3://social-callback)

        Returns:
            OAuth authorization URL
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{BASE_URL}/connect/{platform}",
                headers=_headers(),
                params={
                    "profileId": _profile_id(),
                    "redirect_url": redirect_url,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            url = data.get("authUrl")
            if not url:
                raise RuntimeError(f"No authUrl in Late response: {data}")
            logger.info("late.connect_url", platform=platform)
            return url

    async def publish_now(
        self,
        content: str,
        account_ids: list[dict],
        media_urls: list[str] | None = None,
    ) -> dict:
        """Publish a post immediately.

        Args:
            content: Post text
            account_ids: [{"platform": "instagram", "accountId": "..."}]
            media_urls: Optional list of image/video URLs
        """
        body: dict = {
            "content": content,
            "platforms": account_ids,
            "publishNow": True,
        }
        if media_urls:
            body["mediaItems"] = [
                {
                    "type": "video" if url.endswith((".mp4", ".mov", ".webm")) else "image",
                    "url": url,
                }
                for url in media_urls
            ]

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{BASE_URL}/posts",
                headers=_headers(),
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("late.publish_now", post_id=data.get("post", {}).get("_id"))
            return data

    async def schedule_post(
        self,
        content: str,
        account_ids: list[dict],
        scheduled_for: str,
        timezone: str = "Europe/Paris",
        media_urls: list[str] | None = None,
    ) -> dict:
        """Schedule a post for later.

        Args:
            content: Post text
            account_ids: [{"platform": "instagram", "accountId": "..."}]
            scheduled_for: ISO 8601 datetime (e.g. "2026-03-15T10:00:00")
            timezone: IANA timezone (default Europe/Paris)
            media_urls: Optional list of image/video URLs
        """
        body: dict = {
            "content": content,
            "platforms": account_ids,
            "scheduledFor": scheduled_for,
            "timezone": timezone,
        }
        if media_urls:
            body["mediaItems"] = [
                {
                    "type": "video" if url.endswith((".mp4", ".mov", ".webm")) else "image",
                    "url": url,
                }
                for url in media_urls
            ]

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{BASE_URL}/posts",
                headers=_headers(),
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "late.schedule_post",
                post_id=data.get("post", {}).get("_id"),
                scheduled_for=scheduled_for,
            )
            return data

    async def disconnect_account(self, account_id: str) -> bool:
        """Disconnect a social account."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.delete(
                f"{BASE_URL}/accounts/{account_id}",
                headers=_headers(),
            )
            if resp.status_code in (200, 204):
                logger.info("late.disconnect", account_id=account_id)
                return True
            logger.warning(
                "late.disconnect_failed",
                account_id=account_id,
                status=resp.status_code,
            )
            return False

    async def health_check(self) -> bool:
        """Check if Late API is reachable."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{BASE_URL}/profiles",
                    headers=_headers(),
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning("Late API health check failed", error=str(e))
            return False


def get_late_service() -> LateService:
    return LateService()
