"""
CinematicFoodService — Photo -> cinematic video via Kling 2.6 Pro (fal.ai)

Pipeline:
  1. Receive image URL (S3 or public)
  2. Generate cinematic food prompt based on food_type
  3. Kling 2.6 Pro image-to-video via fal_client.subscribe_async()
  4. Persist video to S3 (permanent URL)
  5. Return video URL + metadata

Cost: $0.07/s x 5s = $0.35 per video (no audio)
Model: fal-ai/kling-video/v2.6/pro/image-to-video
"""

import os
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import settings
from app.services.storage import get_storage_service

logger = structlog.get_logger()

KLING_I2V = "fal-ai/kling-video/v2.6/pro/image-to-video"

CINEMATIC_FOOD_PROMPTS: dict[str, str] = {
    "default": (
        "Cinematic slow motion food video, professional studio lighting, "
        "shallow depth of field, steam rising gently, "
        "appetizing macro close-up, warm golden tones, "
        "restaurant advertisement quality, 4K"
    ),
    "burger": (
        "Cinematic burger video, melted cheese stretching slowly, "
        "warm studio lighting, macro close-up, shallow depth of field, "
        "sizzling atmosphere, golden tones, 4K advertisement"
    ),
    "pizza": (
        "Cinematic pizza video, cheese pull in slow motion, "
        "wood fire oven glow, crispy crust texture macro, "
        "Italian restaurant atmosphere, warm lighting, 4K"
    ),
    "dessert": (
        "Cinematic dessert video, chocolate drizzle in slow motion, "
        "powdered sugar falling gently, macro close-up texture, "
        "soft studio lighting, pastel tones, luxury patisserie style, 4K"
    ),
    "drink": (
        "Cinematic drink video, condensation drops on glass, "
        "liquid pouring in slow motion, ice cubes clinking, "
        "bar atmosphere lighting, macro close-up, 4K advertisement"
    ),
}

VALID_FOOD_TYPES = frozenset(CINEMATIC_FOOD_PROMPTS.keys())


class CinematicFoodService:
    """Photo -> cinematic food video via Kling 2.6 Pro."""

    def __init__(self) -> None:
        self._fal_key = settings.fal_key
        if not self._fal_key:
            raise RuntimeError(
                "FAL_KEY not configured. Set FAL_KEY in environment."
            )

    async def generate(
        self,
        image_url: str,
        brand_id: str = "",
        food_type: str = "default",
        duration: int = 5,
        aspect_ratio: str = "9:16",
    ) -> dict:
        """Generate a cinematic food video from a static image.

        Args:
            image_url: Public URL of the source food photo.
            brand_id: Brand UUID for S3 path.
            food_type: "default" | "burger" | "pizza" | "dessert" | "drink"
            duration: 5 ($0.35) or 10 ($0.70) seconds.
            aspect_ratio: "9:16" (portrait), "1:1" (square), "16:9" (landscape).

        Returns:
            Dict with video_url, cost_usd, duration, food_type, model, generated_at.
        """
        os.environ["FAL_KEY"] = self._fal_key
        import fal_client

        prompt = CINEMATIC_FOOD_PROMPTS.get(food_type, CINEMATIC_FOOD_PROMPTS["default"])

        logger.info(
            "cinematic_food.start",
            food_type=food_type,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )

        arguments: dict = {
            "image_url": image_url,
            "prompt": prompt,
            "duration": str(duration),
            "aspect_ratio": aspect_ratio,
        }

        result = await fal_client.subscribe_async(
            KLING_I2V,
            arguments=arguments,
        )

        video_url_fal = (
            result.get("video", {}).get("url")
            if isinstance(result, dict)
            else None
        )
        if not video_url_fal:
            raise ValueError(
                f"fal.ai returned no video URL for cinematic food ({food_type})"
            )

        # Persist to S3 (fal.ai URLs expire in 24-48h)
        s3_url = await self._persist_video(video_url_fal, brand_id, food_type, duration)

        cost_usd = round(0.07 * duration, 2)

        logger.info(
            "cinematic_food.done",
            food_type=food_type,
            cost_usd=cost_usd,
        )

        return {
            "video_url": s3_url,
            "cost_usd": cost_usd,
            "duration": duration,
            "food_type": food_type,
            "aspect_ratio": aspect_ratio,
            "model": KLING_I2V,
            "persisted": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    async def _persist_video(
        fal_url: str, brand_id: str, food_type: str, duration: int,
    ) -> str:
        """Download video from fal.ai and persist to S3."""
        storage = get_storage_service()

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(fal_url)
            resp.raise_for_status()
            video_bytes = resp.content

        key = storage.generate_key(
            brand_id=brand_id or "ai-studio",
            media_type="video",
            original_filename=f"cinematic_{food_type}_{duration}s_{uuid.uuid4().hex[:8]}.mp4",
        )
        result = await storage.upload_bytes(
            data=video_bytes, key=key, content_type="video/mp4",
        )
        logger.info("cinematic_food.persisted", key=key, size=len(video_bytes))
        return result["url"]
