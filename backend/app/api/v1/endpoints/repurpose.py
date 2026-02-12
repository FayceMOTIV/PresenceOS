"""
PresenceOS — Content Repurposing API (Feature 4)

Endpoints for transforming one piece of content into multiple platform-adapted formats.
"""
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.content_repurposer import ContentRepurposerService

logger = structlog.get_logger()
router = APIRouter()

_service: ContentRepurposerService | None = None


def _get_service() -> ContentRepurposerService:
    global _service
    if _service is None:
        _service = ContentRepurposerService()
    return _service


# ── Request/Response Models ────────────────────────────────

class RepurposeRequest(BaseModel):
    brand_id: str
    caption: str
    hashtags: list[str] = []
    media_urls: list[str] = []
    target_formats: Optional[list[str]] = None


class VariantResponse(BaseModel):
    id: str
    format: str
    label: str
    caption: str
    hashtags: list[str]
    hashtag_text: str
    suggested_cta: str
    media_urls: list[str]
    crop_spec: dict
    tone: str
    platform_tips: str


class PackageResponse(BaseModel):
    id: str
    brand_id: str
    original: dict
    variants: list[VariantResponse]
    variant_count: int
    created_at: str


# ── Endpoints ──────────────────────────────────────────────

@router.post("/repurpose", response_model=PackageResponse)
async def repurpose_content(request: RepurposeRequest):
    """Transform one piece of content into multiple platform-adapted formats.

    Generates up to 7 variants (Instagram Post, Reel, Story, TikTok,
    Facebook, GBP, LinkedIn) with adapted captions, hashtags, CTAs,
    and media crop specifications.
    """
    service = _get_service()
    result = service.repurpose(
        brand_id=request.brand_id,
        original_caption=request.caption,
        original_hashtags=request.hashtags,
        original_media_urls=request.media_urls,
        target_formats=request.target_formats,
    )
    return result


@router.get("/package/{package_id}", response_model=PackageResponse)
async def get_package(package_id: str):
    """Retrieve a previously generated content package."""
    service = _get_service()
    result = service.get_package(package_id)
    if not result:
        raise HTTPException(status_code=404, detail="Package non trouve")
    return result


@router.get("/formats")
async def get_formats():
    """Get all available output format specifications.

    Useful for the frontend to display format options and constraints.
    """
    service = _get_service()
    return service.get_format_specs()
