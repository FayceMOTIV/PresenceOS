"""
PresenceOS - AI Studio API (Photo Generation)

Endpoints for AI-powered photo generation using DALL-E 3.
Named studio_ai to avoid conflict with any existing studio.py.
"""
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.photo_studio import PhotoStudio
from app.api.v1.deps import CurrentUser, DBSession

logger = structlog.get_logger()
router = APIRouter()

_photo_service: PhotoStudio | None = None


def _get_photo_service() -> PhotoStudio:
    global _photo_service
    if _photo_service is None:
        _photo_service = PhotoStudio()
    return _photo_service


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
        description="Business niche: restaurant, hotel, beauty_salon, fitness, retail",
    )


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/generate")
async def generate_photo(
    request: GeneratePhotoRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Generate a single marketing photo using DALL-E 3.

    Enhances the base prompt with niche-specific context and the chosen
    visual style before sending to DALL-E 3 (HD quality).

    Returns the generated image URL along with metadata.
    """
    service = _get_photo_service()

    try:
        result = await service.generate_photo(
            prompt=request.prompt,
            niche=request.niche,
            style=request.style,
            size=request.size,
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

    Returns a dict with a 'variations' list, each entry containing the
    image URL and its associated style metadata.
    """
    service = _get_photo_service()

    try:
        variations = await service.generate_variations(
            base_prompt=request.prompt,
            niche=request.niche,
            count=4,
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
