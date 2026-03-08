"""
BreakoutEngine V3 — photo -> rembg -> Remotion template -> MP4

Pipeline :
  1. Recevoir une image (upload ou URL)
  2. rembg -> PNG sans fond (3-5s, CPU)
  3. Upload des 2 images sur fal.ai storage
  4. Appel HTTP au service Remotion (Express) avec retry sur 503 (warming)
  5. Remotion rend le MP4 (~25-60s)
  6. Retourner l'URL du MP4

Temps cible : 45-90s. Cout : 0 EUR.
"""

import asyncio
import base64
import io
import os
import tempfile
from pathlib import Path

import httpx
import structlog
from PIL import Image, ImageFilter

from app.core.config import settings

logger = structlog.get_logger()

# Retry config for Remotion warming (503)
RENDER_TIMEOUT = 150  # 2min30 — above render max (120s) + margin
WARMING_RETRY_MAX = 6
WARMING_RETRY_DELAY = 30  # seconds


class BreakoutEngine:
    """Pipeline Breakout V3 : image -> rembg -> Remotion -> MP4"""

    async def generate(
        self,
        image_url: str,
        business_name: str = "Mon Restaurant",
        likes_count: int = 1200,
        instagram_handle: str = "@monrestaurant",
        accent_color: str = "#F59E0B",
    ) -> dict:
        logger.info("breakout.v3.start", image_url=image_url[:80])

        # Step 1 : Download original
        original_bytes = await self._download_image(image_url)

        # Step 2 : rembg background removal (CPU, ~3-5s)
        logger.info("breakout.rembg_start")
        cutout_bytes = await asyncio.to_thread(self._remove_background, original_bytes)
        logger.info("breakout.rembg_done")

        # Step 3 : Upload both to fal.ai storage (public URLs, 7 day TTL)
        original_url, cutout_url = await asyncio.gather(
            asyncio.to_thread(self._upload_to_fal, original_bytes, "original.jpg"),
            asyncio.to_thread(self._upload_to_fal, cutout_bytes, "cutout.png"),
        )
        logger.info("breakout.uploads_done", original_url=original_url[:60])

        # Step 4 : Call Remotion render service (with retry on 503 warming)
        logger.info("breakout.remotion_start")
        video_bytes = await self._call_remotion(
            original_photo_url=original_url,
            cutout_url=cutout_url,
            business_name=business_name,
            likes_count=likes_count,
            instagram_handle=instagram_handle,
            accent_color=accent_color,
        )

        # Step 5 : Upload final video to fal.ai storage
        video_url = await asyncio.to_thread(
            self._upload_to_fal, video_bytes, "breakout.mp4"
        )
        logger.info("breakout.v3.done", video_url=video_url[:60])

        return {
            "video_url": video_url,
            "duration_seconds": 3,
            "original_url": original_url,
            "cutout_url": cutout_url,
        }

    def _remove_background(self, image_bytes: bytes) -> bytes:
        """rembg CPU — remove background, return PNG with alpha."""
        from rembg import remove as rembg_remove

        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        output_image = rembg_remove(input_image)

        # Light feathering for cleaner edges
        alpha = output_image.split()[3]
        smoothed_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1))
        output_image.putalpha(smoothed_alpha)

        buf = io.BytesIO()
        output_image.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def _download_image(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.content

    def _upload_to_fal(self, data: bytes, filename: str) -> str:
        """Upload bytes to fal.ai storage -> public URL (7 day TTL)."""
        import fal_client

        fal_key = settings.fal_key
        if fal_key:
            os.environ["FAL_KEY"] = fal_key

        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(data)
            tmp_path = f.name
        try:
            return fal_client.upload_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    async def _call_remotion(
        self,
        original_photo_url: str,
        cutout_url: str,
        business_name: str,
        likes_count: int,
        instagram_handle: str,
        accent_color: str,
    ) -> bytes:
        """
        HTTP call to Remotion Express server -> returns MP4 bytes.

        Handles:
        - 503 warming -> retry up to WARMING_RETRY_MAX times
        - Timeout -> retry once then raise
        - Response is base64-encoded video
        """
        remotion_url = settings.remotion_service_url
        payload = {
            "originalPhotoUrl": original_photo_url,
            "cutoutUrl": cutout_url,
            "businessName": business_name,
            "likesCount": likes_count,
            "instagramHandle": instagram_handle,
            "accentColor": accent_color,
        }

        for attempt in range(WARMING_RETRY_MAX):
            try:
                async with httpx.AsyncClient(timeout=RENDER_TIMEOUT) as client:
                    response = await client.post(
                        f"{remotion_url}/render/breakout",
                        json=payload,
                    )

                if response.status_code == 503:
                    logger.info(
                        "breakout.remotion_warming",
                        attempt=attempt + 1,
                        max_retries=WARMING_RETRY_MAX,
                    )
                    await asyncio.sleep(WARMING_RETRY_DELAY)
                    continue

                if response.status_code != 200:
                    error_detail = response.text[:500]
                    raise RuntimeError(
                        f"Remotion returned {response.status_code}: {error_detail}"
                    )

                data = response.json()
                video_b64 = data.get("video_base64")
                if not video_b64:
                    raise RuntimeError("No video_base64 in Remotion response")

                return base64.b64decode(video_b64)

            except httpx.TimeoutException:
                if attempt < WARMING_RETRY_MAX - 1:
                    logger.warning(
                        "breakout.remotion_timeout",
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(5)
                    continue
                raise RuntimeError(
                    f"Remotion render timed out after {RENDER_TIMEOUT}s "
                    f"(tried {WARMING_RETRY_MAX} times)"
                )

        raise RuntimeError("Remotion unavailable after max retries")
