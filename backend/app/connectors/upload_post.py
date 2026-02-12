"""
PresenceOS - Upload-Post Connector

Uses the Upload-Post API (https://api.upload-post.com/api/upload)
to publish content on Instagram, Facebook, and TikTok.

LinkedIn remains handled by its native connector (linkedin.py).
"""
import structlog
from datetime import datetime, timezone
from typing import Any

import httpx

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()

UPLOAD_POST_API_URL = "https://api.upload-post.com/api/upload"


class UploadPostConnector(BaseConnector):
    """
    Connector for Instagram, Facebook, and TikTok via Upload-Post API.

    Upload-Post is a unified social media API that handles
    content adaptation (aspect ratios, file sizes, caption lengths)
    per platform automatically.
    """

    platform_name = "upload_post"

    def __init__(self, platform: str = "instagram"):
        super().__init__()
        self.api_key = settings.upload_post_api_key
        self.platform = platform

    # ── OAuth stubs (not used — Upload-Post uses API key auth) ──────────

    def get_oauth_url(self, state: str) -> tuple[str, str]:
        """Not applicable for Upload-Post (API key auth)."""
        raise NotImplementedError(
            "Upload-Post utilise une cle API, pas OAuth. "
            "Configurez UPLOAD_POST_API_KEY dans les parametres."
        )

    async def exchange_code(
        self, authorization_code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Not applicable for Upload-Post."""
        raise NotImplementedError("Upload-Post n'utilise pas OAuth.")

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Not applicable for Upload-Post (no token expiry)."""
        return {
            "access_token": self.api_key,
            "refresh_token": None,
            "expires_at": None,
            "scope": None,
        }

    async def revoke_token(self, access_token: str) -> bool:
        """Not applicable for Upload-Post."""
        return True

    async def get_account_info(self, access_token: str) -> dict[str, Any]:
        """Return basic info for Upload-Post connection."""
        return {
            "account_id": f"upload-post-{self.platform}",
            "account_name": f"Upload-Post ({self.platform.capitalize()})",
            "account_username": None,
            "account_avatar_url": None,
            "platform_data": {
                "provider": "upload-post",
                "platform": self.platform,
            },
        }

    # ── Publishing ──────────────────────────────────────────────────────

    async def publish(
        self,
        access_token: str,
        content: dict[str, Any],
        media_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Publish content via Upload-Post API.

        POST https://api.upload-post.com/api/upload
        Headers: Authorization: Apikey <key>
        Body (multipart/form-data):
          - title: caption text
          - platform[]: target platforms (instagram, facebook, tiktok)
          - user: account identifier (from connector account_username or account_id)
          - video/image: media file URL or binary
        """
        api_key = access_token or self.api_key
        if not api_key:
            raise ValueError(
                "Cle API Upload-Post manquante. "
                "Configurez UPLOAD_POST_API_KEY dans les parametres."
            )

        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])
        account_username = content.get("account_username") or content.get("account_id", "")
        platform = content.get("platform") or self.platform

        # Build full caption with hashtags
        full_caption = caption
        if hashtags:
            full_caption += "\n\n" + " ".join(f"#{tag}" for tag in hashtags)

        # Map internal platform names to Upload-Post names
        platform_map = {
            "instagram": "instagram",
            "facebook": "facebook",
            "tiktok": "tiktok",
        }
        target_platform = platform_map.get(platform, platform)

        logger.info(
            "Publishing via Upload-Post",
            platform=target_platform,
            has_media=bool(media_urls),
            caption_length=len(full_caption),
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Build multipart form data
            data = {
                "title": full_caption,
                "user": account_username,
            }
            files_payload: list[tuple] = []

            # Add platform(s)
            files_payload.append(("platform[]", (None, target_platform)))

            # Add media if present
            if media_urls:
                # Download the first media file and send it
                media_url = media_urls[0]
                try:
                    media_response = await client.get(media_url)
                    media_response.raise_for_status()

                    # Determine if video or image
                    content_type = media_response.headers.get("content-type", "")
                    is_video = "video" in content_type or media_url.endswith(
                        (".mp4", ".mov", ".webm", ".avi")
                    )
                    field_name = "video" if is_video else "image"
                    filename = f"media.{'mp4' if is_video else 'jpg'}"

                    files_payload.append(
                        (field_name, (filename, media_response.content, content_type or "application/octet-stream"))
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to download media for Upload-Post",
                        media_url=media_url,
                        error=str(e),
                    )
                    # Continue without media — some platforms allow text-only

            headers = {
                "Authorization": f"Apikey {api_key}",
            }

            try:
                response = await client.post(
                    UPLOAD_POST_API_URL,
                    data=data,
                    files=files_payload,
                    headers=headers,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Upload-Post rate limit atteint. Reessayer dans {retry_after}s"
                    )

                # Handle auth error
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Cle API Upload-Post invalide ou expiree."
                    )

                # Handle content rejection
                if response.status_code == 422:
                    detail = response.json().get("detail", response.text)
                    raise ContentRejectedError(
                        f"Contenu rejete par Upload-Post: {detail}"
                    )

                response.raise_for_status()
                result = response.json()

                # Extract post info from response
                post_id = result.get("id") or result.get("post_id", "")
                post_url = None

                # Try to extract platform-specific URL
                platforms_result = result.get("platforms", [])
                if isinstance(platforms_result, list):
                    for p in platforms_result:
                        if p.get("name", "").lower() == target_platform:
                            post_url = p.get("url")
                            break
                elif isinstance(platforms_result, dict):
                    post_url = platforms_result.get(target_platform, {}).get("url")

                # Fallback URL extraction
                if not post_url:
                    post_url = result.get("url") or result.get("post_url")

                logger.info(
                    "Upload-Post publish success",
                    platform=target_platform,
                    post_id=post_id,
                    post_url=post_url,
                )

                return {
                    "post_id": str(post_id),
                    "post_url": post_url,
                    "published_at": datetime.now(timezone.utc),
                    "platform_response": result,
                }

            except (RateLimitError, AuthenticationError, ContentRejectedError):
                raise
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Upload-Post API error",
                    status_code=e.response.status_code,
                    response=e.response.text[:500],
                )
                raise PublishError(
                    f"Erreur API Upload-Post ({e.response.status_code}): {e.response.text[:200]}"
                ) from e
            except httpx.TimeoutException:
                raise PublishError(
                    "Timeout lors de la publication via Upload-Post. "
                    "Le serveur n'a pas repondu dans les 120 secondes."
                )

    # ── Post status & metrics (limited with Upload-Post) ────────────────

    async def get_post_status(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """Get post status (limited with Upload-Post)."""
        return {
            "status": "published",
            "post_url": None,
            "error": None,
        }

    async def get_post_metrics(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """Get post metrics (not available via Upload-Post)."""
        return {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "impressions": 0,
            "reach": 0,
        }

    async def get_account_metrics(self, access_token: str) -> dict[str, Any]:
        """Get account metrics (not available via Upload-Post)."""
        return {
            "followers_count": 0,
            "followers_gained": 0,
        }


# ── Custom exceptions ───────────────────────────────────────────────────

class UploadPostError(Exception):
    """Base exception for Upload-Post errors."""
    pass


class RateLimitError(UploadPostError):
    """Raised when API rate limit is hit."""
    pass


class AuthenticationError(UploadPostError):
    """Raised when API key is invalid."""
    pass


class ContentRejectedError(UploadPostError):
    """Raised when content is rejected by the platform."""
    pass


class PublishError(UploadPostError):
    """Generic publish error."""
    pass
