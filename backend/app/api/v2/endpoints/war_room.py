"""
PresenceOS - War Room v2 Endpoints

Ilyas analyse n'importe quoi (URL, image, audio, texte) et retourne un plan stratégique.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.data.niches import detect_niche
from app.middleware.rate_limit import limiter
from app.services.strategic_analyzer import strategic_analyzer

logger = structlog.get_logger()
router = APIRouter()


# ── Helpers ──


async def _get_context(brand_id: UUID, user: "FirebaseUser", db: "DBSession") -> tuple:
    """Récupère brand_context + niche_profile depuis la DB."""
    brand = await verify_brand_access(str(brand_id), user, db)

    business_type = (
        getattr(brand, "business_type", None)
        or getattr(brand, "category", None)
        or "restaurant"
    )
    niche = detect_niche(business_type)
    brand_context = {
        "id": str(brand_id),
        "name": brand.name,
        "description": getattr(brand, "description", ""),
    }
    return brand_context, niche


# ── Request models ──


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=5)


class AnalyzeUrlRequest(BaseModel):
    url: str = Field(...)


# ── Endpoints ──


@router.post("/{brand_id}/analyze-url")
@limiter.limit("10/minute")
async def analyze_url(
    request: Request,
    brand_id: UUID,
    body: AnalyzeUrlRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Analyse une URL (TikTok concurrent, article tendance, site web)."""
    if not body.url.startswith("http"):
        raise HTTPException(400, "URL invalide — doit commencer par http:// ou https://")

    brand_context, niche = await _get_context(brand_id, current_user, db)

    try:
        result = await strategic_analyzer.analyze_url(body.url, brand_context, niche)
        return {"status": "ok", "input_type": "url", "analysis": result}
    except Exception as e:
        logger.error("war_room_url_error", error=str(e))
        raise HTTPException(500, f"Analyse échouée : {str(e)}")


@router.post("/{brand_id}/analyze-image")
@limiter.limit("10/minute")
async def analyze_image(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
    note: str = Form(""),
    image: UploadFile = File(...),
) -> dict:
    """Analyse une image (photo plat, screenshot, inspiration)."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Le fichier doit être une image (jpg, png, webp)")

    image_bytes = await image.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(400, "Image trop grande (max 20MB)")

    brand_context, niche = await _get_context(brand_id, current_user, db)

    try:
        result = await strategic_analyzer.analyze_image(
            image_bytes, brand_context, niche, note
        )
        return {"status": "ok", "input_type": "image", "analysis": result}
    except Exception as e:
        logger.error("war_room_image_error", error=str(e))
        raise HTTPException(500, f"Analyse image échouée : {str(e)}")


@router.post("/{brand_id}/analyze-audio")
@limiter.limit("10/minute")
async def analyze_audio(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
    audio: UploadFile = File(...),
) -> dict:
    """Transcrit et analyse un vocal."""
    audio_bytes = await audio.read()
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(400, "Audio trop grand (max 25MB)")

    brand_context, niche = await _get_context(brand_id, current_user, db)

    try:
        result = await strategic_analyzer.analyze_audio(
            audio_bytes, brand_context, niche
        )
        return {"status": "ok", "input_type": "audio", "analysis": result}
    except Exception as e:
        logger.error("war_room_audio_error", error=str(e))
        raise HTTPException(500, f"Analyse audio échouée : {str(e)}")


@router.post("/{brand_id}/analyze-text")
@limiter.limit("20/minute")
async def analyze_text(
    request: Request,
    brand_id: UUID,
    body: AnalyzeTextRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Analyse un texte libre (retour client, idée, observation)."""
    brand_context, niche = await _get_context(brand_id, current_user, db)

    try:
        result = await strategic_analyzer.analyze_text(
            body.text.strip(), brand_context, niche
        )
        return {"status": "ok", "input_type": "text", "analysis": result}
    except Exception as e:
        logger.error("war_room_text_error", error=str(e))
        raise HTTPException(500, f"Analyse texte échouée : {str(e)}")
