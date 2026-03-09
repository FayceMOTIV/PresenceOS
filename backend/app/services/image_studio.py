"""
PresenceOS - ImageStudio Service
Brain-aware image generation using Gemini Image.
Bug Fix #2: ImageStudio calls VisualBrain to optimize prompts.
VisualBrain NEVER generates images.

Migration: GPT-Image-1 → Gemini Image (March 2026)
"""
import asyncio
import base64
import uuid
from datetime import datetime, timezone

import structlog
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
        api_key = settings.google_api_key or settings.gemini_api_key
        if not api_key:
            return {"image_url": None, "error": "No Google API key configured", "brain_optimized": False}

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

        # Step 3: Generate image via Gemini Image
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-image")
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(
                    contents=enhanced,
                    generation_config=genai.GenerationConfig(response_modalities=["IMAGE"]),
                ),
            )

            image_bytes = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    raw = part.inline_data.data
                    image_bytes = base64.b64decode(raw) if isinstance(raw, str) else raw
                    break

            if not image_bytes:
                return {"image_url": None, "error": "Gemini returned no image", "brain_optimized": brain_optimized}

            # Persist to S3
            permanent_url = await self._persist_image_bytes(image_bytes, niche, style)

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

    async def _persist_image_bytes(self, image_bytes: bytes, niche: str, style: str) -> str:
        """Persist image bytes to S3. Returns permanent URL."""
        storage = get_storage_service()
        key = storage.generate_key(
            brand_id=str(self.brand_id),
            media_type="image",
            original_filename=f"gemini_{niche}_{style}_{uuid.uuid4().hex[:8]}.png",
        )
        result = await storage.upload_bytes(data=image_bytes, key=key, content_type="image/png")
        logger.info("Image persisted to S3", key=key, size=len(image_bytes))
        return result["url"]

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
