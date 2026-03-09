"""
PresenceOS — Video Templates API v2

Templates:
  - Breakout V4: Photo -> rembg -> Remotion 3-layer -> MP4 ($0.00)
  - Cinematic Food: Photo -> Kling 2.6 Pro image-to-video ($0.35/5s)
"""

import asyncio
import logging
import os
import tempfile

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Response Models ──────────────────────────────────────────────────────


class BreakoutV4PrepareResponse(BaseModel):
    status: str = "ready"
    original_url: str
    cutout_url: str


class BreakoutV4RenderRequest(BaseModel):
    original_url: str = Field(..., min_length=10)
    cutout_url: str = Field(..., min_length=10)
    business_name: str = Field(default="Mon Restaurant", max_length=100)
    instagram_handle: str = Field(default="@monrestaurant", max_length=100)
    caption: str = Field(default="", max_length=500)
    accent_color: str = Field(default="#F59E0B", max_length=20)


class BreakoutV4RenderResponse(BaseModel):
    status: str = "done"
    video_url: str
    duration_seconds: int = 3
    template: str = "breakout_v4"
    cost_usd: float = 0.0
    original_url: str | None = None
    cutout_url: str | None = None


class CinematicFoodResponse(BaseModel):
    status: str = "done"
    video_url: str
    template: str = "cinematic_food"
    food_type: str
    duration: int
    aspect_ratio: str = "9:16"
    cost_usd: float


class CinematicPricingResponse(BaseModel):
    model: str = "kling-2.6-pro"
    provider: str = "fal.ai"
    pricing: dict
    recommended: str = "5s_no_audio"


# ── BREAKOUT V4 ──────────────────────────────────────────────────────────


@router.post(
    "/breakout-v4/brands/{brand_id}/prepare",
    response_model=BreakoutV4PrepareResponse,
    summary="Upload photo -> rembg cutout (~5s)",
)
@limiter.limit("10/minute")
async def prepare_breakout_v4(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    photo: UploadFile = File(...),
):
    """
    Step 1: Upload photo -> background removal -> return preview assets.
    Fast (~3-5s). Preview before launching the render.
    """
    await verify_brand_access(brand_id, user, db)

    content_type = photo.content_type or ""
    allowed_types = ("image/jpeg", "image/png", "image/heic", "image/heif", "image/webp")
    if not any(content_type.startswith(t) for t in allowed_types):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit etre une image (JPEG, PNG, HEIC, WebP)",
        )

    contents = await photo.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image trop volumineuse (max 20 Mo)",
        )

    # Normalize HEIC/WebP/PNG -> JPEG
    from app.utils.normalize_image import normalize_image
    contents = await asyncio.to_thread(normalize_image, contents)

    # Upload to fal.ai to get a public URL for the engine
    from app.core.config import settings
    import fal_client

    fal_key = settings.fal_key
    if fal_key:
        os.environ["FAL_KEY"] = fal_key

    def _upload():
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(contents)
            tmp = f.name
        try:
            return fal_client.upload_file(tmp)
        finally:
            os.unlink(tmp)

    image_url = await asyncio.to_thread(_upload)

    # Run prepare (rembg + upload assets)
    from app.services.breakout.breakout_v4_engine import BreakoutV4Engine

    engine = BreakoutV4Engine()
    try:
        assets = await engine.prepare(image_url=image_url, brand_id=brand_id)
    except Exception as exc:
        logger.error("Breakout V4 prepare failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Background removal echouee: {str(exc)[:200]}",
        )

    return BreakoutV4PrepareResponse(
        original_url=assets["original_url"],
        cutout_url=assets["cutout_url"],
    )


@router.post(
    "/breakout-v4/brands/{brand_id}/render",
    response_model=BreakoutV4RenderResponse,
    summary="Render BreakoutV4 Remotion template (~30-45s)",
)
@limiter.limit("5/minute")
async def render_breakout_v4(
    request: Request,
    brand_id: str,
    body: BreakoutV4RenderRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """
    Step 2: Remotion render BreakoutV4 composition.
    Takes ~30-45s. Returns S3 permanent video URL.
    """
    await verify_brand_access(brand_id, user, db)

    from app.services.breakout.breakout_v4_engine import BreakoutV4Engine

    engine = BreakoutV4Engine()
    try:
        result = await engine.render(
            original_url=body.original_url,
            cutout_url=body.cutout_url,
            brand_id=brand_id,
            business_name=body.business_name,
            instagram_handle=body.instagram_handle,
            caption=body.caption,
            accent_color=body.accent_color,
        )
    except Exception as exc:
        logger.error("Breakout V4 render failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Render echoue: {str(exc)[:200]}",
        )

    return BreakoutV4RenderResponse(
        video_url=result["video_url"],
        duration_seconds=result["duration_seconds"],
        original_url=result.get("original_url"),
        cutout_url=result.get("cutout_url"),
    )


@router.post(
    "/breakout-v4/brands/{brand_id}/generate",
    response_model=BreakoutV4RenderResponse,
    summary="Full Breakout V4 pipeline: photo -> MP4 (~35-45s)",
)
@limiter.limit("5/minute")
async def generate_breakout_v4_full(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    photo: UploadFile = File(...),
    business_name: str = Form(default="Mon Restaurant"),
    instagram_handle: str = Form(default="@monrestaurant"),
    caption: str = Form(default=""),
    accent_color: str = Form(default="#F59E0B"),
):
    """
    Full pipeline in one call: photo -> rembg -> Remotion -> MP4.
    ~35-45s response time. No polling needed.
    """
    await verify_brand_access(brand_id, user, db)

    contents = await photo.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image trop volumineuse (max 20 Mo)",
        )

    from app.utils.normalize_image import normalize_image
    contents = await asyncio.to_thread(normalize_image, contents)

    from app.core.config import settings
    import fal_client

    fal_key = settings.fal_key
    if fal_key:
        os.environ["FAL_KEY"] = fal_key

    def _upload():
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(contents)
            tmp = f.name
        try:
            return fal_client.upload_file(tmp)
        finally:
            os.unlink(tmp)

    image_url = await asyncio.to_thread(_upload)

    from app.services.breakout.breakout_v4_engine import BreakoutV4Engine

    engine = BreakoutV4Engine()
    try:
        result = await engine.generate_v4(
            image_url=image_url,
            brand_id=brand_id,
            business_name=business_name,
            instagram_handle=instagram_handle,
            caption=caption,
            accent_color=accent_color,
        )
    except Exception as exc:
        logger.error("Breakout V4 full failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation echouee: {str(exc)[:200]}",
        )

    return BreakoutV4RenderResponse(
        video_url=result["video_url"],
        duration_seconds=result["duration_seconds"],
        original_url=result.get("original_url"),
        cutout_url=result.get("cutout_url"),
    )


