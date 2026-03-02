"""
PresenceOS - Google My Business Service
Handles GMB API interactions for autopublishing posts.
"""
import structlog
import httpx
from datetime import datetime, timezone

from app.core.config import settings

logger = structlog.get_logger()

GMB_API_BASE = "https://mybusiness.googleapis.com/v4"


class GMBService:
    """Google My Business API integration."""

    def __init__(self, access_token: str):
        self.access_token = access_token

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def create_local_post(
        self,
        account_id: str,
        location_id: str,
        summary: str,
        image_url: str | None = None,
        call_to_action: dict | None = None,
    ) -> dict:
        """Create a local post on Google My Business."""
        url = f"{GMB_API_BASE}/accounts/{account_id}/locations/{location_id}/localPosts"

        post_data: dict = {
            "languageCode": "fr",
            "summary": summary[:1500],  # GMB limit
            "topicType": "STANDARD",
        }

        if image_url:
            post_data["media"] = [{
                "mediaFormat": "PHOTO",
                "sourceUrl": image_url,
            }]

        if call_to_action:
            post_data["callToAction"] = call_to_action

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self._headers,
                    json=post_data,
                )
                if response.status_code == 200:
                    result = response.json()
                    logger.info("GMB post created", location_id=location_id)
                    return {"status": "published", "post": result}
                else:
                    logger.error("GMB post failed", status=response.status_code, body=response.text[:200])
                    return {"status": "failed", "error": response.text[:200]}
        except Exception as exc:
            logger.error("GMB API error", error=str(exc))
            return {"status": "error", "error": str(exc)}

    async def get_locations(self, account_id: str) -> list[dict]:
        """List locations for a GMB account."""
        url = f"{GMB_API_BASE}/accounts/{account_id}/locations"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("locations", [])
                return []
        except Exception as exc:
            logger.error("GMB locations fetch failed", error=str(exc))
            return []

    async def get_reviews(self, account_id: str, location_id: str) -> list[dict]:
        """Fetch reviews for a location."""
        url = f"{GMB_API_BASE}/accounts/{account_id}/locations/{location_id}/reviews"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("reviews", [])
                return []
        except Exception as exc:
            logger.error("GMB reviews fetch failed", error=str(exc))
            return []
