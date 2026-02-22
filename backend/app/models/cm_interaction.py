"""
PresenceOS - Community Manager Interaction Model

Stores all interactions (reviews, comments, DMs, mentions) from
platforms like Google Business Profile, Instagram, Facebook.
Tracks AI-generated responses and their approval workflow.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CMPlatform(str, enum.Enum):
    GOOGLE = "google"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class CMInteractionType(str, enum.Enum):
    REVIEW = "review"
    COMMENT = "comment"
    DM = "dm"
    MENTION = "mention"


class CMClassification(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    QUESTION = "question"
    CRISIS = "crisis"


class CMResponseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    AUTO_PUBLISHED = "auto_published"


class CMInteraction(BaseModel):
    """A single interaction (review, comment, DM, mention) from a platform."""

    __tablename__ = "cm_interactions"

    # Relationship to the brand (workspace-scoped)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Platform & type
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
    )
    interaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )

    # External platform reference (unique to avoid duplicates)
    external_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False,
    )

    # Original content
    commenter_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    rating: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )

    # AI analysis
    sentiment_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5,
    )
    classification: Mapped[str] = mapped_column(
        String(20), nullable=False, default="neutral",
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
    )

    # AI response
    ai_response_draft: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    ai_reasoning: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    final_response: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )

    # Workflow
    response_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
    )

    # Human feedback
    human_rating: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True,
    )

    # Publishing
    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    platform_response_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
    )

    # Extensible metadata (e.g. Google review URL, profile photo, etc.)
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict,
    )
