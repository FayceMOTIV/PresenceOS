"""
BreakoutEngine V4 — "Subject breaks out of Instagram frame" (Tim Gray style)

Upgrade from V3:
- New Remotion composition: BreakoutV4 (3 layers, spring animations)
- Persists final video to S3 (permanent URL, not fal.ai 7-day TTL)
- Separate prepare/render steps for mobile preview

Pipeline:
  1. Download image
  2. rembg -> cutout PNG (reuses V3 _remove_background)
  3. Upload both to fal.ai storage (public URLs for Remotion)
  4. Remotion renders BreakoutV4 composition -> MP4 bytes
  5. Persist MP4 to S3 -> permanent URL

Cost: $0.00 (rembg local + Remotion self-hosted)
"""

import asyncio
import uuid

import structlog

from app.services.breakout.breakout_engine import BreakoutEngine
from app.services.storage import get_storage_service

logger = structlog.get_logger()


class BreakoutV4Engine(BreakoutEngine):
    """Breakout V4 — extends V3 with new composition + S3 persistence."""

    async def prepare(
        self,
        image_url: str,
        brand_id: str = "",
    ) -> dict:
        """Step 1: Download + rembg -> return asset URLs for preview.

        Returns:
            {
                "original_url": str,  # fal.ai public URL
                "cutout_url": str,    # fal.ai public URL (PNG transparent)
            }
        """
        logger.info("breakout.v4.prepare_start", image_url=image_url[:80])

        original_bytes = await self._download_image(image_url)

        cutout_bytes = await asyncio.to_thread(
            self._remove_background, original_bytes
        )

        original_url, cutout_url = await asyncio.gather(
            asyncio.to_thread(self._upload_to_fal, original_bytes, "original.jpg"),
            asyncio.to_thread(self._upload_to_fal, cutout_bytes, "cutout.png"),
        )

        logger.info("breakout.v4.prepare_done")
        return {
            "original_url": original_url,
            "cutout_url": cutout_url,
        }

    async def render(
        self,
        original_url: str,
        cutout_url: str,
        brand_id: str = "",
        business_name: str = "Mon Restaurant",
        instagram_handle: str = "@monrestaurant",
        caption: str = "",
        accent_color: str = "#F59E0B",
    ) -> dict:
        """Step 2: Remotion render BreakoutV4 -> persist to S3.

        Returns:
            {
                "video_url": str,      # S3 permanent URL
                "duration_seconds": 3,
                "original_url": str,
                "cutout_url": str,
            }
        """
        logger.info("breakout.v4.render_start")

        video_bytes = await self._call_remotion_v4(
            original_url=original_url,
            cutout_url=cutout_url,
            business_name=business_name,
            instagram_handle=instagram_handle,
            caption=caption,
            accent_color=accent_color,
        )

        # Persist to S3 (permanent URL, unlike fal.ai 7-day TTL)
        video_url = await self._persist_to_s3(video_bytes, brand_id)

        logger.info("breakout.v4.render_done", video_url=video_url[:60])
        return {
            "video_url": video_url,
            "duration_seconds": 3,
            "original_url": original_url,
            "cutout_url": cutout_url,
        }

    async def generate_v4(
        self,
        image_url: str,
        brand_id: str = "",
        business_name: str = "Mon Restaurant",
        instagram_handle: str = "@monrestaurant",
        caption: str = "",
        accent_color: str = "#F59E0B",
    ) -> dict:
        """Full pipeline: prepare + render in one call."""
        assets = await self.prepare(image_url, brand_id)
        return await self.render(
            original_url=assets["original_url"],
            cutout_url=assets["cutout_url"],
            brand_id=brand_id,
            business_name=business_name,
            instagram_handle=instagram_handle,
            caption=caption,
            accent_color=accent_color,
        )

    async def _call_remotion_v4(
        self,
        original_url: str,
        cutout_url: str,
        business_name: str,
        instagram_handle: str,
        caption: str,
        accent_color: str,
    ) -> bytes:
        """Call Remotion with BreakoutV4 composition.

        Falls back to V3 /render/breakout if /render/breakout-v4 is not deployed yet.
        """
        import base64

        import httpx

        from app.core.config import settings

        remotion_url = settings.remotion_service_url
        payload = {
            "originalPhotoUrl": original_url,
            "cutoutUrl": cutout_url,
            "businessName": business_name,
            "instagramHandle": instagram_handle,
            "caption": caption,
            "accentColor": accent_color,
        }

        # Try V4 endpoint first, fallback to V3
        for endpoint in ("/render/breakout-v4", "/render/breakout"):
            try:
                async with httpx.AsyncClient(timeout=150) as client:
                    response = await client.post(
                        f"{remotion_url}{endpoint}",
                        json=payload,
                    )

                if response.status_code == 404 and endpoint == "/render/breakout-v4":
                    logger.info("breakout.v4.fallback_to_v3")
                    continue

                if response.status_code == 503:
                    # Remotion warming — retry via parent V3 logic
                    return await self._call_remotion(
                        original_photo_url=original_url,
                        cutout_url=cutout_url,
                        business_name=business_name,
                        likes_count=1200,
                        instagram_handle=instagram_handle,
                        accent_color=accent_color,
                    )

                if response.status_code != 200:
                    raise RuntimeError(
                        f"Remotion returned {response.status_code}: "
                        f"{response.text[:300]}"
                    )

                data = response.json()
                video_b64 = data.get("video_base64")
                if not video_b64:
                    raise RuntimeError("No video_base64 in Remotion response")

                return base64.b64decode(video_b64)

            except httpx.TimeoutException:
                if endpoint == "/render/breakout-v4":
                    continue
                raise RuntimeError("Remotion render timed out")

        raise RuntimeError("Remotion unavailable for breakout-v4")

    @staticmethod
    async def _persist_to_s3(video_bytes: bytes, brand_id: str) -> str:
        """Upload video to S3, return permanent URL."""
        storage = get_storage_service()
        key = storage.generate_key(
            brand_id=brand_id or "ai-studio",
            media_type="video",
            original_filename=f"breakout-v4_{uuid.uuid4().hex[:8]}.mp4",
        )
        result = await storage.upload_bytes(
            data=video_bytes, key=key, content_type="video/mp4",
        )
        logger.info("breakout.v4.persisted", key=key, size=len(video_bytes))
        return result["url"]
