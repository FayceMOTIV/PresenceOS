"""
PresenceOS — Hyperlocal Intelligence API (Feature 10)
"""
from typing import Optional

import structlog
from fastapi import APIRouter, Query

from app.services.hyperlocal_intel import HyperlocalIntelService

logger = structlog.get_logger()
router = APIRouter()

_service: HyperlocalIntelService | None = None


def _get_service() -> HyperlocalIntelService:
    global _service
    if _service is None:
        _service = HyperlocalIntelService()
    return _service


@router.get("/context/{brand_id}")
async def get_context(
    brand_id: str,
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
):
    """Get full hyperlocal context (weather, events, seasonal, suggestions)."""
    service = _get_service()
    return service.get_context(brand_id, lat, lon)


@router.get("/weather/{brand_id}")
async def get_weather(brand_id: str):
    """Get current weather context."""
    service = _get_service()
    return service.get_weather(brand_id)


@router.get("/events/{brand_id}")
async def get_events(brand_id: str):
    """Get nearby events."""
    service = _get_service()
    return service.get_events(brand_id)


@router.get("/suggestions/{brand_id}")
async def get_suggestions(brand_id: str):
    """Get content suggestions based on all hyperlocal signals."""
    service = _get_service()
    return service.get_suggestions(brand_id)
