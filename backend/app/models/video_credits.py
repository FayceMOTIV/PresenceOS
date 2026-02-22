"""
PresenceOS - Video Credits Model

Tracks video generation credits per brand.
1 credit = 1 video of 5 seconds.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class VideoPlan(str, enum.Enum):
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
    STUDIO = "studio"
    UNLIMITED = "unlimited"


class VideoCredits(BaseModel):
    """Video generation credits for a brand."""

    __tablename__ = "video_credits"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default=VideoPlan.TRIAL.value
    )
    credits_remaining: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    credits_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    reset_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="video_credits")

    def __repr__(self) -> str:
        return f"<VideoCredits brand={self.brand_id} plan={self.plan} remaining={self.credits_remaining}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
