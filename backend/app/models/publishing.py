"""
PresenceOS - Publishing Models (Connectors, Jobs, Metrics)
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.content import ContentDraft


class SocialPlatform(str, enum.Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class ConnectorStatus(str, enum.Enum):
    CONNECTED = "connected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class PostStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class SocialConnector(BaseModel):
    """OAuth connection to a social platform for a brand."""

    __tablename__ = "social_connectors"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Platform info
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform), nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Platform's account/page ID
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Connection status
    status: Mapped[ConnectorStatus] = mapped_column(
        Enum(ConnectorStatus), default=ConnectorStatus.CONNECTED, nullable=False
    )

    # OAuth tokens (encrypted at rest)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Platform-specific data
    platform_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # For Instagram: {"business_account_id": "...", "page_id": "..."}
    # For TikTok: {"open_id": "...", "union_id": "..."}
    # For LinkedIn: {"organization_id": "...", "person_id": "..."}

    # Scopes granted
    scopes: Mapped[list[str] | None] = mapped_column(Text, nullable=True)

    # Rate limiting tracking
    daily_posts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_posts_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Last sync
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="social_connectors")
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        "ScheduledPost", back_populates="connector"
    )
    metrics_snapshots: Mapped[list["MetricsSnapshot"]] = relationship(
        "MetricsSnapshot", back_populates="connector", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SocialConnector {self.platform} - {self.account_username}>"


class ScheduledPost(BaseModel):
    """A post scheduled for publishing."""

    __tablename__ = "scheduled_posts"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    draft_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_drafts.id", ondelete="SET NULL"),
        nullable=True,
    )
    connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_connectors.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Paris", nullable=False)

    # Status
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.SCHEDULED, nullable=False
    )

    # Content snapshot (in case draft is edited after scheduling)
    content_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # {"caption": "...", "hashtags": [...], "media_urls": [...], "platform_data": {...}}

    # Platform response
    platform_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform_post_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error tracking
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="scheduled_posts")
    draft: Mapped["ContentDraft | None"] = relationship(
        "ContentDraft", back_populates="scheduled_posts"
    )
    connector: Mapped["SocialConnector"] = relationship(
        "SocialConnector", back_populates="scheduled_posts"
    )
    publish_jobs: Mapped[list["PublishJob"]] = relationship(
        "PublishJob", back_populates="scheduled_post", cascade="all, delete-orphan"
    )
    metrics: Mapped["MetricsSnapshot | None"] = relationship(
        "MetricsSnapshot",
        back_populates="post",
        uselist=False,
        foreign_keys="MetricsSnapshot.post_id",
    )

    def __repr__(self) -> str:
        return f"<ScheduledPost {self.status} at {self.scheduled_at}>"


class PublishJob(BaseModel):
    """Individual publish attempt/job."""

    __tablename__ = "publish_jobs"

    scheduled_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Job tracking
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Platform response
    platform_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Celery task ID
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship
    scheduled_post: Mapped["ScheduledPost"] = relationship(
        "ScheduledPost", back_populates="publish_jobs"
    )

    def __repr__(self) -> str:
        return f"<PublishJob {self.status} attempt {self.attempt_number}>"


class MetricsSnapshot(BaseModel):
    """Performance metrics for a published post or connector."""

    __tablename__ = "metrics_snapshots"

    connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_connectors.id", ondelete="CASCADE"),
        nullable=False,
    )
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_posts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Snapshot timing
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Engagement metrics
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_watch_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # seconds

    # Calculated metrics
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Account-level metrics (when post_id is null)
    followers_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    followers_gained: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Raw platform data
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    connector: Mapped["SocialConnector"] = relationship(
        "SocialConnector", back_populates="metrics_snapshots"
    )
    post: Mapped["ScheduledPost | None"] = relationship(
        "ScheduledPost", back_populates="metrics", foreign_keys=[post_id]
    )

    def __repr__(self) -> str:
        return f"<MetricsSnapshot {self.snapshot_date}>"
