"""
PresenceOS - AI Generation Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_brand

# Rate limiter for AI endpoints (20 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)
from app.models.brand import Brand, KnowledgeItem
from app.models.content import ContentIdea, ContentDraft, ContentVariant, IdeaSource, IdeaStatus, DraftStatus
from app.schemas.content import (
    GenerateIdeasRequest,
    GenerateIdeasResponse,
    GeneratedIdea,
    GenerateDraftRequest,
    GenerateDraftResponse,
    GeneratedDraft,
    GeneratedVariant,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    ContentIdeaResponse,
    ContentDraftResponse,
)
from app.prompts.caption_generator import PROMPT_VERSION
from app.services.ai_service import AIService
from app.services.embeddings import EmbeddingService

router = APIRouter()


@router.post("/brands/{brand_id}/ideas/generate", response_model=GenerateIdeasResponse)
@limiter.limit("20/minute")
async def generate_ideas(
    request: Request,
    brand_id: UUID,
    data: GenerateIdeasRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Generate content ideas using AI."""
    brand = await get_brand(brand_id, current_user, db)

    # Load brand with voice
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one()

    ai_service = AIService()

    ideas = await ai_service.generate_ideas(
        brand=brand,
        count=data.count,
        content_pillars=data.content_pillars,
        platforms=[p.value for p in data.platforms] if data.platforms else None,
        context=data.context,
        date_range=(data.date_range_start, data.date_range_end),
    )

    return GenerateIdeasResponse(
        ideas=ideas,
        model_used=ai_service.model_name,
        prompt_version=PROMPT_VERSION,
    )


@router.post("/brands/{brand_id}/ideas/save", response_model=list[ContentIdeaResponse])
async def save_generated_ideas(
    brand_id: UUID,
    ideas: list[GeneratedIdea],
    current_user: CurrentUser,
    db: DBSession,
):
    """Save generated ideas to the database."""
    await get_brand(brand_id, current_user, db)

    saved_ideas = []
    for idea_data in ideas:
        idea = ContentIdea(
            brand_id=brand_id,
            title=idea_data.title,
            description=idea_data.description,
            source=IdeaSource.AI_GENERATED,
            status=IdeaStatus.NEW,
            content_pillar=idea_data.content_pillar,
            target_platforms=idea_data.target_platforms,
            hooks=idea_data.hooks,
            ai_reasoning=idea_data.ai_reasoning,
            suggested_date=idea_data.suggested_date,
        )
        db.add(idea)
        saved_ideas.append(idea)

    await db.commit()

    # Refresh all
    for idea in saved_ideas:
        await db.refresh(idea)

    return [ContentIdeaResponse.model_validate(idea) for idea in saved_ideas]


