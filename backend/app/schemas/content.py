"""
PresenceOS - Content Schemas (Ideas, Drafts, Generation)
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import (
    DraftStatus,
    IdeaSource,
    IdeaStatus,
    Platform,
    VariantStyle,
)


# Content Idea schemas
class ContentIdeaBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    source: IdeaSource = IdeaSource.USER_CREATED
    content_pillar: str | None = None
    target_platforms: list[str] | None = None
    trend_reference: str | None = None
    hooks: list[str] | None = None
    suggested_date: datetime | None = None


class ContentIdeaCreate(ContentIdeaBase):
    pass


class ContentIdeaUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: IdeaStatus | None = None
    content_pillar: str | None = None
    target_platforms: list[str] | None = None
    trend_reference: str | None = None
    hooks: list[str] | None = None
    suggested_date: datetime | None = None
    user_score: int | None = Field(None, ge=1, le=5)


class ContentIdeaResponse(ContentIdeaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    status: IdeaStatus
    ai_reasoning: str | None = None
    user_score: int | None = None
    created_at: datetime
    updated_at: datetime


class ContentIdeaListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    title: str
    source: IdeaSource
    status: IdeaStatus
    content_pillar: str | None = None
    target_platforms: list[str] | None = None
    suggested_date: datetime | None = None
    created_at: datetime


# Content Draft schemas
class PlatformData(BaseModel):
    """Platform-specific content data."""

    # TikTok script
    script: list[dict[str, str]] | None = None  # [{"scene": "1", "action": "...", "voiceover": "..."}]
    music_suggestion: str | None = None

    # Stories frames
    frames: list[dict[str, Any]] | None = None  # [{"type": "text", "content": "..."}]
    stickers: list[str] | None = None

    # LinkedIn
    article_link: str | None = None
    call_to_action: str | None = None

    # Custom
    custom: dict[str, Any] | None = None


class ContentDraftBase(BaseModel):
    platform: Platform
    caption: str = Field(..., min_length=1)
    hashtags: list[str] | None = None
    media_urls: list[str] | None = None
    media_type: str | None = None
    platform_data: PlatformData | None = None


class ContentDraftCreate(ContentDraftBase):
    idea_id: UUID | None = None


class ContentDraftUpdate(BaseModel):
    caption: str | None = None
    hashtags: list[str] | None = None
    media_urls: list[str] | None = None
    media_type: str | None = None
    platform_data: PlatformData | None = None
    status: DraftStatus | None = None


class ContentVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    draft_id: UUID
    style: VariantStyle
    caption: str
    hashtags: list[str] | None = None
    is_selected: bool
    ai_notes: str | None = None
    created_at: datetime


class ContentDraftResponse(ContentDraftBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    idea_id: UUID | None = None
    status: DraftStatus
    ai_model_used: str | None = None
    prompt_version: str | None = None
    variants: list[ContentVariantResponse] = []
    created_at: datetime
    updated_at: datetime


class ContentDraftListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    platform: Platform
    status: DraftStatus
    caption: str
    media_type: str | None = None
    created_at: datetime


# AI Generation requests
class GenerateIdeasRequest(BaseModel):
    """Request to generate content ideas."""

    count: int = Field(3, ge=1, le=10)
    content_pillars: list[str] | None = None  # Filter by pillars
    platforms: list[Platform] | None = None
    context: str | None = None  # Additional context (trends, events)
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None


class GeneratedIdea(BaseModel):
    title: str
    description: str
    content_pillar: str
    target_platforms: list[str]
    hooks: list[str]
    ai_reasoning: str
    suggested_date: datetime | None = None


class GenerateIdeasResponse(BaseModel):
    ideas: list[GeneratedIdea]
    model_used: str
    prompt_version: str


class GenerateDraftRequest(BaseModel):
    """Request to generate a content draft."""

    idea_id: UUID | None = None
    platform: Platform
    topic: str | None = None  # If no idea_id, use this topic
    media_urls: list[str] | None = None
    generate_variants: bool = True
    variant_styles: list[VariantStyle] = [
        VariantStyle.CONSERVATIVE,
        VariantStyle.BALANCED,
        VariantStyle.BOLD,
    ]
    additional_instructions: str | None = None


class GeneratedDraft(BaseModel):
    platform: Platform
    caption: str
    hashtags: list[str]
    platform_data: dict[str, Any] | None = None


class GeneratedVariant(BaseModel):
    style: VariantStyle
    caption: str
    hashtags: list[str]
    ai_notes: str


class GenerateDraftResponse(BaseModel):
    draft: GeneratedDraft
    variants: list[GeneratedVariant]
    model_used: str
    prompt_version: str


# Trend input for idea generation
class TrendInput(BaseModel):
    """User-provided trend for inspiration."""

    url: str | None = None
    description: str
    platform: str | None = None


class TrendAnalysisRequest(BaseModel):
    trends: list[TrendInput]
    generate_ideas: bool = True
    idea_count: int = Field(3, ge=1, le=10)


class TrendAnalysisResponse(BaseModel):
    summary: str
    key_themes: list[str]
    ideas: list[GeneratedIdea] | None = None
