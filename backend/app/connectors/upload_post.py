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

UPLOAD_POST_VIDEO_URL = "https://api.upload-post.com/api/upload"
UPLOAD_POST_PHOTO_URL = "https://api.upload-post.com/api/upload_photos"


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

    def decrypt_token(self, encrypted_token: str) -> str:
        """Upload-Post uses API key, not per-account OAuth tokens."""
        return self.api_key or ""

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

    async def get_account_info(self, access_token: str, **kwargs: Any) -> dict[str, Any]:
        """Return basic info for Upload-Post connection.

        Args:
            access_token: The API key (unused, server-side key is used).
            account_username: Optional social account username to distinguish
                multiple accounts on the same platform.
        """
        username = kwargs.get("account_username") or f"upload-post-{self.platform}"
        return {
            "account_id": f"{self.platform}-{username}",
            "account_name": f"{username} ({self.platform.capitalize()})",
            "account_username": username,
            "account_avatar_url": None,
            "platform_data": {
                "provider": "upload-post",
                "platform": self.platform,
            },
        }

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _download_media(url: str) -> tuple[bytes, str]:
        """Download media from a URL, using S3 client for MinIO URLs.

        Returns (bytes, content_type).
        """
        s3_key = UploadPostConnector._extract_s3_key(url)
        if s3_key:
            # Use S3 client for authenticated access to MinIO
            import boto3
            from botocore.client import Config as BotoConfig
            import io

            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
                config=BotoConfig(signature_version="s3v4"),
            )
            buf = io.BytesIO()
            client.download_fileobj(settings.s3_bucket_name, s3_key, buf)
            buf.seek(0)

            # Guess content type from extension
            import mimetypes
            ct, _ = mimetypes.guess_type(s3_key)
            content_type = ct or "application/octet-stream"

            logger.info("Downloaded media via S3", key=s3_key, size=buf.getbuffer().nbytes)
            return buf.read(), content_type

        # Fallback: plain HTTP GET for external URLs
        import httpx as _httpx
        with _httpx.Client(timeout=60.0) as http:
            resp = http.get(url)
            resp.raise_for_status()
            return resp.content, resp.headers.get("content-type", "application/octet-stream")

    @staticmethod
    def _extract_s3_key(url: str) -> str | None:
        """Extract S3 object key from a MinIO/S3 URL, or return None if not an S3 URL."""
        from urllib.parse import urlparse
        bucket = settings.s3_bucket_name  # e.g. presenceos-media
        s3_public = settings.s3_public_url or ""
        s3_internal = settings.s3_endpoint_url or ""

        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        # Check if URL is from our MinIO (public or internal)
        public_origin = urlparse(s3_public).netloc if s3_public else ""
        internal_origin = urlparse(s3_internal).netloc if s3_internal else ""

        if parsed.netloc not in (public_origin, internal_origin):
            return None

        # Path is like /presenceos-media/brands/... or /presenceos-media/presenceos-media/brands/...
        path = parsed.path.lstrip("/")

        # Strip bucket name prefix (possibly duplicated)
        if path.startswith(f"{bucket}/{bucket}/"):
            path = path[len(f"{bucket}/{bucket}/"):]
        elif path.startswith(f"{bucket}/"):
            path = path[len(f"{bucket}/"):]

        return path if path else None

    @staticmethod
    def _resolve_internal_url(url: str) -> str:
        """Rewrite localhost MinIO URLs to Docker-internal hostname.

        Media URLs stored in DB use S3_PUBLIC_URL (e.g. http://localhost:9000/...)
        but workers inside Docker need the internal hostname (minio:9000).
        Also fixes duplicate bucket name in path (legacy bug).
        """
        s3_internal = settings.s3_endpoint_url  # e.g. http://minio:9000
        s3_public = settings.s3_public_url       # e.g. http://localhost:9000/presenceos-media
        bucket = settings.s3_bucket_name          # e.g. presenceos-media

        if s3_public and s3_internal:
            from urllib.parse import urlparse
            parsed_public = urlparse(s3_public)
            public_origin = f"{parsed_public.scheme}://{parsed_public.netloc}"

            parsed_internal = urlparse(s3_internal)
            internal_origin = f"{parsed_internal.scheme}://{parsed_internal.netloc}"

            if url.startswith(public_origin):
                resolved = url.replace(public_origin, internal_origin, 1)

                # Fix duplicate bucket name in path (legacy bug):
                # e.g. /presenceos-media/presenceos-media/brands/... -> /presenceos-media/brands/...
                if bucket:
                    dup = f"/{bucket}/{bucket}/"
                    if dup in resolved:
                        resolved = resolved.replace(dup, f"/{bucket}/", 1)

                logger.debug(
                    "Resolved media URL for Docker",
                    original=url[:80],
                    resolved=resolved[:80],
                )
                return resolved

        return url

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
        # Upload-Post expects username without @ prefix
        if account_username and account_username.startswith("@"):
            account_username = account_username[1:]
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

            # Add media if present — determines which endpoint to use
            is_video = False
            if media_urls:
                media_url = media_urls[0]

                try:
                    media_bytes, content_type = self._download_media(media_url)

                    # Determine if video or image
                    is_video = "video" in content_type or media_url.endswith(
                        (".mp4", ".mov", ".webm", ".avi")
                    )

                    if is_video:
                        # Video endpoint uses field "video"
                        files_payload.append(
                            ("video", (f"media.mp4", media_bytes, content_type or "video/mp4"))
                        )
                    else:
                        # Photo endpoint uses field "photos[]"
                        files_payload.append(
                            ("photos[]", (f"media.jpg", media_bytes, content_type or "image/jpeg"))
                        )

                    logger.info(
                        "Media prepared for Upload-Post",
                        is_video=is_video,
                        size=len(media_bytes),
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to download media for Upload-Post",
                        media_url=media_url,
                        error=str(e),
                    )
                    # Continue without media — some platforms allow text-only

            # Select endpoint based on media type
            api_url = UPLOAD_POST_VIDEO_URL if is_video else UPLOAD_POST_PHOTO_URL

            headers = {
                "Authorization": f"Apikey {api_key}",
            }

            try:
                logger.info(
                    "Sending to Upload-Post",
                    endpoint=api_url,
                    is_video=is_video,
                    platform=target_platform,
                )
                response = await client.post(
                    api_url,
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
