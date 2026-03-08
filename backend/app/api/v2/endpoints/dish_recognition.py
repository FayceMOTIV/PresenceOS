"""
PresenceOS — Dish Recognition API v2

Upload a food photo → Gemini Vision identifies dish name, category, description.
Used in mobile upload flow to auto-fill dish info.
"""

import asyncio

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, status
from pydantic import BaseModel

from app.api.v2.deps import FirebaseUser
from app.middleware.rate_limit import limiter

router = APIRouter()


class DishRecognitionResponse(BaseModel):
    dish_name: str
    category: str
    description: str
    confidence: float
    tags: list[str]


@router.post(
    "/recognize",
    response_model=DishRecognitionResponse,
    summary="Recognize dish from photo (Gemini Vision)",
)
@limiter.limit("20/minute")
async def recognize_dish(
    request: Request,
    user: FirebaseUser,
    photo: UploadFile = File(...),
):
    """Upload a food photo → returns dish name, category, description."""
    content_type = photo.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit etre une image",
        )

    contents = await photo.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image trop volumineuse (max 10 Mo)",
        )

    # Normalize HEIC/WebP → JPEG
    from app.utils.normalize_image import normalize_image

    contents = await asyncio.to_thread(normalize_image, contents)

    from app.services.dish_recognition_service import DishRecognitionService

    service = DishRecognitionService()

    try:
        result = await service.recognize(contents)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconnaissance echouee: {str(exc)[:200]}",
        )

    return DishRecognitionResponse(**result.to_dict())
