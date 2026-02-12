"""
PresenceOS — Content Repurposing Engine (Feature 4)

Transform one piece of content into multiple platform-optimized formats.
1 content → up to 7 variants: Instagram Post, Instagram Reel, Story, TikTok,
Facebook, Google Business Profile, LinkedIn.

Adapts captions (length, tone, hashtags, CTA), and provides crop/aspect ratio
specs for media so the frontend or a future worker can apply ffmpeg transforms.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class OutputFormat(str, Enum):
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_STORY = "instagram_story"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    GBP = "gbp"
    LINKEDIN = "linkedin"


# Platform-specific constraints and guidelines
FORMAT_SPECS: dict[str, dict[str, Any]] = {
    OutputFormat.INSTAGRAM_POST: {
        "label": "Instagram Post",
        "aspect_ratio": "1:1",
        "resolution": "1080x1080",
        "max_caption_length": 2200,
        "ideal_caption_length": 150,
        "max_hashtags": 30,
        "ideal_hashtags": 10,
        "tone": "casual, lifestyle, emojis OK",
        "cta_style": "soft (commentez, partagez, enregistrez)",
    },
    OutputFormat.INSTAGRAM_REEL: {
        "label": "Instagram Reel",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "max_caption_length": 2200,
        "ideal_caption_length": 100,
        "max_hashtags": 15,
        "ideal_hashtags": 8,
        "tone": "energique, hook en premiere ligne",
        "cta_style": "direct (suivez pour plus, likez si...)",
    },
    OutputFormat.INSTAGRAM_STORY: {
        "label": "Instagram Story",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "max_caption_length": 250,
        "ideal_caption_length": 50,
        "max_hashtags": 5,
        "ideal_hashtags": 3,
        "tone": "spontane, stickers/polls suggeres",
        "cta_style": "interactive (sondage, question, swipe up)",
    },
    OutputFormat.TIKTOK: {
        "label": "TikTok",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "max_caption_length": 4000,
        "ideal_caption_length": 80,
        "max_hashtags": 8,
        "ideal_hashtags": 5,
        "tone": "authentique, trending, humour OK",
        "cta_style": "viral (duet, stitch, commentez votre...)",
    },
    OutputFormat.FACEBOOK: {
        "label": "Facebook",
        "aspect_ratio": "16:9",
        "resolution": "1200x630",
        "max_caption_length": 63206,
        "ideal_caption_length": 250,
        "max_hashtags": 5,
        "ideal_hashtags": 3,
        "tone": "informatif, communautaire, emotionnel",
        "cta_style": "engagement (qu'en pensez-vous?, partagez si...)",
    },
    OutputFormat.GBP: {
        "label": "Google Business Profile",
        "aspect_ratio": "4:3",
        "resolution": "1200x900",
        "max_caption_length": 1500,
        "ideal_caption_length": 200,
        "max_hashtags": 0,
        "ideal_hashtags": 0,
        "tone": "professionnel, local, informatif",
        "cta_style": "action (reservez, appelez, visitez-nous)",
    },
    OutputFormat.LINKEDIN: {
        "label": "LinkedIn",
        "aspect_ratio": "1.91:1",
        "resolution": "1200x628",
        "max_caption_length": 3000,
        "ideal_caption_length": 300,
        "max_hashtags": 5,
        "ideal_hashtags": 3,
        "tone": "professionnel, storytelling, expertise",
        "cta_style": "thought leadership (qu'en pensez-vous?, reagissez)",
    },
}


def _adapt_caption(
    original_caption: str,
    original_hashtags: list[str],
    target_format: str,
) -> dict[str, Any]:
    """Adapt a caption to a target platform's constraints.

    Uses rule-based adaptation: truncate/extend, adjust hashtag count,
    add platform-appropriate CTA.
    """
    spec = FORMAT_SPECS[target_format]
    ideal_len = spec["ideal_caption_length"]
    ideal_tags = spec["ideal_hashtags"]

    # Adapt caption length
    adapted_caption = original_caption
    if len(adapted_caption) > ideal_len * 2:
        # Truncate and add ellipsis for short-form platforms
        adapted_caption = adapted_caption[: ideal_len] + "..."

    # Adapt hashtags
    adapted_hashtags = original_hashtags[:ideal_tags] if ideal_tags > 0 else []

    # Add platform CTA suggestion
    cta_suggestions = {
        OutputFormat.INSTAGRAM_POST: "Enregistrez ce post pour plus tard !",
        OutputFormat.INSTAGRAM_REEL: "Suivez pour d'autres recettes !",
        OutputFormat.INSTAGRAM_STORY: "Votez en story !",
        OutputFormat.TIKTOK: "Commentez votre plat prefere !",
        OutputFormat.FACEBOOK: "Qu'en pensez-vous ? Dites-le en commentaire !",
        OutputFormat.GBP: "Reservez votre table des maintenant.",
        OutputFormat.LINKEDIN: "Qu'en pensez-vous ? Partagez votre experience.",
    }

    return {
        "caption": adapted_caption,
        "hashtags": adapted_hashtags,
        "suggested_cta": cta_suggestions.get(target_format, ""),
        "hashtag_text": " ".join(f"#{t}" for t in adapted_hashtags) if adapted_hashtags else "",
    }


def _get_crop_spec(target_format: str) -> dict[str, str]:
    """Return crop/resize specification for media adaptation."""
    spec = FORMAT_SPECS[target_format]
    return {
        "aspect_ratio": spec["aspect_ratio"],
        "resolution": spec["resolution"],
    }


class ContentRepurposerService:
    """Repurpose one piece of content into multiple platform-adapted formats."""

    def __init__(self) -> None:
        self._packages: dict[str, dict] = {}

    def repurpose(
        self,
        brand_id: str,
        original_caption: str,
        original_hashtags: list[str] | None = None,
        original_media_urls: list[str] | None = None,
        target_formats: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate a content package with platform-adapted variants.

        Args:
            brand_id: Brand identifier.
            original_caption: Source caption text.
            original_hashtags: Source hashtags (without #).
            original_media_urls: Source media file URLs.
            target_formats: List of OutputFormat values. If None, generates all.

        Returns:
            Content package with all variants.
        """
        hashtags = original_hashtags or []
        media_urls = original_media_urls or []

        if target_formats is None:
            formats = list(OutputFormat)
        else:
            formats = [OutputFormat(f) for f in target_formats]

        package_id = str(uuid.uuid4())
        variants = []

        for fmt in formats:
            adapted = _adapt_caption(original_caption, hashtags, fmt)
            crop = _get_crop_spec(fmt)
            spec = FORMAT_SPECS[fmt]

            variant = {
                "id": str(uuid.uuid4()),
                "format": fmt.value,
                "label": spec["label"],
                "caption": adapted["caption"],
                "hashtags": adapted["hashtags"],
                "hashtag_text": adapted["hashtag_text"],
                "suggested_cta": adapted["suggested_cta"],
                "media_urls": media_urls,
                "crop_spec": crop,
                "tone": spec["tone"],
                "platform_tips": f"Longueur ideale : {spec['ideal_caption_length']} car. | "
                                 f"Hashtags : {spec['ideal_hashtags']} max | "
                                 f"Format media : {spec['aspect_ratio']}",
            }
            variants.append(variant)

        package = {
            "id": package_id,
            "brand_id": brand_id,
            "original": {
                "caption": original_caption,
                "hashtags": hashtags,
                "media_urls": media_urls,
            },
            "variants": variants,
            "variant_count": len(variants),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._packages[package_id] = package
        logger.info("content_repurposed", package_id=package_id, variant_count=len(variants))
        return package

    def get_package(self, package_id: str) -> dict[str, Any] | None:
        """Retrieve a previously generated content package."""
        return self._packages.get(package_id)

    def get_format_specs(self) -> dict[str, dict]:
        """Return all format specifications for the frontend."""
        return {
            fmt.value: {
                "label": spec["label"],
                "aspect_ratio": spec["aspect_ratio"],
                "resolution": spec["resolution"],
                "ideal_caption_length": spec["ideal_caption_length"],
                "max_hashtags": spec["max_hashtags"],
                "tone": spec["tone"],
                "cta_style": spec["cta_style"],
            }
            for fmt, spec in FORMAT_SPECS.items()
        }
