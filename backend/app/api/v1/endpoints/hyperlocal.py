"""
PresenceOS — Hyperlocal Intelligence API (Feature 10)
"""
from typing import Optional

import structlog
from fastapi import APIRouter, Query

from app.api.v1.deps import CurrentBrand
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
    brand: CurrentBrand,
    lat: Optional[float] = Query(default=None),
    lon: Optional[float] = Query(default=None),
):
    """Get full hyperlocal context (weather, events, seasonal, suggestions)."""
    service = _get_service()
    return service.get_context(str(brand.id), lat, lon)


@router.get("/weather/{brand_id}")
async def get_weather(brand: CurrentBrand):
    """Get current weather context."""
    service = _get_service()
    return service.get_weather(str(brand.id))


@router.get("/events/{brand_id}")
async def get_events(brand: CurrentBrand):
    """Get nearby events."""
    service = _get_service()
    return service.get_events(str(brand.id))


@router.get("/suggestions/{brand_id}")
async def get_suggestions(brand: CurrentBrand):
    """Get content suggestions based on all hyperlocal signals."""
    service = _get_service()
    return service.get_suggestions(str(brand.id))
