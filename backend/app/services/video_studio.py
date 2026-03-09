"""
PresenceOS - VideoStudio Service
Video generation using fal.ai Kling 3.0.
Brain-aware: uses VisualBrain for prompt optimization.
"""
import os
import uuid
from datetime import datetime, timezone

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.visual_brain import VisualBrain

logger = structlog.get_logger()

STYLE_MODIFIERS = {
    "cinematic": "cinematic lighting, shallow depth of field, film grain, warm tones, professional",
    "natural": "natural daylight, authentic, candid atmosphere, soft shadows, realistic",
    "vibrant": "vibrant saturated colors, high contrast, energetic, social media optimized",
}


class VideoStudio:
    """Brain-aware video generation service."""

    def __init__(self, brand_id: uuid.UUID, db: AsyncSession):
        self.brand_id = brand_id
        self.db = db
        self.vb = VisualBrain(brand_id, db)

    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        style: str = "cinematic",
        aspect_ratio: str = "9:16",
        use_brain: bool = True,
    ) -> dict:
        """Generate a video with optional VisualBrain optimization."""
        fal_key = settings.fal_key
        if not fal_key:
            return {"video_url": None, "error": "FAL_KEY not configured", "brain_optimized": False}

        # Optionally optimize prompt
        final_prompt = prompt
        brain_optimized = False
        if use_brain:
            try:
                optimized = await self.vb.reoptimize_prompt("video", prompt)
                if optimized and optimized != prompt:
                    final_prompt = optimized
                    brain_optimized = True
            except Exception as e:
                logger.warning("VisualBrain video optimization failed", error=str(e))

        # Enhance with style
        style_mod = STYLE_MODIFIERS.get(style, STYLE_MODIFIERS["cinematic"])
        enhanced = f"{final_prompt}. {style_mod}"

        # Call fal.ai
        try:
            os.environ["FAL_KEY"] = fal_key
            import fal_client

            # Kling 2.6 Pro for all durations (master variant removed by fal.ai)
            model_id = "fal-ai/kling-video/v2.6/pro/text-to-video"

            result = await fal_client.subscribe_async(
                model_id,
                arguments={
                    "prompt": enhanced,
                    "duration": str(duration),
                    "aspect_ratio": aspect_ratio,
                },
            )

            video_url = result.get("video", {}).get("url") if isinstance(result, dict) else None

            if video_url:
                # Persist to S3 (fal.ai URLs expire in 24-48h)
                video_url = await self._persist_video(video_url, style, duration)

                # Record in VisualBrain
                await self.vb.remember_visual_performance(
                    template_key="video",
                    prompt_used=enhanced,
                    image_url=video_url,
                    style_tags=[style, "video", f"{duration}s"],
                )

            return {
                "video_url": video_url,
                "prompt_used": enhanced,
                "brain_optimized": brain_optimized,
                "duration": duration,
                "style": style,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.error("Video generation failed", error=str(exc))
            return {"video_url": None, "error": str(exc), "brain_optimized": brain_optimized}

    async def _persist_video(self, fal_url: str, style: str, duration: int) -> str:
        """Download a fal.ai video and persist to S3.

        Returns the permanent S3 URL, or the original URL as fallback.
        """
        try:
            from app.services.storage import get_storage_service
            storage = get_storage_service()
            if not storage:
                return fal_url

            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.get(fal_url)
                resp.raise_for_status()
                video_bytes = resp.content

            key = storage.generate_key(
                brand_id=str(self.brand_id),
                media_type="video",
                original_filename=f"kling_{style}_{duration}s.mp4",
            )
            result = await storage.upload_bytes(
                video_bytes, key, content_type="video/mp4"
            )
            logger.info("Video persisted to S3", key=key, size=len(video_bytes))
            return result["url"]
        except Exception as exc:
            logger.warning("Failed to persist video, using ephemeral URL", error=str(exc))
            return fal_url
