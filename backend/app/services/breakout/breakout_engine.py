"""
BreakoutEngine V3 — photo -> rembg -> Remotion template -> MP4

Pipeline :
  1. Recevoir une image (upload ou URL)
  2. rembg -> PNG sans fond (3-5s, CPU)
  3. Upload des 2 images sur fal.ai storage
  4. Appel HTTP au service Remotion (Express)
  5. Remotion rend le MP4 (~25s)
  6. Retourner l'URL du MP4

Temps cible : 35-40s. Cout : 0 EUR.
"""

import asyncio
import io
import os
import tempfile
from pathlib import Path

import httpx
import structlog
from PIL import Image, ImageFilter

logger = structlog.get_logger()

REMOTION_URL = os.getenv("REMOTION_SERVICE_URL", "http://localhost:3001")


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

        # Step 4 : Call Remotion render service
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

        from app.core.config import settings

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
        """HTTP call to Remotion Express server -> returns MP4 bytes."""
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{REMOTION_URL}/render/breakout",
                json={
                    "originalPhotoUrl": original_photo_url,
                    "cutoutUrl": cutout_url,
                    "businessName": business_name,
                    "likesCount": likes_count,
                    "instagramHandle": instagram_handle,
                    "accentColor": accent_color,
                },
            )
            r.raise_for_status()
            return r.content
