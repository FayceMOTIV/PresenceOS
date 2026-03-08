"""
PresenceOS - Video Asset Model (Sprint B3)

Persists generated AI videos to S3 for later publishing.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class VideoAssetStatus(str, enum.Enum):
    SAVED = "saved"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class VideoAsset(BaseModel):
    """A generated video saved to S3, optionally published via Upload-Post."""

    __tablename__ = "video_assets"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Video metadata
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False, default="9:16")
    style: Mapped[str] = mapped_column(String(30), nullable=False, default="cinematic")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Original fal.ai URL (temporary, for reference)
    fal_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Publishing
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=VideoAssetStatus.SAVED.value
    )
    platform: Mapped[str | None] = mapped_column(String(30), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    publish_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="video_assets")

    def __repr__(self) -> str:
        return f"<VideoAsset brand={self.brand_id} status={self.status} duration={self.duration_seconds}s>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
