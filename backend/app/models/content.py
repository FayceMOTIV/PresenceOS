"""
PresenceOS - Content Models (Ideas, Drafts, Variants)
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.brand import Brand, ContentPillar
    from app.models.publishing import ScheduledPost


class IdeaSource(str, enum.Enum):
    AI_GENERATED = "ai_generated"
    TREND_INSPIRED = "trend_inspired"
    USER_CREATED = "user_created"
    REPURPOSED = "repurposed"
    CALENDAR_EVENT = "calendar_event"


class IdeaStatus(str, enum.Enum):
    NEW = "new"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    DRAFTED = "drafted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class Platform(str, enum.Enum):
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class VariantStyle(str, enum.Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    BOLD = "bold"
    FAICAL_STYLE = "faical_style"  # Special "Faïçal style" variant


class ContentIdea(BaseModel):
    """A content idea that can be developed into drafts."""

    __tablename__ = "content_ideas"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    source: Mapped[IdeaSource] = mapped_column(
        Enum(IdeaSource), default=IdeaSource.AI_GENERATED, nullable=False
    )
    status: Mapped[IdeaStatus] = mapped_column(
        Enum(IdeaStatus), default=IdeaStatus.NEW, nullable=False
    )
    content_pillar: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Target platforms
    target_platforms: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )

    # AI generation context
    trend_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Hook suggestions
    hooks: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Suggested date (for calendar-based ideas)
    suggested_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # User rating
    user_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="content_ideas")
    drafts: Mapped[list["ContentDraft"]] = relationship(
        "ContentDraft", back_populates="idea", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ContentIdea {self.title}>"


class ContentDraft(BaseModel):
    """A draft of content for a specific platform."""

    __tablename__ = "content_drafts"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    idea_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_ideas.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Platform targeting
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)

    # Status
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus), default=DraftStatus.DRAFT, nullable=False
    )

    # Main content
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Media
    media_urls: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    media_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # image, video, carousel

    # Platform-specific data
    platform_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # For TikTok: {"script": [...], "scenes": [...], "music_suggestion": "..."}
    # For Stories: {"frames": [...], "stickers": [...]}
    # For LinkedIn: {"article_link": "...", "call_to_action": "..."}

    # AI metadata
    ai_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="content_drafts")
    idea: Mapped["ContentIdea | None"] = relationship(
        "ContentIdea", back_populates="drafts"
    )
    variants: Mapped[list["ContentVariant"]] = relationship(
        "ContentVariant", back_populates="draft", cascade="all, delete-orphan"
    )
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        "ScheduledPost", back_populates="draft"
    )

    def __repr__(self) -> str:
        return f"<ContentDraft {self.platform} - {self.status}>"


class ContentVariant(BaseModel):
    """A variant of a draft (conservative, balanced, bold, Faïçal style)."""

    __tablename__ = "content_variants"

    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_drafts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Variant type
    style: Mapped[VariantStyle] = mapped_column(Enum(VariantStyle), nullable=False)

    # Content
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Selection
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # AI reasoning for this variant
    ai_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    draft: Mapped["ContentDraft"] = relationship(
        "ContentDraft", back_populates="variants"
    )

    def __repr__(self) -> str:
        return f"<ContentVariant {self.style} for draft {self.draft_id}>"