# ── CINEMATIC FOOD ───────────────────────────────────────────────────────


@router.post(
    "/cinematic/brands/{brand_id}/generate",
    response_model=CinematicFoodResponse,
    summary="Photo -> cinematic food video (Kling 2.6 Pro, ~60-90s)",
)
@limiter.limit("5/minute")
async def generate_cinematic_food(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    photo: UploadFile = File(...),
    food_type: str = Form(default="default"),
    duration: int = Form(default=5),
    aspect_ratio: str = Form(default="9:16"),
):
    """
    Upload a food photo -> Kling 2.6 Pro generates a cinematic video.

    food_type: "default" | "burger" | "pizza" | "dessert" | "drink"
    duration: 5 ($0.35) or 10 ($0.70) seconds
    Time: ~60-90s
    """
    await verify_brand_access(brand_id, user, db)

    # Validate
    if duration not in (5, 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="duration must be 5 or 10",
        )

    from app.services.cinematic_food_service import VALID_FOOD_TYPES
    if food_type not in VALID_FOOD_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"food_type must be one of: {', '.join(sorted(VALID_FOOD_TYPES))}",
        )

    if aspect_ratio not in ("9:16", "1:1", "16:9"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="aspect_ratio must be 9:16, 1:1, or 16:9",
        )

    content_type = photo.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit etre une image",
        )

    contents = await photo.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image trop volumineuse (max 20 Mo)",
        )

    # Upload source image to S3 first (needed as public URL for Kling)
    from app.services.storage import get_storage_service
    storage = get_storage_service()

    # Determine content type
    ct = "image/jpeg"
    if content_type.startswith("image/png"):
        ct = "image/png"
    elif content_type.startswith("image/webp"):
        ct = "image/webp"

    key = storage.generate_key(
        brand_id=brand_id or "ai-studio",
        media_type="image",
        original_filename=f"cinematic_input_{food_type}.jpg",
    )
    upload_result = await storage.upload_bytes(data=contents, key=key, content_type=ct)
    image_url = upload_result["url"]

    # Generate video
    from app.services.cinematic_food_service import CinematicFoodService

    try:
        svc = CinematicFoodService()
        result = await svc.generate(
            image_url=image_url,
            brand_id=brand_id,
            food_type=food_type,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Video generation timed out (>120s)",
        )
    except Exception as exc:
        logger.error("Cinematic food failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation echouee: {str(exc)[:200]}",
        )

    return CinematicFoodResponse(
        video_url=result["video_url"],
        food_type=result["food_type"],
        duration=result["duration"],
        aspect_ratio=result.get("aspect_ratio", "9:16"),
        cost_usd=result["cost_usd"],
    )


@router.post(
    "/cinematic/brands/{brand_id}/from-url",
    response_model=CinematicFoodResponse,
    summary="Image URL -> cinematic food video (no upload needed)",
)
@limiter.limit("5/minute")
async def generate_cinematic_from_url(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    image_url: str = Form(...),
    food_type: str = Form(default="default"),
    duration: int = Form(default=5),
    aspect_ratio: str = Form(default="9:16"),
):
    """Generate cinematic video from an existing image URL (S3, media library)."""
    await verify_brand_access(brand_id, user, db)

    if duration not in (5, 10):
        raise HTTPException(status_code=400, detail="duration must be 5 or 10")

    from app.services.cinematic_food_service import VALID_FOOD_TYPES, CinematicFoodService
    if food_type not in VALID_FOOD_TYPES:
        raise HTTPException(status_code=400, detail=f"food_type invalide")

    try:
        svc = CinematicFoodService()
        result = await svc.generate(
            image_url=image_url,
            brand_id=brand_id,
            food_type=food_type,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Cinematic from-url failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Generation echouee: {str(exc)[:200]}")

    return CinematicFoodResponse(
        video_url=result["video_url"],
        food_type=result["food_type"],
        duration=result["duration"],
        aspect_ratio=result.get("aspect_ratio", "9:16"),
        cost_usd=result["cost_usd"],
    )


@router.get(
    "/cinematic/pricing",
    response_model=CinematicPricingResponse,
    summary="Kling 2.6 Pro pricing info",
)
async def get_cinematic_pricing():
    """Return Kling 2.6 Pro pricing for cinematic food videos."""
    return CinematicPricingResponse(
        pricing={
            "5s_no_audio": 0.35,
            "5s_with_audio": 0.70,
            "10s_no_audio": 0.70,
            "10s_with_audio": 1.40,
        },
    )
