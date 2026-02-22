"""
PresenceOS - Media Library Models (Sprint 9B)

MediaAsset: images/videos received via WhatsApp or uploaded.
VoiceNote: audio messages transcribed by Whisper.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MediaSource(str, enum.Enum):
    WHATSAPP = "whatsapp"
    UPLOAD = "upload"
    AI_GENERATED = "ai_generated"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    IMPROVING = "improving"
    READY = "ready"
    FAILED = "failed"


class MediaAsset(BaseModel):
    """An image or video received via WhatsApp or uploaded."""

    __tablename__ = "media_assets"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # File metadata
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType), nullable=False
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Source
    source: Mapped[MediaSource] = mapped_column(
        Enum(MediaSource),
        default=MediaSource.UPLOAD,
        nullable=False,
    )
    whatsapp_media_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI analysis
    ai_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    ai_analyzed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Content Library — AI enhancement
    improved_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.READY.value, nullable=False
    )
    linked_dish_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dishes.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Usage tracking
    used_in_posts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="media_assets")
    linked_dish: Mapped["Dish | None"] = relationship(
        "Dish", foreign_keys=[linked_dish_id]
    )

    def __repr__(self) -> str:
        return f"<MediaAsset {self.media_type.value} source={self.source.value}>"


class VoiceNote(BaseModel):
    """A voice note received via WhatsApp and transcribed."""

    __tablename__ = "voice_notes"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Storage
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    public_url: Mapped[str] = mapped_column(Text, nullable=False)

    # File metadata
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Transcription
    transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_transcribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # WhatsApp source
    whatsapp_media_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Parsed instructions (from instruction_parser)
    parsed_instructions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Link to pending post created from this voice note
    pending_post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pending_posts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="voice_notes")

    def __repr__(self) -> str:
        return f"<VoiceNote brand={self.brand_id} transcribed={self.is_transcribed}>"


# TYPE_CHECKING import to avoid circular
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.dish import Dish
