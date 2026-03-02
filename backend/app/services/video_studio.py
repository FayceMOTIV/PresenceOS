"""
PresenceOS - VideoStudio Service
Video generation using fal.ai Kling 3.0.
Brain-aware: uses VisualBrain for prompt optimization.
"""
import os
import uuid
from datetime import datetime, timezone

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

            # Model mapping: pro for 5s/10s, master for 15s
            if duration >= 15:
                model_id = "fal-ai/kling-video/v2.1/master/text-to-video"
            else:
                model_id = "fal-ai/kling-video/v2.1/pro/text-to-video"

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
