"""
PresenceOS — AI Video Generation API v2

Generate videos from text or images using fal.ai (Kling 2.6 Pro / Wan 2.6).
Includes video credits management (Firebase auth).
"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.models.video_credits import VideoCredits, VideoPlan

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────


class TextToVideoRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    duration: int = Field(default=5, ge=5, le=10)
    aspect_ratio: str = Field(default="9:16", pattern="^(9:16|16:9|1:1)$")
    model: str = Field(default="kling", pattern="^(kling|wan)$")


class ImageToVideoRequest(BaseModel):
    image_url: str = Field(..., min_length=10, max_length=2000)
    prompt: str = Field(default="", max_length=1000)
    duration: int = Field(default=5, ge=5, le=10)
    aspect_ratio: str = Field(default="9:16", pattern="^(9:16|16:9|1:1)$")


class AIVideoResponse(BaseModel):
    url: str
    model: str
    duration: int
    aspect_ratio: str
    persisted: bool = True
    generated_at: str


class VideoCreditsResponse(BaseModel):
    credits_remaining: int
    credits_total: int
    plan: str
    reset_date: str | None = None


class SetCreditsRequest(BaseModel):
    credits: int = Field(ge=0, le=10000)
    plan: str = "studio"


# ── Helpers ──────────────────────────────────────────────────────────


async def _ensure_credits(brand_id: str, db) -> VideoCredits:
    """Get or create video credits for a brand."""
    bid = uuid.UUID(brand_id) if isinstance(brand_id, str) else brand_id
    result = await db.execute(
        select(VideoCredits).where(VideoCredits.brand_id == bid)
    )
    credits = result.scalar_one_or_none()

    if not credits:
        credits = VideoCredits(
            brand_id=bid,
            plan=VideoPlan.TRIAL.value,
            credits_remaining=10,
            credits_total=10,
        )
        db.add(credits)
        await db.commit()
        await db.refresh(credits)

    return credits


# ── Credits Endpoints ────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/credits",
    response_model=VideoCreditsResponse,
    summary="Get video credits for a brand",
)
async def get_credits(
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Get video credits balance."""
    await verify_brand_access(brand_id, user, db)
    credits = await _ensure_credits(brand_id, db)
    return VideoCreditsResponse(
        credits_remaining=credits.credits_remaining,
        credits_total=credits.credits_total,
        plan=credits.plan,
        reset_date=credits.reset_date.isoformat() if credits.reset_date else None,
    )


@router.put(
    "/brands/{brand_id}/credits",
    response_model=VideoCreditsResponse,
    summary="Set video credits for a brand",
)
async def set_credits(
    brand_id: str,
    body: SetCreditsRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Set video credits (admin)."""
    await verify_brand_access(brand_id, user, db)
    credits = await _ensure_credits(brand_id, db)
    credits.credits_remaining = body.credits
    credits.credits_total = body.credits
    credits.plan = body.plan
    await db.commit()
    await db.refresh(credits)
    return VideoCreditsResponse(
        credits_remaining=credits.credits_remaining,
        credits_total=credits.credits_total,
        plan=credits.plan,
        reset_date=credits.reset_date.isoformat() if credits.reset_date else None,
    )


# ── Video Generation Endpoints ───────────────────────────────────────


@router.post(
    "/brands/{brand_id}/text-to-video",
    response_model=AIVideoResponse,
    summary="Generate video from text (Kling 2.6 Pro / Wan 2.6)",
)
@limiter.limit("5/minute")
async def text_to_video(
    request: Request,
    brand_id: str,
    body: TextToVideoRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Generate a video from a text prompt using fal.ai and persist to S3."""
    await verify_brand_access(brand_id, user, db)

    from app.services.ai_video_service import AIVideoService

    try:
        svc = AIVideoService()
        result = await svc.text_to_video(
            prompt=body.prompt,
            duration=body.duration,
            aspect_ratio=body.aspect_ratio,
            brand_id=brand_id,
            model=body.model,
        )
        return AIVideoResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("text_to_video failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video generation failed: {str(exc)[:200]}",
        )


@router.post(
    "/brands/{brand_id}/image-to-video",
    response_model=AIVideoResponse,
    summary="Animate a static image into video (Kling 2.6 Pro)",
)
@limiter.limit("5/minute")
async def image_to_video(
    request: Request,
    brand_id: str,
    body: ImageToVideoRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Animate a static image into a short video using Kling 2.6 Pro."""
    await verify_brand_access(brand_id, user, db)

    from app.services.ai_video_service import AIVideoService

    try:
        svc = AIVideoService()
        result = await svc.image_to_video(
            image_url=body.image_url,
            prompt=body.prompt,
            duration=body.duration,
            aspect_ratio=body.aspect_ratio,
            brand_id=brand_id,
        )
        return AIVideoResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("image_to_video failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video animation failed: {str(exc)[:200]}",
        )
