"""
PresenceOS - ImageService (Gemini Image Generation)

Replaces DALL-E 3 / GPT Image 1 with Gemini Image models.
All images are persisted to S3 immediately (permanent URLs).

Models:
- gemini-2.0-flash-preview-image-generation  (fast, ~$0.02/img)
- gemini-2.5-pro-preview-06-05              (pro quality, ~$0.067/img)
"""
import asyncio
import base64
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import settings
from app.services.storage import get_storage_service

logger = structlog.get_logger()

MODEL_FAST = "gemini-2.0-flash-preview-image-generation"
MODEL_PRO = "gemini-2.5-pro-preview-06-05"

FOOD_PROMPT = """Professional restaurant food photography of {dish_name}.
{description}
Studio lighting, clean background, appetizing presentation, sharp focus,
warm tones, 1:1 square format. Ultra-realistic, high resolution.
No text, no people, no watermarks."""


class ImageService:
    """Gemini-powered image generation with S3 persistence."""

    def __init__(self) -> None:
        self._model_cache: dict = {}

    def _get_api_key(self) -> str:
        key = settings.google_api_key or settings.gemini_api_key
        if not key:
            raise RuntimeError(
                "Google API key not configured. "
                "Set GOOGLE_API_KEY or GEMINI_API_KEY in environment."
            )
        return key

    def _get_model(self, model_id: str):
        """Lazy-init and cache genai model instances."""
        if model_id not in self._model_cache:
            import google.generativeai as genai
            genai.configure(api_key=self._get_api_key())
            self._model_cache[model_id] = genai.GenerativeModel(model_id)
        return self._model_cache[model_id]

    async def generate_food_image(
        self,
        dish_name: str,
        description: str = "",
        brand_id: str = "",
        quality: str = "fast",
    ) -> dict:
        """Generate a food image and persist to S3. Returns permanent URL."""
        import google.generativeai as genai

        model_id = MODEL_PRO if quality == "pro" else MODEL_FAST
        prompt = FOOD_PROMPT.format(dish_name=dish_name, description=description)

        logger.info("Generating food image", dish=dish_name, model=model_id, quality=quality)

        model = self._get_model(model_id)
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(
                contents=prompt,
                generation_config=genai.GenerationConfig(
                    response_modalities=["IMAGE"],
                ),
            ),
        )

        image_bytes = self._extract_image_bytes(response)
        if not image_bytes:
            raise ValueError(f"Gemini returned no image for: {dish_name}")

        s3_url = await self._persist_image(
            image_bytes, brand_id, f"food-{uuid.uuid4().hex[:12]}.png"
        )

        return {
            "url": s3_url,
            "model": model_id,
            "quality": quality,
            "persisted": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def enhance_food_photo(
        self,
        source_url: str,
        brand_id: str = "",
        style: str = "restaurant",
    ) -> dict:
        """Enhance an existing food photo using Gemini Pro."""
        import google.generativeai as genai

        STYLES = {
            "restaurant": "Professional restaurant menu photography, studio lighting, clean background.",
            "delivery": "Food delivery app photography, bright lighting, mobile-optimized.",
            "instagram": "Instagram aesthetic, moody lighting, artistic plating, warm tones.",
        }
        style_prompt = STYLES.get(style, STYLES["restaurant"])

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(source_url)
            resp.raise_for_status()
            source_bytes = resp.content

        model = self._get_model(MODEL_PRO)
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(
                contents=[
                    {"mime_type": "image/jpeg", "data": base64.b64encode(source_bytes).decode()},
                    f"Enhance this food photo: {style_prompt} Keep the dish identical, only improve lighting and composition.",
                ],
                generation_config=genai.GenerationConfig(response_modalities=["IMAGE"]),
            ),
        )

        image_bytes = self._extract_image_bytes(response)
        if not image_bytes:
            raise ValueError("No enhanced image returned from Gemini")

        s3_url = await self._persist_image(
            image_bytes, brand_id, f"enhanced-{uuid.uuid4().hex[:12]}.png"
        )

        return {
            "url": s3_url,
            "model": MODEL_PRO,
            "style": style,
            "persisted": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _extract_image_bytes(response) -> bytes | None:
        """Extract image bytes from a Gemini response."""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                raw = part.inline_data.data
                return base64.b64decode(raw) if isinstance(raw, str) else raw
        return None

    @staticmethod
    async def _persist_image(image_bytes: bytes, brand_id: str, filename: str) -> str:
        """Upload image bytes to S3 and return permanent URL."""
        storage = get_storage_service()
        key = storage.generate_key(
            brand_id=brand_id or "ai-studio",
            media_type="image",
            original_filename=filename,
        )
        ct = "image/png" if filename.endswith(".png") else "image/jpeg"
        result = await storage.upload_bytes(data=image_bytes, key=key, content_type=ct)
        logger.info("Image persisted to S3", key=key, size=len(image_bytes))
        return result["url"]
