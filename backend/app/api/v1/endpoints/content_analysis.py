"""
PresenceOS - Content Analysis Endpoints

Analyze Instagram content to extract brand tone and vocabulary.
Uses free tier LLM (OpenRouter / Llama 3.3 70B).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import CurrentUser, DBSession, get_brand, CurrentBrand
from app.services.content_analyzer_free import ContentAnalyzerFree

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    instagram_username: str


class ToneResult(BaseModel):
    tone_formal: int
    tone_playful: int
    tone_bold: int
    tone_emotional: int
    humor_level: int


class VocabularyResult(BaseModel):
    favorite_words: list[str] = []
    favorite_emojis: list[str] = []
    cta_style: str = ""
    sentence_style: str = ""
    hashtag_style: str = ""
    words_to_prefer: list[str] = []


class StoredResult(BaseModel):
    voice_updated: bool = False
    knowledge_items_created: int = 0


class AnalyzeResponse(BaseModel):
    success: bool
    posts_found: int = 0
    posts_analyzed: int = 0
    summary: str = ""
    tone: ToneResult | None = None
    vocabulary: VocabularyResult | None = None
    stored: StoredResult | None = None
    custom_instructions: str = ""
    error: str | None = None


# ── Endpoints ───────────────────────────────────────────────

@router.post(
    "/brands/{brand_id}/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze Instagram content for brand tone",
)
async def analyze_instagram_content(
    brand_id: UUID,
    request: AnalyzeRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Analyze an Instagram account's content to extract:
    - Tone metrics (formal, playful, bold, emotional, humor)
    - Vocabulary patterns (favorite words, emojis, CTA style)

    Results are stored in BrandVoice and KnowledgeItems.
    """
    # Validate brand access
    brand = await get_brand(brand_id, current_user, db)

    username = request.instagram_username.strip().lstrip("@")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram username is required",
        )

    analyzer = ContentAnalyzerFree()
    result = await analyzer.analyze_and_store(username, brand, db)

    if not result.get("success"):
        return AnalyzeResponse(
            success=False,
            error=result.get("error", "Erreur inconnue"),
        )

    return AnalyzeResponse(
        success=True,
        posts_found=result["posts_found"],
        posts_analyzed=result["posts_analyzed"],
        summary=result["summary"],
        tone=ToneResult(**result["tone"]),
        vocabulary=VocabularyResult(**result["vocabulary"]),
        stored=StoredResult(**result["stored"]),
        custom_instructions=result.get("custom_instructions", ""),
    )


@router.get(
    "/brands/{brand_id}/status",
    summary="Get content analysis status for a brand",
)
async def get_analysis_status(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Check if a brand has been analyzed and return current voice config."""
    brand = await get_brand(brand_id, current_user, db)

    has_voice = brand.voice is not None
    voice_data = None
    if brand.voice:
        voice_data = {
            "tone_formal": brand.voice.tone_formal,
            "tone_playful": brand.voice.tone_playful,
            "tone_bold": brand.voice.tone_bold,
            "tone_emotional": brand.voice.tone_emotional,
            "words_to_prefer": brand.voice.words_to_prefer or [],
            "words_to_avoid": brand.voice.words_to_avoid or [],
            "emojis_allowed": brand.voice.emojis_allowed or [],
            "custom_instructions": brand.voice.custom_instructions or "",
        }

    return {
        "has_voice": has_voice,
        "voice": voice_data,
        "brand_name": brand.name,
    }
