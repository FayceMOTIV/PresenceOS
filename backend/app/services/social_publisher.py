"""
PresenceOS - Unified Social Publisher via Upload-Post API

Handles all social media publishing through Upload-Post
(https://docs.upload-post.com).

Key insight from API: GET /uploadposts/users returns ALL profiles for the
API key. Each profile has a `social_accounts` dict keyed by platform name,
where connected accounts are dicts and disconnected ones are empty strings.
"""
import structlog
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings

logger = structlog.get_logger()

UPLOAD_POST_BASE = "https://api.upload-post.com/api"


class UploadPostError(Exception):
    pass


class UploadPostAuthError(UploadPostError):
    pass


class UploadPostRateLimitError(UploadPostError):
    pass


class SocialPublisher:

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.upload_post_api_key
        if not self.api_key:
            raise UploadPostAuthError(
                "UPLOAD_POST_API_KEY manquante. Configurez-la dans .env."
            )

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Apikey {self.api_key}"}

    @property
    def _json_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Apikey {self.api_key}",
            "Content-Type": "application/json",
        }

    def _handle_error(self, response: httpx.Response, context: str = "") -> None:
        if response.status_code == 401:
            raise UploadPostAuthError("Cle API Upload-Post invalide ou expiree.")
        if response.status_code == 429:
            raise UploadPostRateLimitError("Rate limit Upload-Post atteint.")
        if response.status_code >= 400:
            detail = ""
            try:
                detail = response.json().get("message", response.text[:300])
            except Exception:
                detail = response.text[:300]
            raise UploadPostError(
                f"Erreur Upload-Post {context} ({response.status_code}): {detail}"
            )

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _get_all_profiles(self) -> list[dict[str, Any]]:
        """GET /uploadposts/users → returns {"profiles": [...]}."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{UPLOAD_POST_BASE}/uploadposts/users",
                headers=self._json_headers,
            )
            self._handle_error(r, "get_all_profiles")
            data = r.json()
            return data.get("profiles", [])

    async def _find_profile(self, username: str) -> dict[str, Any] | None:
        """Find a specific profile by username (case-insensitive)."""
        profiles = await self._get_all_profiles()
        for p in profiles:
            if p.get("username", "").lower() == username.lower():
                return p
        return None

    # ── 1. Brand Profile ─────────────────────────────────────────────────

    async def create_brand_profile(self, brand_id: str) -> dict[str, Any]:
        """
        Register a brand as an Upload-Post user.
        Checks if the profile already exists first (avoids duplicates).
        """
        existing = await self._find_profile(brand_id)
        if existing:
            logger.info("Upload-Post profile already exists", brand_id=brand_id)
            return {"username": existing["username"], "already_exists": True}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{UPLOAD_POST_BASE}/uploadposts/users",
                headers=self._json_headers,
                json={"username": brand_id},
            )
            if response.status_code == 409:
                return {"username": brand_id, "already_exists": True}
            self._handle_error(response, "create_brand_profile")
            result = response.json()
            logger.info("Upload-Post user created", brand_id=brand_id)
            return result

    # ── 2. Social Link URL ───────────────────────────────────────────────

    async def get_social_link_url(
        self,
        brand_id: str,
        platforms: list[str] | None = None,
        logo_image: str = "https://presenceos.app/logo.png",
        connect_title: str = "Connecter mes reseaux",
        redirect_url: str | None = None,
    ) -> str:
        """
        Generate a branded JWT URL for connecting social accounts.
        Includes redirect_url so Upload-Post redirects after connection.
        Accepts optional redirect_url for mobile deep link callbacks.
        """
        if platforms is None:
            platforms = ["instagram", "facebook", "tiktok"]

        # Default to web URL, but allow mobile deep link override
        final_redirect = redirect_url or "https://presenceos.app/connected"

        payload = {
            "username": brand_id,
            "logo_image": logo_image,
            "platforms": platforms,
            "connect_title": connect_title,
            "redirect_url": final_redirect,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{UPLOAD_POST_BASE}/uploadposts/users/generate-jwt",
                headers=self._json_headers,
                json=payload,
            )
            self._handle_error(response, "get_social_link_url")
            result = response.json()
            access_url = result.get("access_url", "")
            logger.info(
                "Upload-Post JWT URL generated",
                brand_id=brand_id,
                url_length=len(access_url),
            )
            return access_url

    # ── 3. Publish Photo ─────────────────────────────────────────────────

    async def publish_photo(
        self,
        brand_id: str,
        image_url: str,
        caption: str,
        platforms: list[str],
        hashtags: list[str] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Publish a photo to connected platforms via multipart form.
        POST https://api.upload-post.com/api/upload
        """
        full_caption = caption
        if hashtags:
            full_caption += "\n\n" + " ".join(f"#{tag}" for tag in hashtags)

        # Upload-Post requires a non-empty title
        post_title = title or full_caption[:100].split("\n")[0] or "Post"

        logger.info(
            "Publishing photo via Upload-Post",
            brand_id=brand_id,
            platforms=platforms,
            caption_length=len(full_caption),
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Download image to send as file upload
            img_resp = await client.get(image_url)
            if img_resp.status_code != 200:
                raise UploadPostError(
                    f"Impossible de telecharger l'image: HTTP {img_resp.status_code}"
                )

            content_type = img_resp.headers.get("content-type", "image/jpeg")
            ext = "jpg"
            if "png" in content_type:
                ext = "png"
            elif "webp" in content_type:
                ext = "webp"

            # Upload-Post API: POST /upload_photos
            # Required fields: photos[] (file), user, platform[], title
            # Use single 'files' param to avoid httpx async/sync conflict
            multipart: list[tuple[str, Any]] = [
                ("photos[]", (f"post.{ext}", img_resp.content, content_type)),
                ("user", (None, brand_id)),
                ("title", (None, post_title)),
            ]
            for p in platforms:
                multipart.append(("platform[]", (None, p)))

            response = await client.post(
                f"{UPLOAD_POST_BASE}/upload_photos",
                headers=self._headers,
                files=multipart,
            )
            self._handle_error(response, "publish_photo")
            result = response.json()

            logger.info(
                "Upload-Post publish success",
                brand_id=brand_id,
                platforms=platforms,
            )

            return {
                "success": True,
                "post_id": result.get("id", ""),
                "post_url": result.get("postUrl"),
                "published_at": datetime.now(timezone.utc),
                "platform_response": result,
            }

    # ── 4. Connected Accounts ────────────────────────────────────────────

    async def get_connected_accounts(
        self, brand_id: str
    ) -> list[dict[str, Any]]:
        """
        List connected social accounts for a brand.

        Upload-Post API returns profiles with social_accounts as a dict:
        {"instagram": {"handle": "...", ...}, "tiktok": "", "facebook": {...}}

        Connected = value is a dict (not empty string).
        """
        profile = await self._find_profile(brand_id)
        if not profile:
            return []

        social = profile.get("social_accounts", {})
        accounts = []

        for platform, data in social.items():
            if isinstance(data, dict) and data:
                accounts.append({
                    "platform": platform,
                    "username": data.get("handle") or data.get("display_name") or "",
                    "display_name": data.get("display_name") or "",
                    "avatar_url": data.get("social_images") or "",
                    "connected": True,
                    "reauth_required": data.get("reauth_required", False),
                })
            else:
                accounts.append({
                    "platform": platform,
                    "connected": False,
                })

        logger.info(
            "Upload-Post accounts fetched",
            brand_id=brand_id,
            total=len(accounts),
            connected=sum(1 for a in accounts if a.get("connected")),
        )
        return accounts
