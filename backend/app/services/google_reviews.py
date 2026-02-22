"""
PresenceOS - Google Business Profile Reviews Service

Handles fetching reviews and publishing replies via the
Google Business Profile API (mybusiness.googleapis.com/v4).
"""
import httpx
import structlog

logger = structlog.get_logger()

GBP_BASE_URL = "https://mybusiness.googleapis.com/v4"


class GoogleReviewsService:
    """Client for Google Business Profile Reviews API."""

    def __init__(self, access_token: str, account_id: str, location_id: str) -> None:
        self.access_token = access_token
        self.account_id = account_id
        self.location_id = location_id

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @property
    def _location_path(self) -> str:
        return f"accounts/{self.account_id}/locations/{self.location_id}"

    async def list_reviews(self, page_size: int = 50, page_token: str | None = None) -> dict:
        """Fetch reviews from Google Business Profile.

        GET /accounts/{accountId}/locations/{locationId}/reviews

        Returns:
            {
                "reviews": [...],
                "averageRating": float,
                "totalReviewCount": int,
                "nextPageToken": str | None,
            }
        """
        url = f"{GBP_BASE_URL}/{self._location_path}/reviews"
        params: dict[str, str | int] = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self._headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def reply_to_review(self, review_id: str, comment: str) -> dict:
        """Post a reply to a Google review.

        PUT /accounts/{accountId}/locations/{locationId}/reviews/{reviewId}/reply
        Body: {"comment": "..."}

        Returns the reply object from Google.
        """
        url = f"{GBP_BASE_URL}/{self._location_path}/reviews/{review_id}/reply"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(
                url,
                headers=self._headers,
                json={"comment": comment},
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_reply(self, review_id: str) -> None:
        """Delete a reply from a Google review.

        DELETE /accounts/{accountId}/locations/{locationId}/reviews/{reviewId}/reply
        """
        url = f"{GBP_BASE_URL}/{self._location_path}/reviews/{review_id}/reply"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(url, headers=self._headers)
            resp.raise_for_status()
