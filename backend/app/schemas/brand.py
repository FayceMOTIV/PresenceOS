"""
PresenceOS - Brand & Knowledge Schemas
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.brand import BrandType, KnowledgeType


# Brand Voice schemas
class BrandVoiceBase(BaseModel):
    tone_formal: int = Field(50, ge=0, le=100)
    tone_playful: int = Field(50, ge=0, le=100)
    tone_bold: int = Field(50, ge=0, le=100)
    tone_technical: int = Field(30, ge=0, le=100)
    tone_emotional: int = Field(50, ge=0, le=100)
    example_phrases: list[str] | None = None
    words_to_avoid: list[str] | None = None
    words_to_prefer: list[str] | None = None
    emojis_allowed: list[str] | None = None
    max_emojis_per_post: int = Field(3, ge=0, le=10)
    hashtag_style: str = "lowercase"
    primary_language: str = "fr"
    allow_english_terms: bool = True
    custom_instructions: str | None = None


class BrandVoiceCreate(BrandVoiceBase):
    pass


class BrandVoiceUpdate(BaseModel):
    tone_formal: int | None = Field(None, ge=0, le=100)
    tone_playful: int | None = Field(None, ge=0, le=100)
    tone_bold: int | None = Field(None, ge=0, le=100)
    tone_technical: int | None = Field(None, ge=0, le=100)
    tone_emotional: int | None = Field(None, ge=0, le=100)
    example_phrases: list[str] | None = None
    words_to_avoid: list[str] | None = None
    words_to_prefer: list[str] | None = None
    emojis_allowed: list[str] | None = None
    max_emojis_per_post: int | None = Field(None, ge=0, le=10)
    hashtag_style: str | None = None
    primary_language: str | None = None
    allow_english_terms: bool | None = None
    custom_instructions: str | None = None


class BrandVoiceResponse(BrandVoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    created_at: datetime
    updated_at: datetime


# Brand schemas
class TargetPersona(BaseModel):
    name: str
    age_range: str | None = None
    interests: list[str] | None = None
    pain_points: list[str] | None = None
    goals: list[str] | None = None


class BrandConstraints(BaseModel):
    halal: bool | None = None
    vegetarian: bool | None = None
    opening_hours: dict[str, str] | None = None  # {"mon": "10:00-22:00", ...}
    seasonal: list[str] | None = None
    custom: dict[str, Any] | None = None


class ContentPillarsConfig(BaseModel):
    education: int = Field(20, ge=0, le=100)
    entertainment: int = Field(20, ge=0, le=100)
    engagement: int = Field(20, ge=0, le=100)
    promotion: int = Field(20, ge=0, le=100)
    behind_scenes: int = Field(20, ge=0, le=100)


class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    brand_type: BrandType = BrandType.OTHER
    description: str | None = None
    website_url: str | None = None
    target_persona: TargetPersona | None = None
    locations: list[str] | None = None
    constraints: BrandConstraints | None = None
    content_pillars: ContentPillarsConfig | None = None


class BrandCreate(BrandBase):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    voice: BrandVoiceCreate | None = None


class BrandUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    brand_type: BrandType | None = None
    description: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    website_url: str | None = None
    target_persona: TargetPersona | None = None
    locations: list[str] | None = None
    constraints: BrandConstraints | None = None
    content_pillars: ContentPillarsConfig | None = None
    is_active: bool | None = None


class BrandResponse(BrandBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    slug: str
    logo_url: str | None = None
    cover_url: str | None = None
    is_active: bool
    voice: BrandVoiceResponse | None = None
    created_at: datetime
    updated_at: datetime


class BrandListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    brand_type: BrandType
    logo_url: str | None = None
    is_active: bool
    created_at: datetime


# Knowledge Item schemas
class KnowledgeMetadata(BaseModel):
    """Flexible metadata for different knowledge types."""

    # Menu/Product
    price: float | None = None
    currency: str = "EUR"
    allergens: list[str] | None = None
    is_bestseller: bool = False

    # Offer
    discount: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    conditions: str | None = None

    # Proof/Review
    rating: int | None = Field(None, ge=1, le=5)
    source: str | None = None
    customer_name: str | None = None

    # Event
    event_date: datetime | None = None
    event_location: str | None = None

    # Custom
    custom: dict[str, Any] | None = None


class KnowledgeItemBase(BaseModel):
    knowledge_type: KnowledgeType
    category: str | None = None
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    metadata: KnowledgeMetadata | None = None
    image_urls: list[str] | None = None
    is_active: bool = True
    is_featured: bool = False
    is_seasonal: bool = False
    season_months: list[int] | None = Field(None, min_length=1, max_length=12)


class KnowledgeItemCreate(KnowledgeItemBase):
    pass


class KnowledgeItemUpdate(BaseModel):
    knowledge_type: KnowledgeType | None = None
    category: str | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    metadata: KnowledgeMetadata | None = None
    image_urls: list[str] | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    is_seasonal: bool | None = None
    season_months: list[int] | None = None


class KnowledgeItemResponse(KnowledgeItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    created_at: datetime
    updated_at: datetime


# Knowledge import schemas
class KnowledgeImportItem(BaseModel):
    knowledge_type: KnowledgeType
    category: str | None = None
    title: str
    content: str
    metadata: dict[str, Any] | None = None
    image_urls: list[str] | None = None


class KnowledgeImport(BaseModel):
    items: list[KnowledgeImportItem]
    overwrite_existing: bool = False


class KnowledgeImportResult(BaseModel):
    total: int
    created: int
    updated: int
    errors: list[dict[str, Any]]


# Brand Onboarding schema
class BrandOnboardingRequest(BaseModel):
    """Simplified onboarding wizard payload."""

    name: str = Field(..., min_length=1, max_length=255)
    business_type: BrandType
    tone_voice: str  # "chaleureux" | "premium" | "fun" | "professionnel" | "inspirant"
    target_audience: str
    website_url: str | None = None
