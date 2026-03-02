"""
PresenceOS - Brain Models (BrandBrain + VisualBrain + Orchestrator)
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MemoryType(str, enum.Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    REFLECTION = "reflection"


class StoryType(str, enum.Enum):
    POLL = "poll"
    QUIZ = "quiz"
    COUNTDOWN = "countdown"
    BEHIND_SCENES = "behind_scenes"
    PROMO = "promo"


class PermissionStatus(str, enum.Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    GRANTED = "granted"
    DENIED = "denied"


class BrainMemory(BaseModel):
    __tablename__ = "brain_memories"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class VisualMemory(BaseModel):
    __tablename__ = "visual_memories"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)  # Bug Fix #1
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)
    style_tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class VisualPromptTemplate(BaseModel):
    __tablename__ = "visual_prompt_templates"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    style_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    avg_engagement: Mapped[float] = mapped_column(Float, default=0.0)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OrchestratorJob(BaseModel):
    __tablename__ = "orchestrator_jobs"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    posts_planned: Mapped[int] = mapped_column(Integer, default=0)
    posts_generated: Mapped[int] = mapped_column(Integer, default=0)
    stories_planned: Mapped[int] = mapped_column(Integer, default=0)
    stories_generated: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InstagramStory(BaseModel):
    __tablename__ = "instagram_stories"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    orchestrator_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orchestrator_jobs.id", ondelete="SET NULL"), nullable=True
    )
    story_type: Mapped[str] = mapped_column(String(50), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_overlay: Mapped[str | None] = mapped_column(Text, nullable=True)
    interactive_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UGCPost(BaseModel):
    __tablename__ = "ugc_posts"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    source_platform: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    permission_status: Mapped[str] = mapped_column(String(30), default="pending")
    permission_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reposted: Mapped[bool] = mapped_column(Boolean, default=False)
