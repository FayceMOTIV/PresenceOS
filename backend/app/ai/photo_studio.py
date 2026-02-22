"""
PresenceOS - Photo Studio

AI-powered photo generation using DALL-E 3. Generates high-quality marketing
photos tailored to any business niche with expert-grade prompt engineering.

Supports 20+ business niches with specific visual direction, negative prompts,
and platform-optimized sizing.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx
import openai
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# ── Style definitions with expert photography direction ──────────────────────

STYLE_DESCRIPTIONS: dict[str, str] = {
    "natural": (
        "natural soft window lighting, authentic and warm atmosphere, "
        "shallow depth of field at f/2.8, slightly warm white balance (5600K), "
        "no heavy filters, shot on Canon EOS R5 with 50mm lens, "
        "the kind of photo a skilled food blogger would take"
    ),
    "cinematic": (
        "dramatic cinematic lighting with strong key light and soft fill, "
        "deep shadows with detail, wide aperture bokeh at f/1.8, "
        "film-like color grading with teal and orange tones, golden hour warmth, "
        "anamorphic lens flare subtly present, shot on ARRI Alexa aesthetic, "
        "professional commercial photography with editorial quality"
    ),
    "vibrant": (
        "vibrant saturated colors with high contrast, bright and energetic, "
        "punchy color grading, slightly overhead angle for impact, "
        "clean sharp focus across the frame at f/5.6, studio strobe lighting, "
        "modern editorial style optimized for social media scroll-stopping, "
        "the kind of image that gets saved and shared on Instagram"
    ),
    "minimalist": (
        "clean minimalist composition with generous negative space, "
        "soft neutral background (white marble or light wood), "
        "single elegant subject as hero, simple props only, "
        "even diffused lighting, shot at f/4 for slight depth, "
        "Scandinavian design aesthetic, calming and sophisticated"
    ),
}

# ── Niche contexts with 20+ business types ───────────────────────────────────
# Each entry provides: setting description, typical subjects, mood keywords

NICHE_CONTEXTS: dict[str, dict[str, str]] = {
    "restaurant": {
        "setting": "upscale restaurant table with elegant place setting, warm ambient lighting from candles or Edison bulbs",
        "subjects": "beautifully plated dish, fresh ingredients visible, garnish details, steam rising from hot food",
        "mood": "appetizing, inviting, gourmet, the viewer should want to taste this immediately",
    },
    "fast_food": {
        "setting": "casual modern fast food counter, branded packaging, energetic atmosphere",
        "subjects": "stacked burger dripping with sauce, crispy fries, vibrant soda, messy but appetizing",
        "mood": "craveable, indulgent, fun, casual",
    },
    "bakery": {
        "setting": "artisan bakery counter with flour-dusted wooden surface, rustic shelves in background",
        "subjects": "fresh-baked bread with golden crust, croissants, pastries, visible texture and layers",
        "mood": "artisanal, warm, comforting, morning freshness",
    },
    "cafe": {
        "setting": "cozy coffee shop with exposed brick, plants, warm wood tones, morning light through windows",
        "subjects": "latte art in ceramic cup, pastry, open book or laptop subtly in background",
        "mood": "cozy, hipster, relaxing, Instagram-worthy",
    },
    "bar": {
        "setting": "atmospheric cocktail bar with moody low lighting, polished bar counter, backlit bottles",
        "subjects": "crafted cocktail with garnish, ice catching the light, bartender hands in background",
        "mood": "sophisticated, nightlife, mixology, atmospheric",
    },
    "hotel": {
        "setting": "luxury hotel suite with premium linens, city view through large windows, elegant furniture",
        "subjects": "perfectly made bed, welcome amenities, plush robes, panoramic view",
        "mood": "luxurious, aspirational, restful, premium hospitality",
    },
    "beauty_salon": {
        "setting": "modern beauty salon with clean lines, large mirrors, professional products displayed",
        "subjects": "beauty treatment in progress, styled hair, manicured nails, before/after transformation",
        "mood": "glamorous, transformation, self-care, confidence",
    },
    "barber": {
        "setting": "vintage-modern barbershop with leather chair, hot towels, straight razors on display",
        "subjects": "precise fade haircut, beard grooming, classic tools, masculine atmosphere",
        "mood": "masculine, craftsmanship, tradition meets modern",
    },
    "spa": {
        "setting": "zen spa environment with natural stones, bamboo, soft lighting, water features",
        "subjects": "massage treatment, essential oils, hot stones, serene facial expression",
        "mood": "tranquil, wellness, rejuvenation, escape",
    },
    "fitness": {
        "setting": "modern gym or fitness studio with clean equipment, motivational atmosphere, natural light",
        "subjects": "athlete mid-workout, dynamic movement, sweat glistening, determination visible",
        "mood": "energetic, motivational, powerful, determined",
    },
    "yoga": {
        "setting": "peaceful yoga studio with wooden floors, plants, soft morning light, minimal decoration",
        "subjects": "elegant yoga pose, meditation, breathing exercise, flexible body",
        "mood": "serene, mindful, balanced, inner peace",
    },
    "retail": {
        "setting": "curated boutique with styled shelves, warm spotlighting, lifestyle merchandising",
        "subjects": "beautifully arranged products, gift-wrapped packages, seasonal display",
        "mood": "aspirational, curated, lifestyle, desire to purchase",
    },
    "fashion": {
        "setting": "editorial fashion environment, urban backdrop or studio with seamless background",
        "subjects": "model wearing the collection, fabric texture detail, movement in clothing",
        "mood": "editorial, trendy, confident, style-forward",
    },
    "jewelry": {
        "setting": "elegant display on velvet or marble surface, soft focused spotlight, dark background",
        "subjects": "jewelry piece catching light, gemstone facets, delicate chain detail, worn on model",
        "mood": "luxurious, precious, detailed, desire",
    },
    "florist": {
        "setting": "charming flower shop with buckets of blooms, botanical garden feel, natural light",
        "subjects": "artfully arranged bouquet, seasonal flowers, color harmony, delicate petals",
        "mood": "romantic, fresh, colorful, natural beauty",
    },
    "real_estate": {
        "setting": "stunning property interior or exterior, architectural details, perfect staging",
        "subjects": "spacious living room, kitchen island, terrace view, architectural facade",
        "mood": "aspirational, spacious, dream home, move-in ready",
    },
    "dental": {
        "setting": "modern dental clinic with clean lines, reassuring environment, professional equipment",
        "subjects": "confident smile, team in scrubs, modern treatment room, before/after results",
        "mood": "professional, reassuring, clean, confidence",
    },
    "veterinary": {
        "setting": "warm veterinary clinic with happy pets, caring staff, clean examination room",
        "subjects": "adorable pet with veterinarian, puppy check-up, cat being cuddled, caring interaction",
        "mood": "caring, emotional, trust, love for animals",
    },
    "auto": {
        "setting": "car dealership or garage, polished vehicle, dramatic lighting on car body",
        "subjects": "luxury car detail, engine bay, interior cockpit, driving shot with motion blur",
        "mood": "powerful, precision, luxury, performance",
    },
    "tech": {
        "setting": "modern office or co-working space, screens with code or dashboards, clean desk setup",
        "subjects": "sleek laptop, team collaboration, product on screen, innovation atmosphere",
        "mood": "innovative, clean, futuristic, professional",
    },
    "education": {
        "setting": "bright classroom or online learning environment, books, engaged students",
        "subjects": "student having aha moment, interactive lesson, graduation, mentoring scene",
        "mood": "inspiring, growth, achievement, knowledge",
    },
    "event": {
        "setting": "decorated event venue, fairy lights, elegant table setting, celebration atmosphere",
        "subjects": "wedding detail, corporate event setup, party atmosphere, candid joy moments",
        "mood": "celebratory, magical, memorable, festive",
    },
    "food_truck": {
        "setting": "colorful food truck at outdoor market or festival, urban street setting",
        "subjects": "street food being served, queue of happy customers, vibrant signage",
        "mood": "fun, casual, urban, community",
    },
}

DEFAULT_NICHE_CONTEXT: dict[str, str] = {
    "setting": "professional business environment, modern and clean workspace",
    "subjects": "the main subject beautifully presented, attention to detail",
    "mood": "professional, polished, trustworthy, high-quality",
}

# ── Negative prompt elements (what DALL-E should avoid) ──────────────────────

NEGATIVE_INSTRUCTIONS = (
    "IMPORTANT RESTRICTIONS — The image must NOT contain: "
    "any text, words, letters, numbers, logos, watermarks, or signatures. "
    "No brand names visible. No deformed hands or fingers. "
    "No blurry faces. No artificial-looking or plastic-like skin. "
    "No stock photo feel — this must look authentic and real. "
    "No cluttered or messy composition."
)


class PhotoStudio:
    """AI photo generation service using DALL-E 3.

    Generates marketing-quality photos with customizable styles and
    niche-specific visual contexts for 20+ business types.
    """

    def __init__(self) -> None:
        self._client: openai.AsyncOpenAI | None = None
        self._storage = None

    def _get_storage(self):
        """Lazy initialization of the storage service."""
        if self._storage is None:
            try:
                from app.services.storage import get_storage_service
                self._storage = get_storage_service()
            except Exception:
                logger.warning("Storage service not available, DALL-E URLs will be ephemeral")
        return self._storage

    async def _persist_image(self, dalle_url: str, niche: str, style: str) -> str:
        """Download a DALL-E image and persist it to S3/MinIO.

        Returns the permanent S3 URL, or the original DALL-E URL as fallback
        if storage is unavailable.
        """
        storage = self._get_storage()
        if not storage:
            return dalle_url

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(dalle_url)
                resp.raise_for_status()
                image_bytes = resp.content

            key = storage.generate_key(
                brand_id="ai-studio",
                media_type="image",
                original_filename=f"dalle_{niche}_{style}.png",
            )
            result = await storage.upload_bytes(
                data=image_bytes,
                key=key,
                content_type="image/png",
            )
            logger.info("DALL-E image persisted", key=key, size=len(image_bytes))
            return result["url"]
        except Exception as exc:
            logger.warning("Failed to persist DALL-E image, using ephemeral URL", error=str(exc))
            return dalle_url

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
        niche: str = "restaurant",
        style: str = "natural",
        size: str = "1024x1024",
        brand_name: str | None = None,
    ) -> dict[str, Any]:
        """Generate a single marketing photo using DALL-E 3.

        Args:
            prompt: Base description of the desired image.
            niche: Business niche key (restaurant, cafe, fitness, etc.).
                   Falls back to DEFAULT_NICHE_CONTEXT for unknown niches.
            style: Visual style preset (natural, cinematic, vibrant, minimalist).
            size: Image dimensions (1024x1024, 1792x1024, 1024x1792).
            brand_name: Optional brand name for context (not rendered in image).

        Returns:
            Dict with image_url, revised_prompt, style, niche, size, generated_at.
        """
        client = self._get_client()
        enhanced_prompt = self._enhance_prompt(prompt, niche, style, brand_name)

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
            logger.error("Photo generation failed", niche=niche, style=style, error=str(exc))
            raise

        dalle_url = response.data[0].url
        revised = response.data[0].revised_prompt

        # Persist to S3 so the URL doesn't expire after 1 hour
        permanent_url = await self._persist_image(dalle_url, niche, style)

        result: dict[str, Any] = {
            "image_url": permanent_url,
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
        niche: str = "restaurant",
        count: int = 4,
        brand_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate multiple photo variations with different styles in parallel.

        Args:
            base_prompt: Base description to use across all variations.
            niche: Business niche for contextual enhancement.
            count: Number of variations (default: 4, max: 4).
            brand_name: Optional brand name for context.

        Returns:
            List of dicts, each with image_url and style metadata.
        """
        styles = list(STYLE_DESCRIPTIONS.keys())
        selected_styles = styles[: min(count, len(styles))]

        logger.info("Generating photo variations", niche=niche, count=len(selected_styles))

        tasks = [
            self.generate_photo(
                prompt=base_prompt,
                niche=niche,
                style=style,
                brand_name=brand_name,
            )
            for style in selected_styles
        ]

        try:
            variations = await asyncio.gather(*tasks)
        except Exception as exc:
            logger.error("Photo variations generation failed", niche=niche, error=str(exc))
            raise

        logger.info("Photo variations generated", niche=niche, count=len(variations))
        return list(variations)

    def _enhance_prompt(
        self,
        prompt: str,
        niche: str,
        style: str,
        brand_name: str | None = None,
    ) -> str:
        """Build an expert-grade DALL-E 3 prompt with niche context, style
        direction, and negative constraints.

        The prompt follows the structure:
        1. Subject (what the user asked for)
        2. Setting/Environment (from niche context)
        3. Mood/Atmosphere (from niche context)
        4. Technical photography direction (from style)
        5. Quality markers
        6. Negative instructions (what to avoid)
        """
        niche_ctx = NICHE_CONTEXTS.get(niche, DEFAULT_NICHE_CONTEXT)
        style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["natural"])

        parts = [
            # 1. Subject
            f"A professional marketing photograph of: {prompt}.",
            # 2. Setting
            f"Environment: {niche_ctx['setting']}.",
            # 3. Subject detail
            f"Key visual elements: {niche_ctx['subjects']}.",
            # 4. Mood
            f"The image should feel: {niche_ctx['mood']}.",
            # 5. Style/Technical
            f"Photography style: {style_desc}.",
            # 6. Quality
            "Ultra high quality, commercially viable, suitable for Instagram, "
            "magazine-worthy composition, perfect exposure and white balance.",
        ]

        # Brand context (helps DALL-E understand the vibe without rendering text)
        if brand_name:
            parts.append(
                f"This is for the brand '{brand_name}' — match the sophistication "
                f"level and aesthetic that this brand name suggests."
            )

        # 7. Negative instructions
        parts.append(NEGATIVE_INSTRUCTIONS)

        return " ".join(parts)

    @staticmethod
    def get_supported_niches() -> list[dict[str, str]]:
        """Return the list of supported niches with display labels."""
        labels = {
            "restaurant": "Restaurant",
            "fast_food": "Fast-food",
            "bakery": "Boulangerie",
            "cafe": "Café",
            "bar": "Bar / Cocktails",
            "hotel": "Hôtel",
            "beauty_salon": "Salon de beauté",
            "barber": "Barbier",
            "spa": "Spa / Bien-être",
            "fitness": "Salle de sport",
            "yoga": "Yoga / Pilates",
            "retail": "Commerce / Boutique",
            "fashion": "Mode",
            "jewelry": "Bijouterie",
            "florist": "Fleuriste",
            "real_estate": "Immobilier",
            "dental": "Dentiste",
            "veterinary": "Vétérinaire",
            "auto": "Automobile",
            "tech": "Tech / SaaS",
            "education": "Formation / Éducation",
            "event": "Événementiel",
            "food_truck": "Food truck",
        }
        return [
            {"id": niche_id, "label": label}
            for niche_id, label in labels.items()
        ]
