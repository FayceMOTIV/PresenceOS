"""
PresenceOS - Analytics Service
Aggregates metrics + AI insights.
"""
import json
import uuid
from datetime import datetime, timezone, timedelta

import structlog
from openai import AsyncOpenAI
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.publishing import MetricsSnapshot, ScheduledPost, PostStatus

logger = structlog.get_logger()


async def get_analytics_overview(
    brand_id: uuid.UUID,
    db: AsyncSession,
    days: int = 30,
) -> dict:
    """Get analytics overview with AI insights."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Published posts count
    posts_result = await db.execute(
        select(func.count(ScheduledPost.id)).where(
            ScheduledPost.brand_id == brand_id,
            ScheduledPost.status == PostStatus.PUBLISHED,
            ScheduledPost.published_at >= since,
        )
    )
    published_count = posts_result.scalar() or 0

    # Aggregate metrics
    metrics_result = await db.execute(
        select(
            func.sum(MetricsSnapshot.impressions),
            func.sum(MetricsSnapshot.likes),
            func.sum(MetricsSnapshot.comments),
            func.sum(MetricsSnapshot.shares),
            func.sum(MetricsSnapshot.saves),
            func.avg(MetricsSnapshot.engagement_rate),
        ).where(
            MetricsSnapshot.snapshot_date >= since,
            MetricsSnapshot.post_id.in_(
                select(ScheduledPost.id).where(ScheduledPost.brand_id == brand_id)
            ),
        )
    )
    row = metrics_result.one()

    metrics = {
        "impressions": row[0] or 0,
        "likes": row[1] or 0,
        "comments": row[2] or 0,
        "shares": row[3] or 0,
        "saves": row[4] or 0,
        "avg_engagement_rate": round(float(row[5] or 0), 2),
        "published_posts": published_count,
    }

    # Best posting times
    best_times = await _get_best_posting_times(brand_id, db, since)

    # AI Insights
    ai_insights = await _generate_ai_insights(metrics, days)

    return {
        "period_days": days,
        "metrics": metrics,
        "best_times": best_times,
        "ai_insights": ai_insights,
    }


async def _get_best_posting_times(brand_id: uuid.UUID, db: AsyncSession, since: datetime) -> list[dict]:
    """Analyze which posting times got best engagement."""
    result = await db.execute(
        select(ScheduledPost.published_at, MetricsSnapshot.engagement_rate)
        .join(MetricsSnapshot, MetricsSnapshot.post_id == ScheduledPost.id)
        .where(
            ScheduledPost.brand_id == brand_id,
            ScheduledPost.published_at >= since,
            MetricsSnapshot.engagement_rate.isnot(None),
        )
        .order_by(MetricsSnapshot.engagement_rate.desc())
        .limit(5)
    )
    rows = result.all()

    return [
        {
            "day": r[0].strftime("%A") if r[0] else "Unknown",
            "hour": r[0].hour if r[0] else 12,
            "engagement_rate": round(float(r[1]), 2) if r[1] else 0,
        }
        for r in rows
    ]


async def _generate_ai_insights(metrics: dict, days: int) -> list[str]:
    """Generate AI insights from metrics."""
    if not settings.openai_api_key:
        return ["Configurez votre clé API pour obtenir des insights IA"]

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Tu es un analyste social media pour restaurants. Génère 3-5 insights concis en français basés sur les métriques. Réponds en JSON: {\"insights\": [\"...\"]}"
            },
            {
                "role": "user",
                "content": f"Métriques des {days} derniers jours: {json.dumps(metrics)}",
            },
        ],
        max_tokens=300,
        temperature=0.5,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return data.get("insights", [])
    except Exception as e:
        from app.core.observability import capture_exception
        capture_exception(e, {"context": "analytics_ai_insights_parse"})
        return ["Analyse en cours..."]
