"""
PresenceOS — Google Business Profile API (Feature 7)

Endpoints for GBP autopublish configuration and post management.
"""
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gbp_publisher import GBPPublisherService

logger = structlog.get_logger()
router = APIRouter()

_service: GBPPublisherService | None = None


def _get_service() -> GBPPublisherService:
    global _service
    if _service is None:
        _service = GBPPublisherService()
    return _service


# ── Request/Response Models ────────────────────────────────

class GBPConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    location_id: Optional[str] = None
    auto_sync: Optional[bool] = None
    default_post_type: Optional[str] = None
    default_cta: Optional[str] = None
    include_photos: Optional[bool] = None
    include_offers: Optional[bool] = None
    publish_frequency: Optional[str] = None


class GBPPublishRequest(BaseModel):
    brand_id: str
    caption: str
    media_urls: list[str] = []
    post_type: str = "WHATS_NEW"
    cta_type: Optional[str] = None
    cta_url: Optional[str] = None
    event_title: Optional[str] = None
    event_start: Optional[str] = None
    event_end: Optional[str] = None
    offer_coupon: Optional[str] = None
    offer_terms: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────

@router.get("/config/{brand_id}")
async def get_config(brand_id: str):
    """Get GBP autopublish configuration for a brand."""
    service = _get_service()
    return service.get_config(brand_id)


@router.patch("/config/{brand_id}")
async def update_config(brand_id: str, request: GBPConfigUpdate):
    """Update GBP autopublish configuration."""
    service = _get_service()
    updates = request.model_dump(exclude_none=True)
    return service.update_config(brand_id, updates)


@router.post("/config/{brand_id}/toggle")
async def toggle_config(brand_id: str):
    """Toggle GBP autopublish on/off."""
    service = _get_service()
    return service.toggle(brand_id)


@router.post("/publish")
async def publish_post(request: GBPPublishRequest):
    """Publish a post to Google Business Profile."""
    service = _get_service()
    return service.publish_post(
        brand_id=request.brand_id,
        caption=request.caption,
        media_urls=request.media_urls,
        post_type=request.post_type,
        cta_type=request.cta_type,
        cta_url=request.cta_url,
        event_title=request.event_title,
        event_start=request.event_start,
        event_end=request.event_end,
        offer_coupon=request.offer_coupon,
        offer_terms=request.offer_terms,
    )


@router.get("/posts/{brand_id}")
async def get_published_posts(brand_id: str):
    """List all GBP-published posts for a brand."""
    service = _get_service()
    return service.get_published(brand_id)


@router.get("/post/{post_id}")
async def get_post(post_id: str):
    """Get a specific GBP post."""
    service = _get_service()
    result = service.get_post(post_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post GBP non trouve")
    return result


@router.delete("/post/{post_id}")
async def delete_post(post_id: str):
    """Delete a GBP post."""
    service = _get_service()
    if not service.delete_post(post_id):
        raise HTTPException(status_code=404, detail="Post GBP non trouve")
    return {"status": "deleted", "post_id": post_id}


@router.get("/stats/{brand_id}")
async def get_stats(brand_id: str):
    """Get GBP publishing statistics for a brand."""
    service = _get_service()
    return service.get_stats(brand_id)
