"""
PresenceOS - AI Video Service

AI video generation using fal.ai:
- Kling 2.6 Pro: text-to-video + image-to-video ($0.07/s without audio)
- Wan 2.6 Budget: text-to-video ($0.05/s)

All videos are persisted to S3 immediately (permanent URLs).
"""
import os
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import settings
from app.core.timeouts import get_http_timeout
from app.services.storage import get_storage_service

logger = structlog.get_logger()

# Model IDs
KLING_T2V = "fal-ai/kling-video/v2.6/pro/text-to-video"
KLING_I2V = "fal-ai/kling-video/v2.6/pro/image-to-video"
WAN_T2V = "fal-ai/wan/v2.2/t2v-14b"


class AIVideoService:
    """AI video generation with S3 persistence."""

    def __init__(self) -> None:
        self._fal_key = settings.fal_key
        if not self._fal_key:
            raise RuntimeError(
                "FAL_KEY not configured. Set FAL_KEY in environment."
            )

    async def text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        brand_id: str = "",
        model: str = "kling",
    ) -> dict:
        """Generate a video from text prompt.

        Args:
            prompt: Video description.
            duration: Duration in seconds (5 or 10).
            aspect_ratio: "9:16" (portrait), "16:9" (landscape), "1:1" (square).
            brand_id: Brand UUID for S3 path.
            model: "kling" (quality) or "wan" (budget).

        Returns:
            Dict with url, model, duration, aspect_ratio, persisted, generated_at.
        """
        os.environ["FAL_KEY"] = self._fal_key
        import fal_client

        model_id = WAN_T2V if model == "wan" else KLING_T2V

        logger.info(
            "Generating text-to-video",
            model=model_id,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )

        result = await fal_client.subscribe_async(
            model_id,
            arguments={
                "prompt": prompt,
                "duration": str(duration),
                "aspect_ratio": aspect_ratio,
            },
        )

        video_url = result.get("video", {}).get("url") if isinstance(result, dict) else None
        if not video_url:
            raise ValueError("fal.ai returned no video URL")

        # Persist to S3 (fal.ai URLs expire in 24-48h)
        s3_url = await self._persist_video(video_url, brand_id, model, duration)

        return {
            "url": s3_url,
            "model": model_id,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "persisted": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        aspect_ratio: str = "9:16",
        brand_id: str = "",
    ) -> dict:
        """Animate a static image into a video.

        Args:
            image_url: URL of the source image.
            prompt: Optional motion description.
            duration: Duration in seconds (5 or 10).
            aspect_ratio: Video aspect ratio.
            brand_id: Brand UUID for S3 path.

        Returns:
            Dict with url, model, duration, aspect_ratio, persisted, generated_at.
        """
        os.environ["FAL_KEY"] = self._fal_key
        import fal_client

        logger.info(
            "Generating image-to-video",
            model=KLING_I2V,
            duration=duration,
        )

        arguments: dict = {
            "image_url": image_url,
            "duration": str(duration),
            "aspect_ratio": aspect_ratio,
        }
        if prompt:
            arguments["prompt"] = prompt

        result = await fal_client.subscribe_async(
            KLING_I2V,
            arguments=arguments,
        )

        video_url = result.get("video", {}).get("url") if isinstance(result, dict) else None
        if not video_url:
            raise ValueError("fal.ai returned no video URL")

        s3_url = await self._persist_video(video_url, brand_id, "kling-i2v", duration)

        return {
            "url": s3_url,
            "model": KLING_I2V,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "persisted": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    async def _persist_video(
        fal_url: str, brand_id: str, model: str, duration: int,
    ) -> str:
        """Download video from fal.ai and persist to S3."""
        storage = get_storage_service()

        async with httpx.AsyncClient(timeout=get_http_timeout("video_download")) as client:
            resp = await client.get(fal_url)
            resp.raise_for_status()
            video_bytes = resp.content

        key = storage.generate_key(
            brand_id=brand_id or "ai-studio",
            media_type="video",
            original_filename=f"{model}_{duration}s_{uuid.uuid4().hex[:8]}.mp4",
        )
        result = await storage.upload_bytes(
            data=video_bytes, key=key, content_type="video/mp4",
        )
        logger.info("Video persisted to S3", key=key, size=len(video_bytes))
        return result["url"]
