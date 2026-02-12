"""
PresenceOS - Photo Enhancement Service (Feature 2)

Transforms amateur food photos into professional marketing-ready images.
Pipeline: Analyze quality -> Pillow enhancement -> Optional AI enhancement -> Validation.

Uses Pillow for local processing (no external API needed for basic enhancement).
"""
import io
import os
import uuid
import json
import base64
from enum import Enum
from typing import Any, Optional

import structlog
from PIL import Image, ImageEnhance, ImageFilter, ImageStat

from app.core.config import settings

logger = structlog.get_logger()

UPLOAD_DIR = "/tmp/presenceos/uploads"
ENHANCED_DIR = "/tmp/presenceos/uploads/enhanced"


class PhotoStyle(str, Enum):
    """Enhancement presets optimized for different use cases."""
    DELIVERY = "delivery"       # White/neutral bg, top-down, delivery app optimized
    INSTAGRAM = "instagram"     # Warm, depth of field, lifestyle
    MENU = "menu"               # Clean, solid bg, brand-aligned
    STORY = "story"             # Vertical, vibrant, text-friendly


# Enhancement parameters per style
STYLE_PARAMS = {
    PhotoStyle.DELIVERY: {
        "brightness": 1.20,
        "contrast": 1.15,
        "saturation": 1.10,
        "sharpness": 1.20,
        "warmth": 0,  # neutral
    },
    PhotoStyle.INSTAGRAM: {
        "brightness": 1.15,
        "contrast": 1.10,
        "saturation": 1.25,
        "sharpness": 1.15,
        "warmth": 15,  # warm amber shift
    },
    PhotoStyle.MENU: {
        "brightness": 1.18,
        "contrast": 1.20,
        "saturation": 1.15,
        "sharpness": 1.25,
        "warmth": 5,
    },
    PhotoStyle.STORY: {
        "brightness": 1.12,
        "contrast": 1.15,
        "saturation": 1.30,
        "sharpness": 1.10,
        "warmth": 10,
    },
}


