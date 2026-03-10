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


STYLE_MODIFIERS = {
    "cinematic": "cinematic lighting, shallow depth of field, film grain, warm tones, professional food photography style",
    "natural": "natural daylight, authentic, candid restaurant atmosphere, soft shadows, realistic",
    "vibrant": "vibrant saturated colors, high contrast, energetic, social media optimized, eye-catching",
    "minimal": "clean minimalist aesthetic, muted palette, simple composition, elegant, modern",
}


def _credits_for_duration(duration: int) -> int:
    if duration <= 5:
        return 1
    if duration <= 10:
        return 2
    return 3


class TextToVideoRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    duration: int = Field(default=5, ge=5, le=10)
    aspect_ratio: str = Field(default="9:16", pattern="^(9:16|16:9|1:1)$")
    model: str = Field(default="kling", pattern="^(kling|wan)$")


class GenerateVideoRequest(BaseModel):
    """V1-compatible generate request with style + credit check."""
    prompt: str = Field(..., min_length=5, max_length=1000)
    duration: int = Field(default=5)
    style: str = Field(default="cinematic")
    aspect_ratio: str = Field(default="9:16")


class GenerateVideoResponse(BaseModel):
    video_url: str | None
    duration: int
    credits_used: int
    credits_remaining: int
    status: str


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


@router.post(
    "/brands/{brand_id}/generate",
    response_model=GenerateVideoResponse,
    summary="Generate video with credits + style (replaces V1 /video/generate)",
)
@limiter.limit("5/minute")
async def generate_video(
    request: Request,
    brand_id: str,
    body: GenerateVideoRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Generate video from text with credit check + style modifiers."""
    await verify_brand_access(brand_id, user, db)

    if body.duration not in (5, 10, 15):
        raise HTTPException(status_code=400, detail="Duration must be 5, 10, or 15 seconds")
    if body.style not in STYLE_MODIFIERS:
        raise HTTPException(status_code=400, detail=f"Style must be one of: {', '.join(STYLE_MODIFIERS.keys())}")

    credits = await _ensure_credits(brand_id, db)
    needed = _credits_for_duration(body.duration)

    if credits.credits_remaining < needed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Crédits insuffisants. {needed} requis, {credits.credits_remaining} restants.",
        )

    from app.core.config import settings

    fal_key = getattr(settings, "fal_key", "") or ""
    if not fal_key:
        return GenerateVideoResponse(
            video_url=None, duration=body.duration,
            credits_used=0, credits_remaining=credits.credits_remaining,
            status="no_api_key",
        )

    style_mod = STYLE_MODIFIERS[body.style]
    enhanced_prompt = f"{body.prompt}. {style_mod}"

    try:
        import os
        os.environ["FAL_KEY"] = fal_key
        import fal_client

        result = await fal_client.subscribe_async(
            "fal-ai/kling-video/v2.6/pro/text-to-video",
            arguments={
                "prompt": enhanced_prompt,
                "duration": str(body.duration),
                "aspect_ratio": body.aspect_ratio,
            },
        )

        video_url = result.get("video", {}).get("url") if isinstance(result, dict) else None

        if not video_url:
            return GenerateVideoResponse(
                video_url=None, duration=body.duration,
                credits_used=0, credits_remaining=credits.credits_remaining,
                status="failed",
            )

        credits.credits_remaining -= needed
        await db.commit()

        logger.info("video_generated", brand_id=brand_id, duration=body.duration, credits_used=needed)

        return GenerateVideoResponse(
            video_url=video_url, duration=body.duration,
            credits_used=needed, credits_remaining=credits.credits_remaining,
            status="completed",
        )

    except Exception as exc:
        logger.error("generate_video failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Échec de la génération vidéo : {str(exc)[:200]}")
