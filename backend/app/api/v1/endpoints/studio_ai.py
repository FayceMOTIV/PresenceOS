"""
PresenceOS - AI Studio API (Photo Generation)

Endpoints for AI-powered photo generation using DALL-E 3.
Named studio_ai to avoid conflict with any existing studio.py.

When a brand_id is provided, the brand name is injected into DALL-E
prompts so the visual aesthetic matches the brand identity.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.photo_studio import PhotoStudio
from app.api.v1.deps import CurrentUser, DBSession
from app.models.brand import Brand

logger = structlog.get_logger()
router = APIRouter()

_photo_service: PhotoStudio | None = None


def _get_photo_service() -> PhotoStudio:
    global _photo_service
    if _photo_service is None:
        _photo_service = PhotoStudio()
    return _photo_service


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _get_brand_name(db: AsyncSession, brand_id: UUID) -> str | None:
    """Load just the brand name for DALL-E prompt context."""
    result = await db.execute(
        select(Brand.name).where(Brand.id == brand_id)
    )
    return result.scalar_one_or_none()


# ── Request / Response Models ───────────────────────────────────────────────


class GeneratePhotoRequest(BaseModel):
    prompt: str = Field(..., description="Description of the desired image")
    style: str = Field(
        default="natural",
        description="Visual style: natural, cinematic, vibrant, minimalist",
    )
    size: str = Field(
        default="1024x1024",
        description="Image dimensions: 1024x1024, 1792x1024, 1024x1792",
    )
    niche: str = Field(
        default="restaurant",
        description="Business niche (see GET /niches for full list)",
    )
    brand_id: UUID | None = Field(
        default=None,
        description="Optional brand ID — injects brand name into DALL-E prompt",
    )


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/niches")
async def list_niches() -> dict:
    """Return the list of supported business niches for photo generation.

    Each entry has an id (for API calls) and a label (for display).
    """
    return {"niches": PhotoStudio.get_supported_niches()}


@router.post("/generate")
async def generate_photo(
    request: GeneratePhotoRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Generate a single marketing photo using DALL-E 3.

    Enhances the base prompt with niche-specific context and the chosen
    visual style before sending to DALL-E 3 (HD quality).

    When brand_id is provided, the brand name is used to match
    the visual aesthetic and sophistication level.

    Returns the generated image URL along with metadata.
    """
    service = _get_photo_service()

    # Resolve brand name if brand_id provided
    brand_name: str | None = None
    if request.brand_id:
        brand_name = await _get_brand_name(db, request.brand_id)

    try:
        result = await service.generate_photo(
            prompt=request.prompt,
            niche=request.niche,
            style=request.style,
            size=request.size,
            brand_name=brand_name,
        )
    except RuntimeError as exc:
        logger.error(
            "Photo generation configuration error",
            user_id=str(current_user.id),
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Photo generation failed",
            user_id=str(current_user.id),
            niche=request.niche,
            style=request.style,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Photo generation failed: {str(exc)}",
        )

    return result


@router.post("/generate-variations")
async def generate_variations(
    request: GeneratePhotoRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Generate 4 photo variations across all available visual styles.

    Runs all 4 DALL-E 3 generations in parallel (natural, cinematic,
    vibrant, minimalist) for the given prompt and niche.

    When brand_id is provided, the brand name is used in all 4 prompts.

    Returns a dict with a 'variations' list, each entry containing the
    image URL and its associated style metadata.
    """
    service = _get_photo_service()

    # Resolve brand name if brand_id provided
    brand_name: str | None = None
    if request.brand_id:
        brand_name = await _get_brand_name(db, request.brand_id)

    try:
        variations = await service.generate_variations(
            base_prompt=request.prompt,
            niche=request.niche,
            count=4,
            brand_name=brand_name,
        )
    except RuntimeError as exc:
        logger.error(
            "Photo variations configuration error",
            user_id=str(current_user.id),
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Photo variations generation failed",
            user_id=str(current_user.id),
            niche=request.niche,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Photo variations generation failed: {str(exc)}",
        )

    return {"variations": variations}
