"""
Generic Remotion Template Rendering Engine

Calls the video-engine (rs3-remotion) service to render any Remotion composition.
Pattern: Upload images -> call render endpoint -> get base64 video -> persist to S3.

Supported templates:
  - PromoFlash: /render/promo-flash
  - RestaurantShowcase: /render/restaurant-showcase
  - DailyStory: /render/daily-story
"""

import base64
import uuid

import httpx
import structlog

from app.core.config import settings
from app.services.storage import get_storage_service

logger = structlog.get_logger()


class RemotionTemplateEngine:
    """Generic engine to render Remotion templates and persist to S3."""

    TIMEOUT = 180  # 3 minutes max per render

    async def render_template(
        self,
        endpoint: str,
        props: dict,
        brand_id: str,
        template_name: str,
    ) -> dict:
        """Render a Remotion template and persist the video to S3.

        Args:
            endpoint: Remotion server endpoint (e.g. "/render/promo-flash")
            props: Input props for the Remotion composition
            brand_id: Brand ID for S3 key generation
            template_name: Human-readable template name for logging

        Returns:
            {"video_url": str, "duration_seconds": int, "template": str}
        """
        logger.info(
            "remotion.template.render_start",
            template=template_name,
            endpoint=endpoint,
        )

        remotion_url = settings.remotion_service_url
        if not remotion_url:
            raise RuntimeError("REMOTION_SERVICE_URL not configured")

        # Call Remotion render
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    f"{remotion_url}{endpoint}",
                    json=props,
                )
        except httpx.TimeoutException:
            raise RuntimeError(f"Remotion render timed out for {template_name}")

        if response.status_code == 503:
            raise RuntimeError("Remotion service warming up, retry in 30s")

        if response.status_code != 200:
            raise RuntimeError(
                f"Remotion returned {response.status_code}: "
                f"{response.text[:300]}"
            )

        data = response.json()
        video_b64 = data.get("video_base64")
        if not video_b64:
            raise RuntimeError("No video_base64 in Remotion response")

        video_bytes = base64.b64decode(video_b64)

        # Persist to S3
        storage = get_storage_service()
        key = storage.generate_key(
            brand_id=brand_id or "ai-studio",
            media_type="video",
            original_filename=f"{template_name}_{uuid.uuid4().hex[:8]}.mp4",
        )
        result = await storage.upload_bytes(
            data=video_bytes, key=key, content_type="video/mp4",
        )

        video_url = result["url"]
        logger.info(
            "remotion.template.render_done",
            template=template_name,
            video_url=video_url[:60],
            size=len(video_bytes),
        )

        return {
            "video_url": video_url,
            "template": template_name,
        }

    async def render_promo_flash(
        self,
        background_image_url: str,
        brand_id: str,
        headline: str = "OFFRE SPECIALE",
        subheadline: str = "",
        discount: str = "-20%",
        promo_code: str = "",
        cta_text: str = "Reservez maintenant!",
        primary_color: str = "#E63946",
        brand_name: str = "",
        valid_until: str = "",
    ) -> dict:
        """Render PromoFlash template. Returns {"video_url", "duration_seconds", "template"}."""
        result = await self.render_template(
            endpoint="/render/promo-flash",
            props={
                "backgroundImage": background_image_url,
                "headline": headline,
                "subheadline": subheadline,
                "discount": discount,
                "promoCode": promo_code,
                "ctaText": cta_text,
                "primaryColor": primary_color,
                "brandName": brand_name,
                "validUntil": valid_until,
            },
            brand_id=brand_id,
            template_name="promo-flash",
        )
        result["duration_seconds"] = 8
        return result

    async def render_restaurant_showcase(
        self,
        dishes: list[dict],
        brand_id: str,
        brand_name: str = "Mon Restaurant",
        tagline: str = "Nos specialites",
        primary_color: str = "#FF6B35",
    ) -> dict:
        """Render RestaurantShowcase template.

        dishes: [{"name": str, "image": str (URL), "description": str?}, ...]
        """
        result = await self.render_template(
            endpoint="/render/restaurant-showcase",
            props={
                "brandName": brand_name,
                "tagline": tagline,
                "dishes": dishes,
                "primaryColor": primary_color,
            },
            brand_id=brand_id,
            template_name="restaurant-showcase",
        )
        result["duration_seconds"] = 8
        return result

    async def render_daily_story(
        self,
        slides: list[dict],
        brand_id: str,
        brand_name: str = "Mon Restaurant",
        primary_color: str = "#6C63FF",
    ) -> dict:
        """Render DailyStory template.

        slides: [{"text": str, "image": str (URL)}, ...]
        """
        result = await self.render_template(
            endpoint="/render/daily-story",
            props={
                "slides": slides,
                "brandName": brand_name,
                "primaryColor": primary_color,
            },
            brand_id=brand_id,
            template_name="daily-story",
        )
        result["duration_seconds"] = 7
        return result
