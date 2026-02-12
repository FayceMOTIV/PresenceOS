"""
PresenceOS - Autopilot Schemas (Sprint 9)
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── AutopilotConfig ─────────────────────────────────────────────────


class AutopilotConfigCreate(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["instagram"])
    frequency: str = "daily"
    generation_hour: int = Field(default=7, ge=0, le=23)
    auto_publish: bool = False
    approval_window_hours: int = Field(default=4, ge=1, le=24)
    whatsapp_enabled: bool = False
    whatsapp_phone: Optional[str] = None
    preferred_posting_time: Optional[str] = None
    topics: Optional[list[str]] = None


class AutopilotConfigUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    platforms: Optional[list[str]] = None
    frequency: Optional[str] = None
    generation_hour: Optional[int] = Field(default=None, ge=0, le=23)
    auto_publish: Optional[bool] = None
    approval_window_hours: Optional[int] = Field(default=None, ge=1, le=24)
    whatsapp_enabled: Optional[bool] = None
    whatsapp_phone: Optional[str] = None
    preferred_posting_time: Optional[str] = None
    topics: Optional[list[str]] = None


class AutopilotConfigResponse(BaseModel):
    id: UUID
    brand_id: UUID
    is_enabled: bool
    platforms: Optional[list[str]] = None
    frequency: str
    generation_hour: int
    auto_publish: bool
    approval_window_hours: int
    whatsapp_enabled: bool
    whatsapp_phone: Optional[str] = None
    preferred_posting_time: Optional[str] = None
    topics: Optional[list[str]] = None
    total_generated: int
    total_published: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── PendingPost ─────────────────────────────────────────────────────


class PendingPostResponse(BaseModel):
    id: UUID
    config_id: UUID
    brand_id: UUID
    platform: str
    caption: str
    hashtags: Optional[list[str]] = None
    media_urls: Optional[list[str]] = None
    ai_reasoning: Optional[str] = None
    virality_score: Optional[float] = None
    status: str
    whatsapp_message_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    scheduled_post_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PendingPostAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    connector_id: Optional[UUID] = None  # Required for approve if multiple connectors
