"""
PresenceOS - TikTok Connector

Uses the TikTok Content Posting API.
Documentation: https://developers.tiktok.com/doc/content-posting-api-get-started
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

# TikTok API endpoints
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# Required scopes
TIKTOK_SCOPES = [
    "user.info.basic",
    "video.publish",
    "video.upload",
]


class TikTokConnector(BaseConnector):
    """Connector for TikTok Content Posting API."""

    platform_name = "tiktok"

    def __init__(self):
        super().__init__()
        self.client_key = settings.tiktok_client_key
        self.client_secret = settings.tiktok_client_secret
        self.redirect_uri = settings.tiktok_redirect_uri

    def get_oauth_url(self, state: str) -> tuple[str, str]:
        """Generate TikTok OAuth URL."""
        oauth_state = f"{state}_{secrets.token_urlsafe(16)}"
        code_verifier = secrets.token_urlsafe(64)  # PKCE

        params = {
            "client_key": self.client_key,
            "redirect_uri": self.redirect_uri,
            "scope": ",".join(TIKTOK_SCOPES),
            "response_type": "code",
            "state": oauth_state,
            "code_challenge": code_verifier,  # Simplified, should be hashed
            "code_challenge_method": "S256",
        }

        url = f"{TIKTOK_AUTH_URL}?{urlencode(params)}"
        return url, oauth_state

    async def exchange_code(
        self, authorization_code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TIKTOK_TOKEN_URL,
                data={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "code": authorization_code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

            expires_in = data.get("expires_in", 86400)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "scope": data.get("scope"),
                "open_id": data.get("open_id"),
            }

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh TikTok access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TIKTOK_TOKEN_URL,
                data={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

            expires_in = data.get("expires_in", 86400)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "scope": data.get("scope"),
            }

    async def revoke_token(self, access_token: str) -> bool:
        """Revoke TikTok access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TIKTOK_API_BASE}/oauth/revoke/",
                    data={
                        "client_key": self.client_key,
                        "client_secret": self.client_secret,
                        "token": access_token,
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("Failed to revoke TikTok token", error=str(e))
            return False

    async def get_account_info(self, access_token: str) -> dict[str, Any]:
        """Get TikTok user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TIKTOK_API_BASE}/user/info/",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"fields": "open_id,union_id,avatar_url,display_name,username"},
            )
            response.raise_for_status()
            data = response.json().get("data", {}).get("user", {})

            return {
                "account_id": data.get("open_id"),
                "account_name": data.get("display_name"),
                "account_username": data.get("username"),
                "account_avatar_url": data.get("avatar_url"),
                "platform_data": {
                    "open_id": data.get("open_id"),
                    "union_id": data.get("union_id"),
                },
            }

    async def publish(
        self,
        access_token: str,
        content: dict[str, Any],
        media_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Publish video to TikTok.

        TikTok Content Posting API flow:
        1. Initialize video upload
        2. Upload video file (or provide URL)
        3. Post the video

        Note: TikTok requires videos to be uploaded via URL from cloud storage.
        """
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])

        # Combine caption with hashtags
        full_caption = caption
        if hashtags:
            full_caption += " " + " ".join(f"#{tag}" for tag in hashtags)

        if not media_urls:
            raise ValueError("TikTok posts require a video URL")

        video_url = media_urls[0]

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Initialize post
            init_response = await client.post(
                f"{TIKTOK_API_BASE}/post/publish/video/init/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "post_info": {
                        "title": full_caption[:150],  # TikTok title limit
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": video_url,
                    },
                },
            )
            init_response.raise_for_status()
            init_data = init_response.json().get("data", {})

            publish_id = init_data.get("publish_id")

            if not publish_id:
                raise ValueError("Failed to initialize TikTok post")

            # Step 2: Check status (TikTok processes asynchronously)
            # In production, you'd poll this or use webhooks
            return {
                "post_id": publish_id,
                "post_url": None,  # URL available after processing
                "published_at": datetime.now(timezone.utc),
                "platform_response": init_data,
            }

    async def get_post_status(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """Check TikTok post publishing status."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"publish_id": post_id},
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                status = data.get("status")

                status_map = {
                    "PROCESSING_UPLOAD": "processing",
                    "PROCESSING_DOWNLOAD": "processing",
                    "SEND_TO_USER_INBOX": "published",
                    "PUBLISH_COMPLETE": "published",
                    "FAILED": "failed",
                }

                return {
                    "status": status_map.get(status, "unknown"),
                    "post_url": data.get("publicaly_available_post_id"),
                    "error": data.get("fail_reason") if status == "FAILED" else None,
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
        Get metrics for a TikTok video.
        Note: Requires video.list scope and the video must be accessible.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TIKTOK_API_BASE}/video/query/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "filters": {"video_ids": [post_id]},
                    "fields": [
                        "like_count",
                        "comment_count",
                        "share_count",
                        "view_count",
                    ],
                },
            )

            metrics = {
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "video_views": 0,
                "impressions": 0,
                "reach": 0,
            }

            if response.status_code == 200:
                videos = response.json().get("data", {}).get("videos", [])
                if videos:
                    video = videos[0]
                    metrics["likes"] = video.get("like_count", 0)
                    metrics["comments"] = video.get("comment_count", 0)
                    metrics["shares"] = video.get("share_count", 0)
                    metrics["video_views"] = video.get("view_count", 0)
                    metrics["impressions"] = video.get("view_count", 0)

            return metrics

    async def get_account_metrics(self, access_token: str) -> dict[str, Any]:
        """Get TikTok account metrics."""
        # TikTok doesn't provide direct follower count via Content Posting API
        # Would need Business API for analytics
        return {
            "followers_count": 0,
            "followers_gained": 0,
        }
