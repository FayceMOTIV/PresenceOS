"""
PresenceOS - LinkedIn Connector

Uses the LinkedIn Marketing API for posting.
Documentation: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
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

# LinkedIn API endpoints
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_REST_BASE = "https://api.linkedin.com/rest"

# Required scopes
LINKEDIN_SCOPES = [
    "openid",
    "profile",
    "w_member_social",
    "r_organization_social",
    "w_organization_social",
    "rw_organization_admin",
]


class LinkedInConnector(BaseConnector):
    """Connector for LinkedIn Posts API."""

    platform_name = "linkedin"

    def __init__(self):
        super().__init__()
        self.client_id = settings.linkedin_client_id
        self.client_secret = settings.linkedin_client_secret
        self.redirect_uri = settings.linkedin_redirect_uri

    def get_oauth_url(self, state: str) -> tuple[str, str]:
        """Generate LinkedIn OAuth URL."""
        oauth_state = f"{state}_{secrets.token_urlsafe(16)}"

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(LINKEDIN_SCOPES),
            "state": oauth_state,
        }

        url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
        return url, oauth_state

    async def exchange_code(
        self, authorization_code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

            expires_in = data.get("expires_in", 5184000)  # Default 60 days
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "scope": data.get("scope"),
            }

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh LinkedIn access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

            expires_in = data.get("expires_in", 5184000)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "scope": data.get("scope"),
            }

    async def revoke_token(self, access_token: str) -> bool:
        """Revoke LinkedIn access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.linkedin.com/oauth/v2/revoke",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "token": access_token,
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("Failed to revoke LinkedIn token", error=str(e))
            return False

    async def get_account_info(self, access_token: str) -> dict[str, Any]:
        """Get LinkedIn user/organization info."""
        async with httpx.AsyncClient() as client:
            # Get user info
            response = await client.get(
                f"{LINKEDIN_API_BASE}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            user_data = response.json()

            # Get member URN for posting
            me_response = await client.get(
                f"{LINKEDIN_API_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            me_data = {}
            if me_response.status_code == 200:
                me_data = me_response.json()

            member_id = me_data.get("id") or user_data.get("sub")

            return {
                "account_id": member_id,
                "account_name": user_data.get("name"),
                "account_username": user_data.get("email"),
                "account_avatar_url": user_data.get("picture"),
                "platform_data": {
                    "member_urn": f"urn:li:person:{member_id}",
                    "locale": user_data.get("locale"),
                },
            }

    async def publish(
        self,
        access_token: str,
        content: dict[str, Any],
        media_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Publish post to LinkedIn.

        Uses the new Posts API (replaces UGC Posts).
        """
        author_urn = content.get("author_urn")  # e.g., "urn:li:person:123"
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])

        # Combine caption with hashtags
        full_text = caption
        if hashtags:
            full_text += "\n\n" + " ".join(f"#{tag}" for tag in hashtags)

        async with httpx.AsyncClient(timeout=60.0) as client:
            if media_urls:
                # Post with image
                # First, register the image upload
                register_response = await client.post(
                    f"{LINKEDIN_REST_BASE}/images?action=initializeUpload",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "LinkedIn-Version": "202401",
                    },
                    json={
                        "initializeUploadRequest": {
                            "owner": author_urn,
                        }
                    },
                )

                image_urn = None
                if register_response.status_code == 200:
                    register_data = register_response.json()
                    upload_url = register_data["value"]["uploadUrl"]
                    image_urn = register_data["value"]["image"]

                    # Download image from URL and upload to LinkedIn
                    image_response = await client.get(media_urls[0])
                    if image_response.status_code == 200:
                        await client.put(
                            upload_url,
                            content=image_response.content,
                            headers={"Content-Type": "image/jpeg"},
                        )

                # Create post with image
                post_body = {
                    "author": author_urn,
                    "commentary": full_text,
                    "visibility": "PUBLIC",
                    "distribution": {
                        "feedDistribution": "MAIN_FEED",
                    },
                    "lifecycleState": "PUBLISHED",
                }

                if image_urn:
                    post_body["content"] = {
                        "media": {
                            "id": image_urn,
                        }
                    }

            else:
                # Text-only post
                post_body = {
                    "author": author_urn,
                    "commentary": full_text,
                    "visibility": "PUBLIC",
                    "distribution": {
                        "feedDistribution": "MAIN_FEED",
                    },
                    "lifecycleState": "PUBLISHED",
                }

            # Create the post
            response = await client.post(
                f"{LINKEDIN_REST_BASE}/posts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "LinkedIn-Version": "202401",
                },
                json=post_body,
            )
            response.raise_for_status()

            # Get post ID from response header
            post_urn = response.headers.get("x-restli-id", "")
            post_id = post_urn.split(":")[-1] if post_urn else ""

            return {
                "post_id": post_id,
                "post_url": f"https://www.linkedin.com/feed/update/{post_urn}/" if post_urn else None,
                "published_at": datetime.now(timezone.utc),
                "platform_response": {"urn": post_urn},
            }

    async def get_post_status(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """Get LinkedIn post status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LINKEDIN_REST_BASE}/posts/{post_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "LinkedIn-Version": "202401",
                },
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "published",
                    "post_url": f"https://www.linkedin.com/feed/update/urn:li:share:{post_id}/",
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
        """
        Get metrics for a LinkedIn post.
        Note: Requires organization analytics scope for detailed metrics.
        """
        async with httpx.AsyncClient() as client:
            # Get social actions (likes, comments)
            response = await client.get(
                f"{LINKEDIN_API_BASE}/socialActions/urn:li:share:{post_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )

            metrics = {
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "impressions": 0,
                "reach": 0,
                "clicks": 0,
            }

            if response.status_code == 200:
                data = response.json()
                # LinkedIn API structure varies
                metrics["likes"] = data.get("likesSummary", {}).get("totalLikes", 0)
                metrics["comments"] = data.get("commentsSummary", {}).get("totalFirstLevelComments", 0)

            return metrics

    async def get_account_metrics(self, access_token: str) -> dict[str, Any]:
        """Get LinkedIn account metrics."""
        # Personal profiles don't expose follower count via API
        # Organization pages would need different endpoints
        return {
            "followers_count": 0,
            "followers_gained": 0,
        }
