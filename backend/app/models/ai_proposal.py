"""
PresenceOS - AI Proposal Model (Content Library)

AI-generated content proposals for social media posts.
Generated from Knowledge Base context, daily briefs, assets, or free-text requests.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ProposalType(str, enum.Enum):
    REEL = "reel"
    POST = "post"
    STORY = "story"


class ProposalSource(str, enum.Enum):
    BRIEF = "brief"
    REQUEST = "request"
    ASSET = "asset"
    AUTO = "auto"
    REGENERATE = "regenerate"


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"


class AIProposal(BaseModel):
    """An AI-generated content proposal for social media."""

    __tablename__ = "ai_proposals"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content type
    proposal_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProposalType.POST.value
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, default="instagram")

    # Generated content
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    improved_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source tracking
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProposalSource.REQUEST.value
    )
    source_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # dish_id, asset_id, or brief date

    # Status workflow
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProposalStatus.PENDING.value, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # KB context
    kb_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="ai_proposals")

    def __repr__(self) -> str:
        return f"<AIProposal {self.proposal_type} status={self.status} brand={self.brand_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
