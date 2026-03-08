"""
PresenceOS — Trend Radar API (Feature 8)
"""
from typing import Optional

import structlog
from fastapi import APIRouter, Query

from app.api.v1.deps import CurrentBrand
from app.services.trend_radar import TrendRadarService

logger = structlog.get_logger()
router = APIRouter()

_service: TrendRadarService | None = None


def _get_service() -> TrendRadarService:
    global _service
    if _service is None:
        _service = TrendRadarService()
    return _service


@router.get("/trends/{brand_id}")
async def get_trends(
    brand: CurrentBrand,
    category: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    limit: int = Query(default=10, le=20),
):
    """Get trending topics for the restaurant industry."""
    service = _get_service()
    return service.get_trends(str(brand.id), category, platform, limit)


@router.get("/categories")
async def get_categories():
    """Get available trend categories."""
    service = _get_service()
    return service.get_categories()


@router.get("/summary/{brand_id}")
async def get_summary(brand: CurrentBrand):
    """Get a summary of the current trend landscape."""
    service = _get_service()
    return service.get_summary(str(brand.id))
