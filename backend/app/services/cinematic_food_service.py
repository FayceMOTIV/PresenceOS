"""
CinematicFoodService — Photo -> cinematic video via Kling 2.6 Pro (fal.ai)

Pipeline I2V (existing):
  1. Receive image URL (S3 or public)
  2. Generate cinematic food prompt based on food_type
  3. Kling 2.6 Pro image-to-video via fal_client.subscribe_async()
  4. Persist video to S3 (permanent URL)
  5. Return video URL + metadata

Pipeline T2V (RS3 — 3 clips):
  1. Receive dish name + optional brand context
  2. Generate 3 angle prompts (close-up, overhead, side)
  3. Kling 2.6 Pro text-to-video x3 in parallel via asyncio.gather()
  4. Assemble 3 clips via video_assembly_service
  5. Return assembled video URL + metadata

Cost I2V: $0.07/s x 5s = $0.35 per video (no audio)
Cost T2V: ~$0.117/clip x 3 = ~$0.35 per video (3x5s)
Models: fal-ai/kling-video/v2.6/pro/image-to-video (I2V)
        fal-ai/kling-video/v2.6/pro/text-to-video (T2V)
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import settings
from app.core.observability import capture_exception
from app.core.timeouts import TIMEOUT_VIDEO, get_http_timeout
from app.services.storage import get_storage_service

logger = structlog.get_logger()

KLING_I2V = "fal-ai/kling-video/v2.6/pro/image-to-video"
KLING_T2V = "fal-ai/kling-video/v2.6/pro/text-to-video"

# Cost per second for Kling 2.6 Pro via fal.ai
_COST_PER_SECOND = 0.07
_T2V_CLIP_DURATION = 5
_T2V_CLIP_COUNT = 3

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

        async with httpx.AsyncClient(timeout=get_http_timeout("video_download")) as client:
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

    # ── T2V: 3-clip cinematic food video ────────────────────────────────

    async def generate_text_to_video(
        self,
        dish_name: str,
        brand_id: str = "",
        aspect_ratio: str = "9:16",
        brand_context: str = "",
    ) -> dict:
        """Generate a 3-clip cinematic food video from a dish name (T2V).

        Generates 3 clips in parallel (close-up, overhead, side angle),
        then assembles them into a single 15s video via FFmpeg + S3.

        Args:
            dish_name: Name of the dish (e.g. "Truffle Risotto").
            brand_id: Brand UUID for S3 path.
            aspect_ratio: "9:16" | "16:9" | "1:1".
            brand_context: Optional brand personality/style context from Mem0.

        Returns:
            Dict with success, video_url, clips, clips_count, cost_usd.
        """
        os.environ["FAL_KEY"] = self._fal_key
        import fal_client

        # Build 3 angle prompts
        context_suffix = f" {brand_context}" if brand_context else ""
        prompts = [
            (
                f"Close-up macro shot of {dish_name}, steam rising gently, "
                f"beautiful bokeh background, shallow depth of field, "
                f"warm golden lighting, appetizing food photography, 4K.{context_suffix}"
            ),
            (
                f"Overhead flat lay shot of {dish_name}, elegant plating on dark surface, "
                f"garnishes artfully placed, soft studio lighting, "
                f"high-end restaurant presentation, 4K.{context_suffix}"
            ),
            (
                f"Side angle shot of {dish_name}, chef hands in background, "
                f"restaurant kitchen ambiance, soft warm lighting, "
                f"cinematic shallow depth of field, 4K.{context_suffix}"
            ),
        ]

        logger.info(
            "cinematic_food.t2v_start",
            dish_name=dish_name,
            clips=_T2V_CLIP_COUNT,
            aspect_ratio=aspect_ratio,
        )

        # Generate 3 clips in parallel
        async def _generate_single_clip(prompt: str, clip_idx: int) -> dict | None:
            """Generate one T2V clip. Returns result dict or None on failure."""
            try:
                result = await asyncio.wait_for(
                    fal_client.subscribe_async(
                        KLING_T2V,
                        arguments={
                            "prompt": prompt,
                            "duration": str(_T2V_CLIP_DURATION),
                            "aspect_ratio": aspect_ratio,
                        },
                    ),
                    timeout=TIMEOUT_VIDEO,
                )
                video_url = (
                    result.get("video", {}).get("url")
                    if isinstance(result, dict)
                    else None
                )
                if video_url:
                    logger.info("cinematic_food.t2v_clip_done", clip=clip_idx)
                    return {"url": video_url, "clip_idx": clip_idx}
                else:
                    logger.warning("cinematic_food.t2v_clip_no_url", clip=clip_idx)
                    return None
            except asyncio.TimeoutError:
                logger.error("cinematic_food.t2v_clip_timeout", clip=clip_idx)
                return None
            except Exception as exc:
                logger.error(
                    "cinematic_food.t2v_clip_failed",
                    clip=clip_idx,
                    error=str(exc),
                )
                capture_exception(exc, {"context": f"cinematic_t2v_clip_{clip_idx}"})
                return None

        clip_results = await asyncio.gather(
            *[
                _generate_single_clip(prompt, idx)
                for idx, prompt in enumerate(prompts)
            ]
        )

        # Filter successful clips (preserve order)
        successful_clips = [c for c in clip_results if c is not None]
        clip_urls = [c["url"] for c in successful_clips]

        if not clip_urls:
            logger.error("cinematic_food.t2v_all_clips_failed", dish_name=dish_name)
            return {
                "success": False,
                "video_url": None,
                "clips": [],
                "clips_count": 0,
                "cost_usd": 0.0,
            }

        # Assemble clips via video_assembly_service
        from app.services.video_assembly_service import assemble_clips

        assembled_url = await assemble_clips(
            clip_urls=clip_urls,
            brand_id=brand_id,
            label=f"cinematic_{dish_name.replace(' ', '_')[:30]}",
        )

        cost_usd = round(_COST_PER_SECOND * _T2V_CLIP_DURATION * len(clip_urls), 2)

        logger.info(
            "cinematic_food.t2v_done",
            dish_name=dish_name,
            clips_generated=len(clip_urls),
            assembled=assembled_url is not None,
            cost_usd=cost_usd,
        )

        return {
            "success": True,
            "video_url": assembled_url,
            "clips": clip_urls,
            "clips_count": len(clip_urls),
            "cost_usd": cost_usd,
        }