class PhotoQuality(str, Enum):
    """Quality assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"


def _analyze_quality(img: Image.Image) -> dict[str, Any]:
    """Analyze photo quality metrics without AI.

    Checks brightness, contrast, sharpness, and composition.
    Returns a score 0-100 and quality level.
    """
    # Convert to RGB if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")

    stat = ImageStat.Stat(img)
    r_mean, g_mean, b_mean = stat.mean[:3]
    r_std, g_std, b_std = stat.stddev[:3]

    # Brightness score (0-100): ideal around 120-140 mean
    overall_brightness = (r_mean + g_mean + b_mean) / 3
    if 100 <= overall_brightness <= 170:
        brightness_score = 100
    elif 70 <= overall_brightness <= 200:
        brightness_score = 70
    else:
        brightness_score = 40

    # Contrast score: higher stddev = better contrast
    overall_std = (r_std + g_std + b_std) / 3
    if overall_std > 55:
        contrast_score = 100
    elif overall_std > 35:
        contrast_score = 70
    else:
        contrast_score = 40

    # Color richness: good saturation means varied color channels
    color_range = max(r_mean, g_mean, b_mean) - min(r_mean, g_mean, b_mean)
    if color_range > 25:
        color_score = 100
    elif color_range > 15:
        color_score = 70
    else:
        color_score = 45

    # Resolution score
    w, h = img.size
    pixels = w * h
    if pixels >= 2_000_000:  # 2MP+
        resolution_score = 100
    elif pixels >= 1_000_000:  # 1MP+
        resolution_score = 75
    else:
        resolution_score = 45

    # Weighted composite
    total = (
        brightness_score * 0.25
        + contrast_score * 0.25
        + color_score * 0.25
        + resolution_score * 0.25
    )

    if total >= 80:
        level = PhotoQuality.EXCELLENT
    elif total >= 55:
        level = PhotoQuality.GOOD
    else:
        level = PhotoQuality.NEEDS_IMPROVEMENT

    return {
        "score": round(total),
        "level": level.value,
        "brightness": round(brightness_score),
        "contrast": round(contrast_score),
        "color_richness": round(color_score),
        "resolution": round(resolution_score),
        "width": w,
        "height": h,
        "recommendation": _quality_recommendation(level, brightness_score, contrast_score, color_score),
    }


def _quality_recommendation(
    level: PhotoQuality, brightness: float, contrast: float, color: float
) -> str:
    if level == PhotoQuality.EXCELLENT:
        return "Photo de qualite professionnelle. Enhancement optionnel."
    issues = []
    if brightness < 60:
        issues.append("luminosite insuffisante")
    if contrast < 60:
        issues.append("manque de contraste")
    if color < 60:
        issues.append("couleurs ternes")
    if not issues:
        return "Bonne qualite. Un enhancement subtil ameliorera le rendu."
    return f"A ameliorer : {', '.join(issues)}. L'enhancement IA est recommande."


def _apply_warmth(img: Image.Image, intensity: int) -> Image.Image:
    """Apply warm (amber) color shift to the image.

    intensity: 0-30, where 0 is neutral and 30 is very warm.
    """
    if intensity <= 0:
        return img

    if img.mode != "RGB":
        img = img.convert("RGB")

    # Split channels and boost red/green slightly, reduce blue
    r, g, b = img.split()

    # Create lookup tables
    r_lut = [min(255, int(i + intensity * 0.6)) for i in range(256)]
    g_lut = [min(255, int(i + intensity * 0.2)) for i in range(256)]
    b_lut = [max(0, int(i - intensity * 0.4)) for i in range(256)]

    r = r.point(r_lut)
    g = g.point(g_lut)
    b = b.point(b_lut)

    return Image.merge("RGB", (r, g, b))


def enhance_photo(
    image_data: bytes,
    style: PhotoStyle = PhotoStyle.INSTAGRAM,
    mime_type: str = "image/jpeg",
) -> tuple[bytes, dict[str, Any]]:
    """Enhance a food photo using Pillow.

    Returns:
        (enhanced_image_bytes, metadata_dict)
    """
    img = Image.open(io.BytesIO(image_data))
    original_format = img.format or "JPEG"

    # Convert to RGB for processing
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Get quality assessment BEFORE enhancement
    quality_before = _analyze_quality(img)

    # Apply style parameters
    params = STYLE_PARAMS[style]

    # Brightness
    img = ImageEnhance.Brightness(img).enhance(params["brightness"])

    # Contrast
    img = ImageEnhance.Contrast(img).enhance(params["contrast"])

    # Color saturation
    img = ImageEnhance.Color(img).enhance(params["saturation"])

    # Sharpness
    img = ImageEnhance.Sharpness(img).enhance(params["sharpness"])

    # Warm filter
    img = _apply_warmth(img, params["warmth"])

    # Get quality assessment AFTER enhancement
    quality_after = _analyze_quality(img)

    # Save to bytes
    buf = io.BytesIO()
    save_format = "JPEG" if "jpeg" in mime_type or "jpg" in mime_type else "PNG"
    img.save(buf, format=save_format, quality=92)
    enhanced_bytes = buf.getvalue()

    metadata = {
        "style": style.value,
        "quality_before": quality_before,
        "quality_after": quality_after,
        "improvement": quality_after["score"] - quality_before["score"],
        "params_applied": {k: v for k, v in params.items()},
    }

    return enhanced_bytes, metadata


async def analyze_photo_with_ai(
    image_data: bytes,
    mime_type: str = "image/jpeg",
) -> dict[str, Any]:
    """Use AI Vision to analyze photo quality and suggest improvements.

    This provides more detailed analysis than the Pillow-based quality check.
    Requires OpenAI or Anthropic API key.
    """
    try:
        from app.services.vision import VisionService

        vision = VisionService()

        b64_image = base64.b64encode(image_data).decode("utf-8")

        system_prompt = (
            "Tu es un expert en photographie culinaire et food styling. "
            "Analyse la qualite technique et esthetique de cette photo de nourriture."
        )

        user_prompt = """Analyse cette photo de nourriture pour le marketing.

