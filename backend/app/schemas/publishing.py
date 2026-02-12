"""
PresenceOS - Publishing Schemas (Connectors, Posts, Metrics)
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.publishing import (
    ConnectorStatus,
    JobStatus,
    PostStatus,
    SocialPlatform,
)


# Social Connector schemas
class ConnectorCreate(BaseModel):
    """Initial connector setup (OAuth callback handling)."""

    platform: SocialPlatform
    authorization_code: str
    redirect_uri: str


class ConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    platform: SocialPlatform
    account_id: str
    account_name: str | None = None
    account_username: str | None = None
    account_avatar_url: str | None = None
    status: ConnectorStatus
    token_expires_at: datetime | None = None
    daily_posts_count: int
    daily_posts_reset_at: datetime | None = None
    last_sync_at: datetime | None = None
    last_error: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConnectorListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    platform: SocialPlatform
    account_username: str | None = None
    account_avatar_url: str | None = None
    status: ConnectorStatus
    is_active: bool


# OAuth URL generation
class OAuthUrlRequest(BaseModel):
    platform: SocialPlatform
    brand_id: UUID


class OAuthUrlResponse(BaseModel):
    url: str
    state: str  # For CSRF protection


class ApiKeyConnectRequest(BaseModel):
    """Connect a platform via API key (Upload-Post)."""
    platform: SocialPlatform
    brand_id: UUID
    api_key: str


# Scheduled Post schemas
class ContentSnapshot(BaseModel):
    """Snapshot of content at scheduling time."""

    caption: str
    hashtags: list[str] | None = None
    media_urls: list[str] | None = None
    media_type: str | None = None
    platform_data: dict[str, Any] | None = None


class SchedulePostRequest(BaseModel):
    """Request to schedule a post."""

    draft_id: UUID | None = None
    connector_id: UUID
    scheduled_at: datetime
    timezone: str = "Europe/Paris"
    content: ContentSnapshot | None = None  # If no draft_id, use this


class SchedulePostUpdate(BaseModel):
    scheduled_at: datetime | None = None
    content: ContentSnapshot | None = None


class ScheduledPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    draft_id: UUID | None = None
    connector_id: UUID
    scheduled_at: datetime
    timezone: str
    status: PostStatus
    content_snapshot: dict[str, Any]
    platform_post_id: str | None = None
    platform_post_url: str | None = None
    published_at: datetime | None = None
    last_error: str | None = None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class ScheduledPostListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    connector_id: UUID
    scheduled_at: datetime
    status: PostStatus
    platform_post_url: str | None = None
    created_at: datetime


# Publish Job schemas
class PublishJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scheduled_post_id: UUID
    status: JobStatus
    attempt_number: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    platform_response: dict[str, Any] | None = None
    error_message: str | None = None
    error_code: str | None = None
    created_at: datetime


# Metrics schemas
class MetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connector_id: UUID
    post_id: UUID | None = None
    snapshot_date: datetime
    impressions: int | None = None
    reach: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = None
    clicks: int | None = None
    video_views: int | None = None
    video_watch_time: int | None = None
    engagement_rate: float | None = None
    followers_count: int | None = None
    followers_gained: int | None = None


class MetricsSummary(BaseModel):
    """Aggregated metrics for dashboard."""

    period_start: datetime
    period_end: datetime
    total_posts: int
    total_impressions: int
    total_reach: int
    total_engagement: int  # likes + comments + shares + saves
    average_engagement_rate: float
    top_performing_posts: list[UUID]
    engagement_by_platform: dict[str, int]
    engagement_by_pillar: dict[str, int]


class MetricsRequest(BaseModel):
    """Request for metrics with filters."""

    brand_id: UUID
    connector_ids: list[UUID] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    group_by: str | None = None  # "day", "week", "month"


# Calendar view
class CalendarDay(BaseModel):
    date: datetime
    scheduled_posts: list[ScheduledPostListResponse]
    ideas: list[UUID]  # Idea IDs suggested for this date


class CalendarResponse(BaseModel):
    brand_id: UUID
    start_date: datetime
    end_date: datetime
    days: list[CalendarDay]


# Draft Scheduling schemas
class DraftScheduleRequest(BaseModel):
    """Request to schedule or reschedule a draft."""

    connector_id: UUID
    scheduled_at: datetime
    timezone: str = "Europe/Paris"


class DraftScheduleResponse(BaseModel):
    """Response after scheduling a draft."""

    draft_id: UUID
    scheduled_post_id: UUID
    scheduled_at: datetime
    status: PostStatus
    message: str


class BulkScheduleItem(BaseModel):
    """A single item in a bulk schedule request."""

    scheduled_post_id: UUID
    new_scheduled_at: datetime


class BulkScheduleRequest(BaseModel):
    """Request to reschedule multiple posts at once."""

    items: list[BulkScheduleItem] = Field(..., min_length=1, max_length=50)


class BulkScheduleResult(BaseModel):
    """Result of a single item in bulk schedule."""

    scheduled_post_id: UUID
    success: bool
    new_scheduled_at: datetime | None = None
    error: str | None = None


class BulkScheduleResponse(BaseModel):
    """Response after bulk scheduling."""

    total: int
    successful: int
    failed: int
    results: list[BulkScheduleResult]


# Quick Create schemas
class QuickCreateRequest(BaseModel):
    """Request to quickly create and schedule a post from the calendar."""

    title: str = Field(..., min_length=1, max_length=200)
    caption: str = Field(..., min_length=1, max_length=5000)
    platform: str
    media_type: str
    scheduled_at: datetime
    connector_id: UUID
    timezone: str = "Europe/Paris"


class QuickCreateResponse(BaseModel):
    """Response after quick creating a post."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    caption: str
    platform: str
    media_type: str
    scheduled_at: datetime
    status: PostStatus
    connector_id: UUID
    created_at: datetime
    updated_at: datetime
