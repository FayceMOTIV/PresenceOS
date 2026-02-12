"""
PresenceOS - Smart Scheduling API (Feature 1)

Endpoints for intelligent post scheduling based on optimal engagement times.
"""
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.smart_scheduler import SmartSchedulerService

logger = structlog.get_logger()
router = APIRouter()

_service: SmartSchedulerService | None = None


def _get_service() -> SmartSchedulerService:
    global _service
    if _service is None:
        _service = SmartSchedulerService()
    return _service


# ── Request/Response Models ────────────────────────────────

class ScheduleRequest(BaseModel):
    brand_id: str
    platform: str = "instagram"
    caption: str = ""
    media_urls: list[str] = []
    hashtags: list[str] = []
    scheduled_at: Optional[str] = None
    use_optimal: bool = True


class RescheduleRequest(BaseModel):
    new_datetime: str


class TimeSlot(BaseModel):
    datetime: str
    day: str
    day_label: str
    hour: int
    hour_label: str
    score: int
    platform: str


class ScheduledPost(BaseModel):
    id: str
    brand_id: str
    platform: str
    caption: str
    media_urls: list[str]
    hashtags: list[str]
    scheduled_at: str
    score: int
    status: str
    created_at: str


# ── Endpoints ──────────────────────────────────────────────

@router.get("/optimal-times/{brand_id}", response_model=list[TimeSlot])
async def get_optimal_times(
    brand_id: str,
    platform: str = Query(default="instagram"),
    count: int = Query(default=5, le=20),
    timezone_offset: int = Query(default=1, description="Hours from UTC"),
):
    """Get the top optimal posting times for the next 7 days.

    Uses restaurant industry benchmarks (Sprout Social / Later 2025).
    Returns time slots sorted by engagement score.
    """
    service = _get_service()
    return service.get_optimal_times(brand_id, platform, timezone_offset, count)


@router.get("/next-optimal/{brand_id}", response_model=TimeSlot)
async def get_next_optimal(
    brand_id: str,
    platform: str = Query(default="instagram"),
    timezone_offset: int = Query(default=1),
):
    """Get the single next best time slot for a platform."""
    service = _get_service()
    return service.get_next_optimal(brand_id, platform, timezone_offset)


@router.post("/schedule", response_model=ScheduledPost)
async def schedule_post(request: ScheduleRequest):
    """Schedule a post for the optimal time or a specific time.

    If scheduled_at is provided, uses that time.
    If use_optimal is True (default), picks the next best slot.
    """
    service = _get_service()
    result = service.schedule_post(
        brand_id=request.brand_id,
        platform=request.platform,
        content={
            "caption": request.caption,
            "media_urls": request.media_urls,
            "hashtags": request.hashtags,
        },
        scheduled_at=request.scheduled_at,
        use_optimal=request.use_optimal,
    )
    return result


@router.get("/calendar/{brand_id}")
async def get_calendar(
    brand_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get calendar view with scheduled posts and optimal time hints."""
    service = _get_service()
    return service.get_calendar(brand_id, start_date, end_date)


@router.get("/scheduled/{brand_id}", response_model=list[ScheduledPost])
async def get_scheduled_posts(brand_id: str):
    """List all scheduled posts for a brand."""
    service = _get_service()
    return service.get_scheduled(brand_id)


@router.patch("/reschedule/{post_id}", response_model=ScheduledPost)
async def reschedule_post(post_id: str, request: RescheduleRequest):
    """Move a scheduled post to a different time."""
    service = _get_service()
    result = service.reschedule(post_id, request.new_datetime)
    if not result:
        raise HTTPException(status_code=404, detail="Post planifie non trouve")
    return result


@router.delete("/cancel/{post_id}")
async def cancel_post(post_id: str):
    """Cancel a scheduled post."""
    service = _get_service()
    if not service.cancel(post_id):
        raise HTTPException(status_code=404, detail="Post planifie non trouve")
    return {"status": "cancelled", "post_id": post_id}
