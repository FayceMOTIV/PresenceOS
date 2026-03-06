"""
PresenceOS — Meta Token Manager

Manages Meta (Instagram/Facebook) long-lived access tokens.
- Stores tokens in Redis with 55-day TTL (tokens expire at 60 days)
- Refreshes tokens via Meta Graph API before expiry
- Falls back to settings.meta_access_token if Redis is empty
"""
import logging

import httpx
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

REDIS_KEY = "presenceos:meta:access_token"
TOKEN_TTL_DAYS = 55  # Refresh before 60-day expiry
GRAPH_API_BASE = f"https://graph.facebook.com/{settings.meta_graph_version}"


class MetaTokenManager:
    """Manage Meta long-lived token lifecycle via Redis."""

    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def get_token(self) -> str:
        """Get the current Meta access token (Redis first, env fallback)."""
        try:
            r = await self._get_redis()
            token = await r.get(REDIS_KEY)
            if token:
                return token
        except Exception as exc:
            logger.warning("Redis read failed for Meta token", extra={"error": str(exc)})

        return settings.meta_access_token

    async def store_token(self, token: str) -> None:
        """Store a new token in Redis with TTL."""
        try:
            r = await self._get_redis()
            await r.set(REDIS_KEY, token, ex=TOKEN_TTL_DAYS * 86400)
            logger.info("Meta token stored in Redis", extra={"ttl_days": TOKEN_TTL_DAYS})
        except Exception as exc:
            logger.error("Failed to store Meta token in Redis", extra={"error": str(exc)})

    async def refresh(self) -> dict:
        """Refresh the Meta long-lived token via Graph API.

        Returns dict with success status and new expiry info.
        """
        current_token = await self.get_token()
        if not current_token:
            return {"success": False, "error": "No Meta token configured"}

        if not settings.meta_app_id or not settings.meta_app_secret:
            return {"success": False, "error": "meta_app_id/meta_app_secret not configured"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{GRAPH_API_BASE}/oauth/access_token",
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": settings.meta_app_id,
                        "client_secret": settings.meta_app_secret,
                        "fb_exchange_token": current_token,
                    },
                )
                response.raise_for_status()
                data = response.json()

            new_token = data["access_token"]
            expires_in = data.get("expires_in", 5184000)  # Default 60 days

            await self.store_token(new_token)

            logger.info(
                "Meta token refreshed successfully",
                extra={"expires_in_days": expires_in // 86400},
            )
            return {
                "success": True,
                "expires_in_days": expires_in // 86400,
            }

        except httpx.HTTPStatusError as exc:
            error_msg = f"Meta API error {exc.response.status_code}: {exc.response.text[:200]}"
            logger.error("Meta token refresh failed", extra={"error": error_msg})
            return {"success": False, "error": error_msg}
        except Exception as exc:
            logger.error("Meta token refresh failed", extra={"error": str(exc)})
            return {"success": False, "error": str(exc)}

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None
