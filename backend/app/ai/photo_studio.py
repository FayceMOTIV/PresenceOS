"""
PresenceOS - Photo Studio

AI-powered photo generation using DALL-E 3. Generates high-quality
marketing photos tailored to specific business niches and visual styles.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any

import openai
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# ── Style definitions ───────────────────────────────────────────────────────

STYLE_DESCRIPTIONS: dict[str, str] = {
    "natural": (
        "natural lighting, authentic atmosphere, warm and inviting, "
        "shot on professional camera, realistic colors, no heavy post-processing"
    ),
    "cinematic": (
        "cinematic lighting with dramatic shadows, moody atmosphere, "
        "wide aperture bokeh, film-like color grading, golden hour tones, "
        "professional cinematography aesthetic"
    ),
    "vibrant": (
        "vibrant saturated colors, bright and energetic, eye-catching composition, "
        "high contrast, modern editorial style, social media optimized"
    ),
    "minimalist": (
        "clean minimalist composition, white or neutral background, "
        "negative space, simple elegant styling, Scandinavian aesthetic, "
        "sharp focus on the subject"
    ),
}

# ── Niche context definitions ───────────────────────────────────────────────

NICHE_CONTEXTS: dict[str, str] = {
    "restaurant": (
        "upscale restaurant setting, beautifully plated food, "
        "elegant table setting, warm ambient lighting, fine dining atmosphere"
    ),
    "hotel": (
        "luxury hotel environment, elegant interior design, "
        "premium amenities, sophisticated ambiance, high-end hospitality"
    ),
    "beauty_salon": (
        "modern beauty salon, professional beauty products, "
        "clean and elegant workspace, beauty and wellness atmosphere"
    ),
    "fitness": (
        "modern fitness studio or gym, athletic equipment, "
        "energetic and motivating environment, health and wellness focus"
    ),
    "retail": (
        "stylish retail boutique, curated product display, "
        "attractive store merchandising, premium shopping experience"
    ),
}

# ── Default niche context for unknown niches ───────────────────────────────

DEFAULT_NICHE_CONTEXT = (
    "professional business environment, high-quality presentation, "
    "polished and modern aesthetic"
)


class PhotoStudio:
    """AI photo generation service using DALL-E 3.

    Generates marketing-quality photos with customizable styles and
    niche-specific visual contexts.
    """

    def __init__(self) -> None:
        self._client: openai.AsyncOpenAI | None = None

    def _get_client(self) -> openai.AsyncOpenAI:
        """Lazy initialization of the OpenAI client."""
        if self._client is None:
            if not settings.openai_api_key:
                raise RuntimeError(
                    "OpenAI API key is not configured. "
                    "Set OPENAI_API_KEY in your environment."
                )
            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def generate_photo(
        self,
        prompt: str,
        niche: str,
        style: str = "natural",
        size: str = "1024x1024",
    ) -> dict[str, Any]:
        """Generate a single marketing photo using DALL-E 3.

        Args:
            prompt: Base description of the desired image.
            niche: Business niche for contextual enhancement
                   (restaurant, hotel, beauty_salon, fitness, retail).
            style: Visual style preset (natural, cinematic, vibrant, minimalist).
            size: Image dimensions (1024x1024, 1792x1024, 1024x1792).

        Returns:
            Dict with image_url, revised_prompt, style, niche, size, generated_at.
        """
        client = self._get_client()
        enhanced_prompt = self._enhance_prompt(prompt, niche, style)

        logger.info(
            "Generating photo",
            niche=niche,
            style=style,
            size=size,
            prompt_length=len(enhanced_prompt),
        )

        try:
            response = await client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=size,  # type: ignore[arg-type]
                quality="hd",
                n=1,
            )
        except Exception as exc:
            logger.error(
                "Photo generation failed",
                niche=niche,
                style=style,
                error=str(exc),
            )
            raise

        url = response.data[0].url
        revised = response.data[0].revised_prompt

        result: dict[str, Any] = {
            "image_url": url,
            "revised_prompt": revised,
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "style": style,
            "niche": niche,
            "size": size,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Photo generated successfully", niche=niche, style=style)
        return result

    async def generate_variations(
        self,
        base_prompt: str,
        niche: str,
        count: int = 4,
    ) -> list[dict[str, Any]]:
        """Generate multiple photo variations with different styles.

        Runs all generations in parallel for optimal performance.

        Args:
            base_prompt: Base description to use across all variations.
            niche: Business niche for contextual enhancement.
            count: Number of variations to generate (default: 4, max: 4).

        Returns:
            List of dicts, each with image_url and style metadata.
        """
        styles = list(STYLE_DESCRIPTIONS.keys())
        # Cap to available styles and requested count
        selected_styles = styles[: min(count, len(styles))]

        logger.info(
            "Generating photo variations",
            niche=niche,
            count=len(selected_styles),
            styles=selected_styles,
        )

        tasks = [
            self.generate_photo(
                prompt=base_prompt,
                niche=niche,
                style=style,
            )
            for style in selected_styles
        ]

        try:
            variations = await asyncio.gather(*tasks)
        except Exception as exc:
            logger.error(
                "Photo variations generation failed",
                niche=niche,
                error=str(exc),
            )
            raise

        logger.info(
            "Photo variations generated successfully",
            niche=niche,
            count=len(variations),
        )
        return list(variations)

    def _enhance_prompt(self, prompt: str, niche: str, style: str) -> str:
        """Enrich the base prompt with niche context and style descriptors.

        Args:
            prompt: The user-provided base description.
            niche: Business niche key for contextual details.
            style: Visual style key for aesthetic descriptors.

        Returns:
            A fully enriched prompt string ready for DALL-E 3.
        """
        niche_context = NICHE_CONTEXTS.get(niche, DEFAULT_NICHE_CONTEXT)
        style_descriptor = STYLE_DESCRIPTIONS.get(
            style, STYLE_DESCRIPTIONS["natural"]
        )

        enhanced = (
            f"{prompt}. "
            f"Setting: {niche_context}. "
            f"Visual style: {style_descriptor}. "
            f"Professional marketing photography, suitable for social media. "
            f"High resolution, commercially viable image."
        )

        return enhanced
