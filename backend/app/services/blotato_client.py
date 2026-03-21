"""
PresenceOS - Blotato Social Publishing Client

Async httpx client for the Blotato API.
Follows the same pattern as upload_post.py.
"""
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()

BLOTATO_BASE_URL = "https://api.blotato.com/v1"


class BlotatoError(Exception):
    """Base Blotato API error."""
    pass


class BlotatoAuthError(BlotatoError):
    """API key invalid or missing."""
    pass


class BlotatoRateLimitError(BlotatoError):
    """Rate limit exceeded."""
    pass


class BlotatoClient:
    """Async client for the Blotato social publishing API."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.blotato_api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "blotato-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to Blotato API."""
        if not self._api_key:
            raise BlotatoAuthError("Blotato API key not configured. Set BLOTATO_API_KEY.")

        url = f"{BLOTATO_BASE_URL}{path}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers,
                    json=json,
                    params=params,
                )
            except httpx.TimeoutException:
                raise BlotatoError("Blotato API timeout (60s)")

            if response.status_code == 401:
                raise BlotatoAuthError("Blotato API key invalid or expired.")
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise BlotatoRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after}s"
                )
            if response.status_code >= 400:
                detail = ""
                try:
                    detail = response.json().get("message", response.text[:200])
                except Exception as e:
                    from app.core.observability import get_logger
                    get_logger(__name__).debug("Blotato error response not JSON", error=str(e))
                    detail = response.text[:200]
                raise BlotatoError(
                    f"Blotato API error {response.status_code}: {detail}"
                )

            return response.json()

    # ── Account Management ──

    async def get_accounts(self, platform: str | None = None) -> list[dict[str, Any]]:
        """Get connected social accounts.

        GET /users/me/accounts?platform=instagram
        """
        params = {}
        if platform:
            params["platform"] = platform

        data = await self._request("GET", "/users/me/accounts", params=params)
        accounts = data if isinstance(data, list) else data.get("accounts", data.get("data", []))
        logger.info("Blotato accounts fetched", count=len(accounts), platform=platform)
        return accounts

    async def get_subaccounts(self, account_id: str) -> list[dict[str, Any]]:
        """Get subaccounts (pages) for a parent account.

        GET /users/me/accounts/{account_id}/subaccounts
        """
        data = await self._request("GET", f"/users/me/accounts/{account_id}/subaccounts")
        subaccounts = data if isinstance(data, list) else data.get("subaccounts", data.get("data", []))
        logger.info("Blotato subaccounts fetched", account_id=account_id, count=len(subaccounts))
        return subaccounts

    # ── Publishing ──

    async def publish_post(
        self,
        account_id: str,
        platform: str,
        text: str,
        media_urls: list[str] | None = None,
        page_id: str | None = None,
        scheduled_at: str | None = None,
    ) -> dict[str, Any]:
        """Publish a post via Blotato.

        POST /posts
        """
        body: dict[str, Any] = {
            "account_id": account_id,
            "platform": platform,
            "text": text,
        }

        if media_urls:
            body["media_urls"] = media_urls
        if page_id:
            body["page_id"] = page_id
        if scheduled_at:
            body["scheduled_at"] = scheduled_at

        result = await self._request("POST", "/posts", json=body)
        logger.info(
            "Blotato post published",
            platform=platform,
            account_id=account_id,
            post_id=result.get("id"),
        )
        return result