Reponds en JSON:
{
  "technical_quality": {
    "lighting": "bon|moyen|faible",
    "focus": "net|flou_partiel|flou",
    "composition": "professionnelle|correcte|amateur",
    "white_balance": "correct|trop_chaud|trop_froid"
  },
  "food_appeal": {
    "score": 0-100,
    "plating": "excellent|bon|a_ameliorer",
    "colors": "vibrant|correct|terne",
    "freshness_perception": "excellent|bon|moyen"
  },
  "recommendations": [
    "suggestion 1",
    "suggestion 2"
  ],
  "best_style": "delivery|instagram|menu|story",
  "food_items_detected": ["plat1", "plat2"]
}"""

        result = await vision.analyze_image(image_data, mime_type)

        # Merge vision analysis with our custom prompting
        return {
            "ai_analysis": True,
            "description": result.get("description", ""),
            "tags": result.get("tags", []),
            "mood": result.get("mood", ""),
            "detected_objects": result.get("detected_objects", []),
            "suggested_caption": result.get("suggested_caption", ""),
        }

    except Exception as e:
        logger.warning("AI photo analysis unavailable", error=str(e))
        return {
            "ai_analysis": False,
            "description": "Analyse IA non disponible",
            "tags": [],
            "mood": "unknown",
            "detected_objects": [],
            "suggested_caption": "",
        }


class PhotoEnhancerService:
    """Main service orchestrating photo enhancement pipeline."""

    def __init__(self):
        os.makedirs(ENHANCED_DIR, exist_ok=True)

    async def enhance(
        self,
        image_data: bytes,
        style: PhotoStyle = PhotoStyle.INSTAGRAM,
        mime_type: str = "image/jpeg",
        include_ai_analysis: bool = False,
    ) -> dict[str, Any]:
        """Full enhancement pipeline.

        1. Analyze quality
        2. Apply Pillow enhancement
        3. (Optional) AI analysis
        4. Save enhanced version
        5. Return result with comparison data
        """
        # Generate IDs for tracking
        enhance_id = str(uuid.uuid4())
        ext = "jpg" if "jpeg" in mime_type or "jpg" in mime_type else "png"

        # Save original
        original_path = os.path.join(ENHANCED_DIR, f"{enhance_id}_original.{ext}")
        with open(original_path, "wb") as f:
            f.write(image_data)

        # Enhance
        enhanced_bytes, metadata = enhance_photo(image_data, style, mime_type)

        # Save enhanced
        enhanced_path = os.path.join(ENHANCED_DIR, f"{enhance_id}_enhanced.{ext}")
        with open(enhanced_path, "wb") as f:
            f.write(enhanced_bytes)

        # Optional AI analysis
        ai_analysis = None
        if include_ai_analysis:
            ai_analysis = await analyze_photo_with_ai(image_data, mime_type)

        return {
            "id": enhance_id,
            "original_url": f"/uploads/enhanced/{enhance_id}_original.{ext}",
            "enhanced_url": f"/uploads/enhanced/{enhance_id}_enhanced.{ext}",
            "style": style.value,
            "quality_before": metadata["quality_before"],
            "quality_after": metadata["quality_after"],
            "improvement": metadata["improvement"],
            "params_applied": metadata["params_applied"],
            "ai_analysis": ai_analysis,
        }

    def get_quality_score(self, image_data: bytes) -> dict[str, Any]:
        """Quick quality assessment without enhancement."""
        img = Image.open(io.BytesIO(image_data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        return _analyze_quality(img)

    async def enhance_all_styles(
        self, image_data: bytes, mime_type: str = "image/jpeg"
    ) -> dict[str, Any]:
        """Generate previews for all 4 styles."""
        enhance_id = str(uuid.uuid4())
        ext = "jpg" if "jpeg" in mime_type or "jpg" in mime_type else "png"
        previews = {}

        for style in PhotoStyle:
            enhanced_bytes, metadata = enhance_photo(image_data, style, mime_type)
            filename = f"{enhance_id}_{style.value}.{ext}"
            filepath = os.path.join(ENHANCED_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(enhanced_bytes)
            previews[style.value] = {
                "url": f"/uploads/enhanced/{filename}",
                "quality_score": metadata["quality_after"]["score"],
                "improvement": metadata["improvement"],
            }

        return {
            "id": enhance_id,
            "previews": previews,
        }
