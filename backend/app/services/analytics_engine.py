"""
PresenceOS — Analytics Engine (Feature 9)

Unified cross-platform analytics with:
- Aggregated KPIs (followers, engagement, reach, impressions)
- Platform breakdown with trends
- Content performance ranking
- Weekly AI-generated insights and recommendations
- Growth tracking over time

In dev/degraded mode, returns realistic mock data.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

logger = structlog.get_logger()


def _mock_kpis(brand_id: str, days: int = 30) -> dict[str, Any]:
    """Generate realistic KPI mock data."""
    base_followers = 2450
    base_engagement = 4.2
    base_reach = 12800
    base_impressions = 34500

    prev_followers = base_followers - random.randint(50, 150)
    prev_engagement = round(base_engagement - random.uniform(0.3, 0.8), 1)
    prev_reach = base_reach - random.randint(800, 2000)
    prev_impressions = base_impressions - random.randint(2000, 5000)

    return {
        "period_days": days,
        "followers": {
            "current": base_followers,
            "previous": prev_followers,
            "change": base_followers - prev_followers,
            "change_pct": round((base_followers - prev_followers) / prev_followers * 100, 1),
        },
        "engagement_rate": {
            "current": base_engagement,
            "previous": prev_engagement,
            "change": round(base_engagement - prev_engagement, 1),
            "change_pct": round((base_engagement - prev_engagement) / prev_engagement * 100, 1),
        },
        "reach": {
            "current": base_reach,
            "previous": prev_reach,
            "change": base_reach - prev_reach,
            "change_pct": round((base_reach - prev_reach) / prev_reach * 100, 1),
        },
        "impressions": {
            "current": base_impressions,
            "previous": prev_impressions,
            "change": base_impressions - prev_impressions,
            "change_pct": round((base_impressions - prev_impressions) / prev_impressions * 100, 1),
        },
    }


def _mock_platform_breakdown(brand_id: str) -> list[dict[str, Any]]:
    """Generate platform breakdown data."""
    return [
        {
            "platform": "instagram",
            "followers": 1850,
            "engagement_rate": 4.8,
            "posts_count": 24,
            "top_content_type": "carousel",
            "best_time": "12:00",
            "growth_trend": "up",
        },
        {
            "platform": "tiktok",
            "followers": 320,
            "engagement_rate": 6.2,
            "posts_count": 12,
            "top_content_type": "video",
            "best_time": "19:00",
            "growth_trend": "up",
        },
        {
            "platform": "facebook",
            "followers": 580,
            "engagement_rate": 2.1,
            "posts_count": 18,
            "top_content_type": "photo",
            "best_time": "10:00",
            "growth_trend": "stable",
        },
        {
            "platform": "google_business",
            "followers": None,
            "engagement_rate": None,
            "posts_count": 8,
            "top_content_type": "update",
            "best_time": "09:00",
            "growth_trend": "up",
        },
    ]


def _mock_growth_timeline(brand_id: str, days: int = 30) -> list[dict[str, Any]]:
    """Generate daily growth data points for charting."""
    timeline = []
    base = 2300
    now = datetime.now(timezone.utc)
    for i in range(days, 0, -1):
        date = now - timedelta(days=i)
        base += random.randint(-5, 15)
        timeline.append({
            "date": date.strftime("%Y-%m-%d"),
            "followers": base,
            "engagement": round(random.uniform(3.0, 6.0), 1),
            "reach": random.randint(300, 800),
            "impressions": random.randint(800, 1800),
        })
    return timeline


def _mock_top_content(brand_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Generate top-performing content data."""
    contents = [
        {
            "id": f"post-{i}",
            "caption": caption,
            "platform": platform,
            "engagement_rate": round(random.uniform(3.5, 12.0), 1),
            "likes": random.randint(50, 500),
            "comments": random.randint(5, 80),
            "shares": random.randint(2, 40),
            "reach": random.randint(500, 5000),
            "published_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 28))).isoformat(),
        }
        for i, (caption, platform) in enumerate([
            ("Notre nouveau burger signature est arrive !", "instagram"),
            ("Les coulisses de notre cuisine", "tiktok"),
            ("Menu du jour : risotto aux cèpes", "instagram"),
            ("Merci pour vos 2000 abonnes !", "facebook"),
            ("Notre chef vous montre sa technique", "tiktok"),
            ("Brunch du dimanche — reservez !", "instagram"),
            ("Nouveaux cocktails d'ete", "facebook"),
        ])
    ]
    contents.sort(key=lambda x: x["engagement_rate"], reverse=True)
    return contents[:limit]


def _generate_weekly_insights(brand_id: str, kpis: dict, platform_data: list) -> list[dict[str, Any]]:
    """Generate AI-style weekly insights and recommendations."""
    insights = [
        {
            "type": "growth",
            "icon": "trending_up",
            "title": "Croissance followers",
            "message": f"Vous avez gagne {kpis['followers']['change']} abonnes cette semaine "
                       f"(+{kpis['followers']['change_pct']}%). Votre contenu food "
                       f"performe bien sur Instagram.",
            "priority": "high" if kpis["followers"]["change_pct"] > 3 else "medium",
        },
        {
            "type": "engagement",
            "icon": "heart",
            "title": "Engagement en hausse",
            "message": f"Taux d'engagement a {kpis['engagement_rate']['current']}% "
                       f"(+{kpis['engagement_rate']['change']} pts). Les carousels "
                       f"generent 2x plus d'interactions que les posts simples.",
            "priority": "high",
        },
        {
            "type": "recommendation",
            "icon": "lightbulb",
            "title": "Recommandation",
            "message": "Publiez plus de Reels entre 12h-13h. Ce format "
                       "genere 3x plus de reach sur votre audience restauration.",
            "priority": "medium",
        },
        {
            "type": "opportunity",
            "icon": "zap",
            "title": "Opportunite TikTok",
            "message": "Votre compte TikTok a le meilleur taux d'engagement (6.2%). "
                       "Doublez la frequence de publication pour capitaliser.",
            "priority": "medium",
        },
        {
            "type": "alert",
            "icon": "alert_triangle",
            "title": "Facebook en stagnation",
            "message": "L'engagement Facebook est bas (2.1%). Testez des formats "
                       "video et des questions pour relancer l'interaction.",
            "priority": "low",
        },
    ]
    return insights


class AnalyticsEngineService:
    """Unified cross-platform analytics engine."""

    def get_overview(self, brand_id: str, days: int = 30) -> dict[str, Any]:
        """Get the complete analytics overview for a brand."""
        kpis = _mock_kpis(brand_id, days)
        platforms = _mock_platform_breakdown(brand_id)
        timeline = _mock_growth_timeline(brand_id, days)
        top_content = _mock_top_content(brand_id)
        insights = _generate_weekly_insights(brand_id, kpis, platforms)

        return {
            "brand_id": brand_id,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "kpis": kpis,
            "platforms": platforms,
            "timeline": timeline,
            "top_content": top_content,
            "weekly_insights": insights,
        }

    def get_kpis(self, brand_id: str, days: int = 30) -> dict[str, Any]:
        """Get just the KPIs."""
        return _mock_kpis(brand_id, days)

    def get_timeline(self, brand_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Get growth timeline data for charts."""
        return _mock_growth_timeline(brand_id, days)

    def get_insights(self, brand_id: str) -> list[dict[str, Any]]:
        """Get weekly AI-generated insights."""
        kpis = _mock_kpis(brand_id)
        platforms = _mock_platform_breakdown(brand_id)
        return _generate_weekly_insights(brand_id, kpis, platforms)
