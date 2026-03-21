"""
PresenceOS — Analytics API v2 (Sprint 8)

Cross-platform analytics: KPI summary, activity timeline, AI insights.
Delegates all computation to AnalyticsEngineService (no new SQL).
"""

import logging
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.analytics_engine import AnalyticsEngineService

logger = logging.getLogger(__name__)

router = APIRouter()

_service: AnalyticsEngineService | None = None


def _get_service() -> AnalyticsEngineService:
    global _service
    if _service is None:
        _service = AnalyticsEngineService()
    return _service


class PeriodEnum(str, Enum):
    seven_days = "7d"
    thirty_days = "30d"
    ninety_days = "90d"


_PERIOD_TO_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
}


# ── 1. KPI Summary ──────────────────────────────────────────────


@router.get(
    "/{brand_id}/analytics/summary",
    summary="KPI summary with period selection",
)
@limiter.limit("30/minute")
async def get_analytics_summary(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    period: PeriodEnum = Query(default=PeriodEnum.thirty_days, description="Period: 7d, 30d, or 90d"),
):
    """Return aggregated KPIs (followers, engagement, reach, impressions)
    for the selected period. Reuses AnalyticsEngineService.get_kpis()."""
    brand = await verify_brand_access(brand_id, user, db)
    try:
        days = _PERIOD_TO_DAYS[period.value]
        service = _get_service()
        kpis = service.get_kpis(str(brand.id), days)
        return {
            "brand_id": brand_id,
            "period": period.value,
            "kpis": kpis,
        }
    except Exception as exc:
        logger.error(
            "analytics_summary failed",
            extra={"brand_id": brand_id, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics summary")


# ── 2. Activity Timeline ────────────────────────────────────────


@router.get(
    "/{brand_id}/analytics/activity",
    summary="Activity timeline for charts",
)
@limiter.limit("30/minute")
async def get_analytics_activity(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    period: PeriodEnum = Query(default=PeriodEnum.thirty_days, description="Period: 7d, 30d, or 90d"),
):
    """Return daily data points (followers, engagement, reach, impressions)
    for charting. Reuses AnalyticsEngineService.get_timeline()."""
    brand = await verify_brand_access(brand_id, user, db)
    try:
        days = _PERIOD_TO_DAYS[period.value]
        service = _get_service()
        timeline = service.get_timeline(str(brand.id), days)
        return {
            "brand_id": brand_id,
            "period": period.value,
            "data_points": len(timeline),
            "timeline": timeline,
        }
    except Exception as exc:
        logger.error(
            "analytics_activity failed",
            extra={"brand_id": brand_id, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve activity timeline")


# ── 3. AI Insights ──────────────────────────────────────────────


@router.get(
    "/{brand_id}/analytics/insights",
    summary="AI-generated analytics insights",
)
@limiter.limit("15/minute")
async def get_analytics_insights(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Return weekly AI-generated insights and recommendations.
    Reuses AnalyticsEngineService.get_insights()."""
    brand = await verify_brand_access(brand_id, user, db)
    try:
        service = _get_service()
        insights = service.get_insights(str(brand.id))
        return {
            "brand_id": brand_id,
            "count": len(insights),
            "insights": insights,
        }
    except Exception as exc:
        logger.error(
            "analytics_insights failed",
            extra={"brand_id": brand_id, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve insights")
