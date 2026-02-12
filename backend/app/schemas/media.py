"""
PresenceOS - Media Library Schemas (Sprint 9B)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MediaAssetResponse(BaseModel):
    """Response for a single media asset."""
    id: str
    brand_id: str
    storage_key: str
    public_url: str
    thumbnail_url: Optional[str] = None
    media_type: str  # "image" or "video"
    mime_type: str
    file_size: int
    original_filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    source: str  # "whatsapp", "upload", "ai_generated"
    ai_description: Optional[str] = None
    ai_tags: Optional[list[str]] = None
    ai_analyzed: bool = False
    used_in_posts: int = 0
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MediaAssetUpdate(BaseModel):
    """Update fields for a media asset."""
    ai_description: Optional[str] = None
    ai_tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None


class VoiceNoteResponse(BaseModel):
    """Response for a single voice note."""
    id: str
    brand_id: str
    storage_key: str
    public_url: str
    mime_type: str
    file_size: int
    duration_seconds: Optional[float] = None
    transcription: Optional[str] = None
    is_transcribed: bool = False
    sender_phone: Optional[str] = None
    parsed_instructions: Optional[dict] = None
    pending_post_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MediaLibraryStats(BaseModel):
    """Stats for the media library."""
    total_images: int = 0
    total_videos: int = 0
    total_voice_notes: int = 0
    total_size_bytes: int = 0
    from_whatsapp: int = 0
    from_upload: int = 0
    ai_analyzed_count: int = 0
