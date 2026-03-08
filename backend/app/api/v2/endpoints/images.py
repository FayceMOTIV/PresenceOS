"""
PresenceOS — Image Generation API v2

Gemini Image generation + photo enhancement.
Replaces DALL-E 3 / GPT-Image-1 endpoints.
"""
import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    niche: str = Field(default="restaurant", max_length=50)
    style: str = Field(default="natural", max_length=50)
    quality: str = Field(default="fast", pattern="^(fast|pro)$")
    brand_name: str | None = Field(default=None, max_length=200)


class EnhanceImageRequest(BaseModel):
    source_url: str = Field(..., min_length=10, max_length=2000)
    style: str = Field(default="restaurant", max_length=50)


class ImageResponse(BaseModel):
    url: str
    model: str
    quality: str | None = None
    style: str | None = None
    persisted: bool = True
    generated_at: str


# ── Endpoints ────────────────────────────────────────────────────────


@router.post(
    "/brands/{brand_id}/generate",
    response_model=ImageResponse,
    summary="Generate a marketing image (Gemini Image)",
)
@limiter.limit("10/minute")
async def generate_image(
    request: Request,
    brand_id: str,
    body: GenerateImageRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Generate a food/marketing image using Gemini Image and persist to S3."""
    await verify_brand_access(brand_id, user, db)

    from app.services.image_service import ImageService

    svc = ImageService()

    try:
        result = await svc.generate_food_image(
            dish_name=body.prompt,
            description=f"Style: {body.style}. Niche: {body.niche}.",
            brand_id=brand_id,
            quality=body.quality,
        )
        return ImageResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("generate_image failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(exc)[:200]}",
        )


@router.post(
    "/brands/{brand_id}/enhance",
    response_model=ImageResponse,
    summary="Enhance an existing photo (Gemini Pro)",
)
@limiter.limit("5/minute")
async def enhance_image(
    request: Request,
    brand_id: str,
    body: EnhanceImageRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Enhance an existing food photo using Gemini Pro and persist to S3."""
    await verify_brand_access(brand_id, user, db)

    from app.services.image_service import ImageService

    svc = ImageService()

    try:
        result = await svc.enhance_food_photo(
            source_url=body.source_url,
            brand_id=brand_id,
            style=body.style,
        )
        return ImageResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("enhance_image failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image enhancement failed: {str(exc)[:200]}",
        )


@router.get(
    "/niches",
    summary="List supported business niches",
)
async def list_niches(user: FirebaseUser):
    """Return the list of supported business niches for image generation."""
    from app.ai.photo_studio import PhotoStudio

    return {"niches": PhotoStudio.get_supported_niches()}
