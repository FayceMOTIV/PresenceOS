"""
PresenceOS - Meta (Instagram/Facebook) Connector

Uses the Meta Graph API for Instagram Content Publishing API.
Documentation: https://developers.facebook.com/docs/instagram-api/guides/content-publishing
"""
import secrets
import structlog
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()

# Meta Graph API base URL
GRAPH_API_BASE = f"https://graph.facebook.com/{settings.meta_graph_version}"

# Required scopes for Instagram publishing
INSTAGRAM_SCOPES = [
    "instagram_basic",
    "instagram_content_publish",
    "instagram_manage_comments",
    "instagram_manage_insights",
    "pages_show_list",
    "pages_read_engagement",
    "business_management",
]


class MetaConnector(BaseConnector):
    """Connector for Instagram via Meta Graph API."""

    platform_name = "instagram"

    def __init__(self):
        super().__init__()
        self.app_id = settings.meta_app_id
        self.app_secret = settings.meta_app_secret
        self.redirect_uri = settings.meta_redirect_uri

    def get_oauth_url(self, state: str) -> tuple[str, str]:
        """Generate Meta OAuth URL for Instagram Business accounts."""
        # Generate state with brand_id encoded
        oauth_state = f"{state}_{secrets.token_urlsafe(16)}"

        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": ",".join(INSTAGRAM_SCOPES),
            "response_type": "code",
            "state": oauth_state,
        }

        url = f"https://www.facebook.com/{settings.meta_graph_version}/dialog/oauth?{urlencode(params)}"
        return url, oauth_state

    async def exchange_code(
        self, authorization_code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            # Get short-lived token
            response = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": redirect_uri,
                    "code": authorization_code,
                },
            )
            response.raise_for_status()
            data = response.json()

            short_lived_token = data["access_token"]

            # Exchange for long-lived token (60 days)
            response = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "fb_exchange_token": short_lived_token,
                },
            )
            response.raise_for_status()
            data = response.json()

            expires_in = data.get("expires_in", 5184000)  # Default 60 days
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data["access_token"],
                "refresh_token": None,  # Meta uses token refresh differently
                "expires_at": expires_at,
                "scope": ",".join(INSTAGRAM_SCOPES),
            }

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh Meta access token.
        Note: Meta long-lived tokens can be refreshed before expiry.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "fb_exchange_token": refresh_token,  # Use existing token
                },
            )
            response.raise_for_status()
            data = response.json()

            expires_in = data.get("expires_in", 5184000)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data["access_token"],
                "refresh_token": None,
                "expires_at": expires_at,
                "scope": ",".join(INSTAGRAM_SCOPES),
            }

    async def revoke_token(self, access_token: str) -> bool:
        """Revoke access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{GRAPH_API_BASE}/me/permissions",
                    params={"access_token": access_token},
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("Failed to revoke Meta token", error=str(e))
            return False

    async def get_account_info(self, access_token: str) -> dict[str, Any]:
        """Get connected Instagram Business account info."""
        async with httpx.AsyncClient() as client:
            # Get Facebook pages
            response = await client.get(
                f"{GRAPH_API_BASE}/me/accounts",
                params={
                    "access_token": access_token,
                    "fields": "id,name,access_token,instagram_business_account",
                },
            )
            response.raise_for_status()
            pages = response.json().get("data", [])

            # Find page with Instagram Business account
            for page in pages:
                if "instagram_business_account" in page:
                    ig_account_id = page["instagram_business_account"]["id"]

                    # Get Instagram account details
                    ig_response = await client.get(
                        f"{GRAPH_API_BASE}/{ig_account_id}",
                        params={
                            "access_token": access_token,
                            "fields": "id,username,name,profile_picture_url,followers_count",
                        },
                    )
                    ig_response.raise_for_status()
                    ig_data = ig_response.json()

                    return {
                        "account_id": ig_account_id,
                        "account_name": ig_data.get("name"),
                        "account_username": ig_data.get("username"),
                        "account_avatar_url": ig_data.get("profile_picture_url"),
                        "platform_data": {
                            "page_id": page["id"],
                            "page_access_token": page["access_token"],
                            "followers_count": ig_data.get("followers_count"),
                        },
                    }

            raise ValueError("No Instagram Business account found. Please connect a Facebook Page with an Instagram Business account.")

    async def publish(
        self,
        access_token: str,
        content: dict[str, Any],
        media_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Publish content to Instagram.

        Two-step process:
        1. Create media container
        2. Publish the container
        """
        account_id = content.get("account_id")
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])

        # Combine caption with hashtags
        full_caption = caption
        if hashtags:
            full_caption += "\n\n" + " ".join(f"#{tag}" for tag in hashtags)

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Create media container
            if media_urls and len(media_urls) > 1:
                # Carousel post
                children_ids = []
                for url in media_urls[:10]:  # Max 10 items
                    child_response = await client.post(
                        f"{GRAPH_API_BASE}/{account_id}/media",
                        params={
                            "access_token": access_token,
                            "image_url": url,
                            "is_carousel_item": "true",
                        },
                    )
                    child_response.raise_for_status()
                    children_ids.append(child_response.json()["id"])

                container_response = await client.post(
                    f"{GRAPH_API_BASE}/{account_id}/media",
                    params={
                        "access_token": access_token,
                        "media_type": "CAROUSEL",
                        "children": ",".join(children_ids),
                        "caption": full_caption,
                    },
                )
            elif media_urls and media_urls[0].endswith((".mp4", ".mov")):
                # Video/Reel
                container_response = await client.post(
                    f"{GRAPH_API_BASE}/{account_id}/media",
                    params={
                        "access_token": access_token,
                        "media_type": "REELS",
                        "video_url": media_urls[0],
                        "caption": full_caption,
                    },
                )
            else:
                # Single image
                container_response = await client.post(
                    f"{GRAPH_API_BASE}/{account_id}/media",
                    params={
                        "access_token": access_token,
                        "image_url": media_urls[0] if media_urls else "",
                        "caption": full_caption,
                    },
                )

            container_response.raise_for_status()
            container_id = container_response.json()["id"]

            # Step 2: Publish the container
            # For video, we may need to wait for processing
            publish_response = await client.post(
                f"{GRAPH_API_BASE}/{account_id}/media_publish",
                params={
                    "access_token": access_token,
                    "creation_id": container_id,
                },
            )
            publish_response.raise_for_status()
            post_id = publish_response.json()["id"]

            # Get post permalink
            permalink_response = await client.get(
                f"{GRAPH_API_BASE}/{post_id}",
                params={
                    "access_token": access_token,
                    "fields": "permalink",
                },
            )
            permalink = None
            if permalink_response.status_code == 200:
                permalink = permalink_response.json().get("permalink")

            return {
                "post_id": post_id,
                "post_url": permalink,
                "published_at": datetime.now(timezone.utc),
                "platform_response": {"container_id": container_id},
            }

    async def get_post_status(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """Get post status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE}/{post_id}",
                params={
                    "access_token": access_token,
                    "fields": "id,permalink,timestamp",
                },
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "published",
                    "post_url": data.get("permalink"),
                    "error": None,
                }
            else:
                return {
                    "status": "error",
                    "post_url": None,
                    "error": response.text,
                }

    async def get_post_metrics(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """Get metrics for a published post."""
        async with httpx.AsyncClient() as client:
            # Get basic metrics
            response = await client.get(
                f"{GRAPH_API_BASE}/{post_id}",
                params={
                    "access_token": access_token,
                    "fields": "like_count,comments_count",
                },
            )
            response.raise_for_status()
            basic_data = response.json()

            # Get insights
            insights_response = await client.get(
                f"{GRAPH_API_BASE}/{post_id}/insights",
                params={
                    "access_token": access_token,
                    "metric": "impressions,reach,saved,shares",
                },
            )

            metrics = {
                "likes": basic_data.get("like_count", 0),
                "comments": basic_data.get("comments_count", 0),
                "impressions": 0,
                "reach": 0,
                "saves": 0,
                "shares": 0,
            }

            if insights_response.status_code == 200:
                insights = insights_response.json().get("data", [])
                for insight in insights:
                    name = insight.get("name")
                    value = insight.get("values", [{}])[0].get("value", 0)
                    if name in metrics:
                        metrics[name] = value

            return metrics

    async def get_account_metrics(self, access_token: str) -> dict[str, Any]:
        """Get account-level metrics."""
        # Get account ID from stored platform_data
        # This would need the account_id passed in
        return {
            "followers_count": 0,
            "followers_gained": 0,
        }