@router.post("/brands/{brand_id}/drafts/generate", response_model=GenerateDraftResponse)
@limiter.limit("20/minute")
async def generate_draft(
    request: Request,
    brand_id: UUID,
    data: GenerateDraftRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Generate a content draft using AI."""
    brand = await get_brand(brand_id, current_user, db)

    # Load brand with voice
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one()

    # Get idea context if provided
    idea_context = None
    if data.idea_id:
        idea_result = await db.execute(
            select(ContentIdea).where(ContentIdea.id == data.idea_id)
        )
        idea = idea_result.scalar_one_or_none()
        if idea:
            idea_context = {
                "title": idea.title,
                "description": idea.description,
                "hooks": idea.hooks,
                "content_pillar": idea.content_pillar,
            }

    # Get relevant knowledge via RAG
    embedding_service = EmbeddingService()
    topic = data.topic or (idea_context["title"] if idea_context else "")

    relevant_knowledge = []
    if topic:
        try:
            query_embedding = await embedding_service.generate_embedding(topic)
            knowledge_result = await db.execute(
                select(KnowledgeItem)
                .where(
                    KnowledgeItem.brand_id == brand_id,
                    KnowledgeItem.is_active == True,
                    KnowledgeItem.embedding.isnot(None),
                )
                .order_by(KnowledgeItem.embedding.cosine_distance(query_embedding))
                .limit(5)
            )
            relevant_knowledge = [
                {"title": k.title, "content": k.content, "type": k.knowledge_type.value}
                for k in knowledge_result.scalars().all()
            ]
        except Exception:
            pass  # Continue without RAG if it fails

    ai_service = AIService()

    draft, variants = await ai_service.generate_draft(
        brand=brand,
        platform=data.platform,
        topic=data.topic,
        idea_context=idea_context,
        relevant_knowledge=relevant_knowledge,
        media_urls=data.media_urls,
        generate_variants=data.generate_variants,
        variant_styles=[s.value for s in data.variant_styles],
        additional_instructions=data.additional_instructions,
    )

    return GenerateDraftResponse(
        draft=draft,
        variants=variants,
        model_used=ai_service.model_name,
        prompt_version=PROMPT_VERSION,
    )


@router.post("/brands/{brand_id}/drafts/save", response_model=ContentDraftResponse)
async def save_generated_draft(
    brand_id: UUID,
    draft_data: GenerateDraftResponse,
    idea_id: UUID | None = None,
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Save a generated draft and its variants to the database."""
    await get_brand(brand_id, current_user, db)

    draft = ContentDraft(
        brand_id=brand_id,
        idea_id=idea_id,
        platform=draft_data.draft.platform,
        caption=draft_data.draft.caption,
        hashtags=draft_data.draft.hashtags,
        platform_data=draft_data.draft.platform_data,
        status=DraftStatus.DRAFT,
        ai_model_used=draft_data.model_used,
        prompt_version=draft_data.prompt_version,
    )
    db.add(draft)
    await db.flush()

    # Save variants
    for variant_data in draft_data.variants:
        variant = ContentVariant(
            draft_id=draft.id,
            style=variant_data.style,
            caption=variant_data.caption,
            hashtags=variant_data.hashtags,
            ai_notes=variant_data.ai_notes,
            is_selected=variant_data.style.value == "balanced",
        )
        db.add(variant)

    # Update idea status if linked
    if idea_id:
        idea_result = await db.execute(
            select(ContentIdea).where(ContentIdea.id == idea_id)
        )
        idea = idea_result.scalar_one_or_none()
        if idea:
            idea.status = IdeaStatus.IN_PROGRESS

    await db.commit()

    # Reload with variants
    result = await db.execute(
        select(ContentDraft)
        .options(selectinload(ContentDraft.variants))
        .where(ContentDraft.id == draft.id)
    )
    draft = result.scalar_one()

    return ContentDraftResponse.model_validate(draft)


@router.post("/brands/{brand_id}/trends/analyze", response_model=TrendAnalysisResponse)
@limiter.limit("20/minute")
async def analyze_trends(
    request: Request,
    brand_id: UUID,
    data: TrendAnalysisRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Analyze user-provided trends and generate ideas."""
    brand = await get_brand(brand_id, current_user, db)

    # Load brand with voice
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one()

    ai_service = AIService()

    analysis = await ai_service.analyze_trends(
        brand=brand,
        trends=[t.model_dump() for t in data.trends],
        generate_ideas=data.generate_ideas,
        idea_count=data.idea_count,
    )

    return TrendAnalysisResponse(
        summary=analysis["summary"],
        key_themes=analysis["key_themes"],
        ideas=analysis.get("ideas"),
    )


@router.post("/brands/{brand_id}/voice/transcribe")
@limiter.limit("20/minute")
async def transcribe_audio(
    request: Request,
    brand_id: UUID,
    audio: UploadFile = File(...),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Transcribe audio input for content creation."""
    await get_brand(brand_id, current_user, db)

    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/webm", "audio/ogg"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Allowed: {', '.join(allowed_types)}",
        )

    # Read file
    content = await audio.read()

    ai_service = AIService()
    transcription = await ai_service.transcribe_audio(content, audio.filename)

    return {"transcription": transcription}


@router.post("/brands/{brand_id}/caption/enhance")
@limiter.limit("20/minute")
async def enhance_caption(
    request: Request,
    brand_id: UUID,
    caption: str = Form(...),
    platform: str = Form(...),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Enhance a caption with brand voice and platform optimization."""
    brand = await get_brand(brand_id, current_user, db)

    # Load brand with voice
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one()

    ai_service = AIService()
    enhanced = await ai_service.enhance_caption(
        brand=brand,
        caption=caption,
        platform=platform,
    )

    return {
        "original": caption,
        "enhanced": enhanced["caption"],
        "hashtags": enhanced["hashtags"],
        "changes_made": enhanced["changes_made"],
    }


@router.post("/brands/{brand_id}/reply/suggest")
@limiter.limit("20/minute")
async def suggest_reply(
    request: Request,
    brand_id: UUID,
    comment: str = Form(...),
    context: str = Form(None),
    current_user: CurrentUser = None,
    db: DBSession = None,
):
    """Generate reply suggestions for a comment/message."""
    brand = await get_brand(brand_id, current_user, db)

    # Load brand with voice
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one()

    ai_service = AIService()
    suggestions = await ai_service.suggest_replies(
        brand=brand,
        comment=comment,
        context=context,
    )

    return {"suggestions": suggestions}
