"""
PresenceOS - ImageStudio Service
Brain-aware image generation using GPT-Image-1 (gpt-image-1).
Bug Fix #2: ImageStudio calls VisualBrain to optimize prompts.
VisualBrain NEVER generates images.
"""
import uuid
from datetime import datetime, timezone

import httpx
import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.visual_brain import VisualBrain
from app.services.storage import get_storage_service

logger = structlog.get_logger()

# Style modifiers (same keys as PhotoStudio for consistency)
STYLE_MODIFIERS = {
    "natural": "natural soft window lighting, authentic, warm atmosphere, shallow depth of field",
    "cinematic": "dramatic cinematic lighting, film-like color grading, teal and orange tones, professional",
    "vibrant": "vibrant saturated colors, high contrast, energetic, social media optimized, scroll-stopping",
    "minimalist": "clean minimalist composition, negative space, soft neutral background, elegant",
}


class ImageStudio:
    """Brain-aware image generation service."""

    def __init__(self, brand_id: uuid.UUID, db: AsyncSession):
        self.brand_id = brand_id
        self.db = db
        self.vb = VisualBrain(brand_id, db)

    async def generate(
        self,
        prompt: str,
        template_key: str = "general",
        style: str = "natural",
        size: str = "1024x1024",
        niche: str = "restaurant",
        brand_name: str | None = None,
        use_brain: bool = True,
    ) -> dict:
        """Generate an image with optional VisualBrain optimization.

        Bug Fix #2: ImageStudio calls VisualBrain, never the reverse.
        """
        if not settings.openai_api_key:
            return {"image_url": None, "error": "No OpenAI API key configured", "brain_optimized": False}

        # Step 1: Optionally optimize prompt via VisualBrain
        final_prompt = prompt
        brain_optimized = False
        if use_brain:
            try:
                optimized = await self.vb.reoptimize_prompt(template_key, prompt)
                if optimized and optimized != prompt:
                    final_prompt = optimized
                    brain_optimized = True
            except Exception as e:
                logger.warning("VisualBrain optimization failed, using original prompt", error=str(e))

        # Step 2: Enhance prompt with style and niche context
        style_mod = STYLE_MODIFIERS.get(style, STYLE_MODIFIERS["natural"])
        enhanced = (
            f"A professional marketing photograph: {final_prompt}. "
            f"Style: {style_mod}. "
            f"Niche: {niche}. "
            f"Ultra high quality, commercially viable, suitable for Instagram. "
            f"NO text, NO watermarks, NO logos, NO letters."
        )
        if brand_name:
            enhanced += f" For brand '{brand_name}'."

        # Step 3: Generate image via GPT-Image-1
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        try:
            response = await client.images.generate(
                model="gpt-image-1",
                prompt=enhanced,
                size=size,
                quality="high",
                n=1,
            )
            image_url = response.data[0].url

            # Persist to S3
            permanent_url = await self._persist_image(image_url, niche, style)

            # Step 4: Record in VisualBrain memory (Bug Fix #2: ImageStudio stores, VisualBrain remembers)
            await self.vb.remember_visual_performance(
                template_key=template_key,
                prompt_used=enhanced,
                image_url=permanent_url,
                style_tags=[style, niche],
            )

            return {
                "image_url": permanent_url,
                "prompt_used": enhanced,
                "original_prompt": prompt,
                "brain_optimized": brain_optimized,
                "style": style,
                "niche": niche,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.error("Image generation failed", error=str(exc))
            return {"image_url": None, "error": str(exc), "brain_optimized": brain_optimized}

    async def _persist_image(self, dalle_url: str, niche: str, style: str) -> str:
        """Download and persist image to S3."""
        storage = get_storage_service()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(dalle_url)
                resp.raise_for_status()
                image_bytes = resp.content

            key = storage.generate_key(
                brand_id=str(self.brand_id),
                media_type="image",
                original_filename=f"gpt_image_{niche}_{style}.png",
            )
            result = await storage.upload_bytes(data=image_bytes, key=key, content_type="image/png")
            return result["url"]
        except Exception as exc:
            logger.warning("Failed to persist image, using ephemeral URL", error=str(exc))
            return dalle_url

    async def generate_for_post(
        self,
        topic: str,
        platform: str = "instagram",
        niche: str = "restaurant",
        brand_name: str | None = None,
    ) -> dict:
        """Generate an image specifically for a social media post."""
        size_map = {
            "instagram": "1024x1024",
            "facebook": "1792x1024",
            "tiktok": "1024x1792",
            "linkedin": "1792x1024",
        }
        size = size_map.get(platform, "1024x1024")
        return await self.generate(
            prompt=topic,
            template_key=f"post_{platform}",
            style="vibrant" if platform in ("instagram", "tiktok") else "natural",
            size=size,
            niche=niche,
            brand_name=brand_name,
        )
