"""
PresenceOS - Brand & Knowledge Models
"""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import Workspace
    from app.models.content import ContentIdea, ContentDraft
    from app.models.publishing import SocialConnector, ScheduledPost


class BrandType(str, enum.Enum):
    RESTAURANT = "restaurant"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    SERVICE = "service"
    PERSONAL = "personal"
    OTHER = "other"


class KnowledgeType(str, enum.Enum):
    MENU = "menu"
    PRODUCT = "product"
    OFFER = "offer"
    FAQ = "faq"
    PROOF = "proof"  # testimonials, reviews
    SCRIPT = "script"  # sales scripts, talking points
    EVENT = "event"
    PROCESS = "process"
    TEAM = "team"
    OTHER = "other"


class ContentPillar(str, enum.Enum):
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    ENGAGEMENT = "engagement"
    PROMOTION = "promotion"
    BEHIND_SCENES = "behind_scenes"


class Brand(BaseModel):
    """A brand within a workspace (e.g., Family's restaurant, Appy Solution SaaS)."""

    __tablename__ = "brands"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    brand_type: Mapped[BrandType] = mapped_column(
        Enum(BrandType), default=BrandType.OTHER, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Target audience
    target_persona: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Example: {"name": "Familles CSP+", "age_range": "30-50", "interests": [...], "pain_points": [...]}

    # Geography
    locations: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # Example: ["Paris 15e", "Boulogne"]

    # Business constraints
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Example: {"halal": true, "opening_hours": {...}, "seasonal": [...]}

    # Content pillars weights (sum to 100)
    content_pillars: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Example: {"education": 20, "entertainment": 30, "engagement": 20, "promotion": 15, "behind_scenes": 15}

    # Active status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="brands")
    voice: Mapped["BrandVoice | None"] = relationship(
        "BrandVoice",
        back_populates="brand",
        uselist=False,
        cascade="all, delete-orphan",
    )
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(
        "KnowledgeItem", back_populates="brand", cascade="all, delete-orphan"
    )
    content_ideas: Mapped[list["ContentIdea"]] = relationship(
        "ContentIdea", back_populates="brand", cascade="all, delete-orphan"
    )
    content_drafts: Mapped[list["ContentDraft"]] = relationship(
        "ContentDraft", back_populates="brand", cascade="all, delete-orphan"
    )
    social_connectors: Mapped[list["SocialConnector"]] = relationship(
        "SocialConnector", back_populates="brand", cascade="all, delete-orphan"
    )
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        "ScheduledPost", back_populates="brand", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Brand {self.name}>"


class BrandVoice(BaseModel):
    """Brand voice configuration and guardrails."""

    __tablename__ = "brand_voices"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Tone sliders (0-100)
    tone_formal: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False
    )  # 0=casual, 100=formal
    tone_playful: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False
    )  # 0=serious, 100=playful
    tone_bold: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False
    )  # 0=subtle, 100=bold
    tone_technical: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )  # 0=simple, 100=technical
    tone_emotional: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False
    )  # 0=rational, 100=emotional

    # Example phrases that capture the brand voice
    example_phrases: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Guardrails
    words_to_avoid: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    words_to_prefer: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    emojis_allowed: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )  # empty = no emojis, null = any emoji
    max_emojis_per_post: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    hashtag_style: Mapped[str] = mapped_column(
        String(50), default="lowercase", nullable=False
    )  # lowercase, PascalCase, camelCase

    # Language
    primary_language: Mapped[str] = mapped_column(
        String(10), default="fr", nullable=False
    )
    allow_english_terms: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Additional instructions for AI
    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    brand: Mapped["Brand"] = relationship("Brand", back_populates="voice")

    def __repr__(self) -> str:
        return f"<BrandVoice for brand {self.brand_id}>"


class KnowledgeItem(BaseModel):
    """A piece of business knowledge (menu item, offer, FAQ, etc.)."""

    __tablename__ = "knowledge_items"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Classification
    knowledge_type: Mapped[KnowledgeType] = mapped_column(
        Enum(KnowledgeType), nullable=False
    )
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "Entrées", "Plats", "Desserts"

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured data (type-specific)
    item_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # For menu: {"price": 15.90, "allergens": [...], "is_bestseller": true}
    # For offer: {"discount": "20%", "valid_until": "2024-12-31", "conditions": "..."}
    # For proof: {"rating": 5, "source": "Google", "customer_name": "..."}

    # Media
    image_urls: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_seasonal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    season_months: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # [1,2,3] for Jan-Mar

    # Vector embedding for RAG (stored as JSONB when pgvector is unavailable)
    embedding: Mapped[list[float] | None] = mapped_column(
        JSONB, nullable=True
    )  # OpenAI text-embedding-3-small dimension

    # Relationship
    brand: Mapped["Brand"] = relationship("Brand", back_populates="knowledge_items")

    def __repr__(self) -> str:
        return f"<KnowledgeItem {self.title}>"
