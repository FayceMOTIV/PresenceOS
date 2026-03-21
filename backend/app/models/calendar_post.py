"""
PresenceOS - CalendarPost Model

AI-generated editorial calendar posts, managed via swipe approve/reject.
"""
import enum
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PostStatus(str, enum.Enum):
    PENDING = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"


class CalendarPost(BaseModel):
    """A planned editorial calendar post for a brand."""

    __tablename__ = "calendar_posts"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    visual_description: Mapped[str | None] = mapped_column(Text, nullable=True, default="")
    visual_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cta: Mapped[str | None] = mapped_column(String(200), nullable=True, default="")

    # Scheduling
    scheduled_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "YYYY-MM-DD"
    scheduled_time: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "HH:MM"

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PostStatus.PENDING.value, index=True
    )

    # Metadata
    postiz_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_engagement: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="medium"
    )
    pillar: Mapped[str | None] = mapped_column(String(200), nullable=True, default="")

    def __repr__(self) -> str:
        return f"<CalendarPost {self.platform}/{self.content_type} {self.scheduled_date} status={self.status}>"
