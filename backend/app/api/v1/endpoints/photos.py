"""
PresenceOS - Photo Enhancement API (Feature 2)

Endpoints for AI-powered photo enhancement optimized for food marketing.
"""
import os
from typing import Optional

import structlog
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel

from app.services.photo_enhancer import (
    PhotoEnhancerService,
    PhotoStyle,
    PhotoQuality,
    ENHANCED_DIR,
)

logger = structlog.get_logger()
router = APIRouter()

_service: PhotoEnhancerService | None = None


def _get_service() -> PhotoEnhancerService:
    global _service
    if _service is None:
        _service = PhotoEnhancerService()
    return _service


# ── Response Models ────────────────────────────────────────

class QualityScore(BaseModel):
    score: int
    level: str
    brightness: int
    contrast: int
    color_richness: int
    resolution: int
    width: int
    height: int
    recommendation: str


class EnhanceResponse(BaseModel):
    id: str
    original_url: str
    enhanced_url: str
    style: str
    quality_before: QualityScore
    quality_after: QualityScore
    improvement: int
    params_applied: dict
    ai_analysis: Optional[dict] = None


class QualityResponse(BaseModel):
    score: int
    level: str
    brightness: int
    contrast: int
    color_richness: int
    resolution: int
    width: int
    height: int
    recommendation: str


class StylePreview(BaseModel):
    url: str
    quality_score: int
    improvement: int


class AllStylesResponse(BaseModel):
    id: str
    previews: dict[str, StylePreview]


class CompareResponse(BaseModel):
    id: str
    original_url: str
    enhanced_url: str
    quality_before: QualityScore
    quality_after: QualityScore
    improvement: int


# ── Endpoints ──────────────────────────────────────────────

@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_photo(
    file: UploadFile = File(...),
    style: PhotoStyle = Query(default=PhotoStyle.INSTAGRAM),
    ai_analysis: bool = Query(default=False, description="Include AI vision analysis"),
):
    """Enhance a food photo with the selected style preset.

    Applies professional-grade adjustments:
    - Brightness, contrast, saturation, sharpness
    - Warm amber color shift (food photography standard)
    - Style-specific parameters (delivery, instagram, menu, story)

    Returns before/after quality scores and URLs for both versions.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit etre une image")

    image_data = await file.read()
    if len(image_data) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="Image trop volumineuse (max 20MB)")

    service = _get_service()
    result = await service.enhance(
        image_data=image_data,
        style=style,
        mime_type=file.content_type,
        include_ai_analysis=ai_analysis,
    )

    return result


@router.post("/quality", response_model=QualityResponse)
async def check_quality(
    file: UploadFile = File(...),
):
    """Quick quality assessment of a photo without enhancement.

    Returns a score 0-100 with breakdown by category
    (brightness, contrast, color richness, resolution).
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit etre une image")

    image_data = await file.read()
    service = _get_service()
    return service.get_quality_score(image_data)


@router.post("/enhance/all-styles", response_model=AllStylesResponse)
async def enhance_all_styles(
    file: UploadFile = File(...),
):
    """Generate enhanced previews for all 4 style presets.

    Returns URLs for each style variant so the user can compare and choose.
    Styles: delivery, instagram, menu, story.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit etre une image")

    image_data = await file.read()
    service = _get_service()
    return await service.enhance_all_styles(image_data, file.content_type)


@router.get("/compare/{enhance_id}", response_model=CompareResponse)
async def get_comparison(enhance_id: str):
    """Get before/after comparison for a previously enhanced photo."""
    # Check for enhanced files
    for ext in ("jpg", "png"):
        original = os.path.join(ENHANCED_DIR, f"{enhance_id}_original.{ext}")
        enhanced = os.path.join(ENHANCED_DIR, f"{enhance_id}_enhanced.{ext}")
        if os.path.exists(original) and os.path.exists(enhanced):
            # Re-compute quality scores
            service = _get_service()
            with open(original, "rb") as f:
                original_data = f.read()
            with open(enhanced, "rb") as f:
                enhanced_data = f.read()

            quality_before = service.get_quality_score(original_data)
            quality_after = service.get_quality_score(enhanced_data)

            return {
                "id": enhance_id,
                "original_url": f"/uploads/enhanced/{enhance_id}_original.{ext}",
                "enhanced_url": f"/uploads/enhanced/{enhance_id}_enhanced.{ext}",
                "quality_before": quality_before,
                "quality_after": quality_after,
                "improvement": quality_after["score"] - quality_before["score"],
            }

    raise HTTPException(status_code=404, detail="Enhancement non trouve")
