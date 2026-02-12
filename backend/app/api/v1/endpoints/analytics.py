"""
PresenceOS — Analytics Dashboard API (Feature 9)

Unified cross-platform analytics endpoints.
"""
import structlog
from fastapi import APIRouter, Query

from app.services.analytics_engine import AnalyticsEngineService

logger = structlog.get_logger()
router = APIRouter()

_service: AnalyticsEngineService | None = None


def _get_service() -> AnalyticsEngineService:
    global _service
    if _service is None:
        _service = AnalyticsEngineService()
    return _service


@router.get("/overview/{brand_id}")
async def get_overview(
    brand_id: str,
    days: int = Query(default=30, le=90),
):
    """Get the complete analytics overview with KPIs, platforms, timeline,
    top content, and weekly AI insights."""
    service = _get_service()
    return service.get_overview(brand_id, days)


@router.get("/kpis/{brand_id}")
async def get_kpis(
    brand_id: str,
    days: int = Query(default=30, le=90),
):
    """Get aggregated KPIs (followers, engagement, reach, impressions)."""
    service = _get_service()
    return service.get_kpis(brand_id, days)


@router.get("/timeline/{brand_id}")
async def get_timeline(
    brand_id: str,
    days: int = Query(default=30, le=90),
):
    """Get daily growth data points for charting."""
    service = _get_service()
    return service.get_timeline(brand_id, days)


@router.get("/insights/{brand_id}")
async def get_insights(brand_id: str):
    """Get weekly AI-generated insights and recommendations."""
    service = _get_service()
    return service.get_insights(brand_id)
