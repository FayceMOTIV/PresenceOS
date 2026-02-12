"""
PresenceOS - Metrics & Analytics Endpoints
"""
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.publishing import (
    MetricsSnapshot,
    ScheduledPost,
    SocialConnector,
    PostStatus,
)
from app.schemas.publishing import MetricsResponse, MetricsSummary
from pydantic import BaseModel

router = APIRouter()


class DashboardMetrics(BaseModel):
    """Dashboard KPI summary."""

    total_posts_published: int
    total_posts_scheduled: int
    total_impressions: int
    total_engagement: int
    average_engagement_rate: float
    top_platform: str | None
    best_posting_time: str | None
    ai_insight: str | None


class PlatformBreakdown(BaseModel):
    platform: str
    posts_count: int
    total_impressions: int
    total_engagement: int
    average_engagement_rate: float


@router.get("/brands/{brand_id}/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    days: int = Query(30, le=90),
):
    """Get dashboard KPI metrics for a brand."""
    await get_brand(brand_id, current_user, db)

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get published posts count
    published_result = await db.execute(
        select(func.count(ScheduledPost.id)).where(
            ScheduledPost.brand_id == brand_id,
            ScheduledPost.status == PostStatus.PUBLISHED,
            ScheduledPost.published_at >= start_date,
        )
    )
    total_published = published_result.scalar() or 0

    # Get scheduled posts count
    scheduled_result = await db.execute(
        select(func.count(ScheduledPost.id)).where(
            ScheduledPost.brand_id == brand_id,
            ScheduledPost.status == PostStatus.SCHEDULED,
        )
    )
    total_scheduled = scheduled_result.scalar() or 0

    # Get metrics aggregates
    metrics_result = await db.execute(
        select(
            func.sum(MetricsSnapshot.impressions),
            func.sum(MetricsSnapshot.likes),
            func.sum(MetricsSnapshot.comments),
            func.sum(MetricsSnapshot.shares),
            func.sum(MetricsSnapshot.saves),
            func.avg(MetricsSnapshot.engagement_rate),
        )
        .join(SocialConnector)
        .where(
            SocialConnector.brand_id == brand_id,
            MetricsSnapshot.snapshot_date >= start_date,
            MetricsSnapshot.post_id.isnot(None),
        )
    )
    metrics = metrics_result.one()

    total_impressions = metrics[0] or 0
    total_likes = metrics[1] or 0
    total_comments = metrics[2] or 0
    total_shares = metrics[3] or 0
    total_saves = metrics[4] or 0
    avg_engagement_rate = float(metrics[5] or 0)

    total_engagement = total_likes + total_comments + total_shares + total_saves

    # Find top platform
    platform_result = await db.execute(
        select(
            SocialConnector.platform,
            func.sum(MetricsSnapshot.impressions + MetricsSnapshot.likes).label(
                "score"
            ),
        )
        .join(SocialConnector)
        .where(
            SocialConnector.brand_id == brand_id,
            MetricsSnapshot.snapshot_date >= start_date,
        )
        .group_by(SocialConnector.platform)
        .order_by(func.sum(MetricsSnapshot.impressions + MetricsSnapshot.likes).desc())
        .limit(1)
    )
    top_platform_row = platform_result.first()
    top_platform = top_platform_row[0].value if top_platform_row else None

    # Generate AI insight
    ai_insight = None
    if total_published > 0:
        if avg_engagement_rate > 5:
            ai_insight = f"Excellent performance! Your average engagement rate of {avg_engagement_rate:.1f}% is above industry benchmarks. Keep creating similar content."
        elif avg_engagement_rate > 2:
            ai_insight = f"Good engagement at {avg_engagement_rate:.1f}%. Consider experimenting with video content to boost interaction."
        else:
            ai_insight = f"Engagement at {avg_engagement_rate:.1f}% has room for growth. Try posting during peak hours and using more engaging hooks."

    return DashboardMetrics(
        total_posts_published=total_published,
        total_posts_scheduled=total_scheduled,
        total_impressions=total_impressions,
        total_engagement=total_engagement,
        average_engagement_rate=avg_engagement_rate,
        top_platform=top_platform,
        best_posting_time=None,  # TODO: Calculate from historical data
        ai_insight=ai_insight,
    )


@router.get("/brands/{brand_id}/platforms", response_model=list[PlatformBreakdown])
async def get_platform_breakdown(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    days: int = Query(30, le=90),
):
    """Get metrics breakdown by platform."""
    await get_brand(brand_id, current_user, db)

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            SocialConnector.platform,
            func.count(MetricsSnapshot.id).label("posts_count"),
            func.sum(MetricsSnapshot.impressions).label("total_impressions"),
            func.sum(
                MetricsSnapshot.likes
                + MetricsSnapshot.comments
                + MetricsSnapshot.shares
            ).label("total_engagement"),
            func.avg(MetricsSnapshot.engagement_rate).label("avg_engagement"),
        )
        .join(SocialConnector)
        .where(
            SocialConnector.brand_id == brand_id,
            MetricsSnapshot.snapshot_date >= start_date,
            MetricsSnapshot.post_id.isnot(None),
        )
        .group_by(SocialConnector.platform)
    )

    platforms = []
    for row in result.all():
        platforms.append(
            PlatformBreakdown(
                platform=row.platform.value,
                posts_count=row.posts_count or 0,
                total_impressions=row.total_impressions or 0,
                total_engagement=row.total_engagement or 0,
                average_engagement_rate=float(row.avg_engagement or 0),
            )
        )

    return platforms


@router.get("/posts/{post_id}", response_model=MetricsResponse)
async def get_post_metrics(
    post_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get metrics for a specific published post."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    await get_brand(post.brand_id, current_user, db)

    if post.status != PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post has not been published yet",
        )

    # Get latest metrics snapshot
    metrics_result = await db.execute(
        select(MetricsSnapshot)
        .where(MetricsSnapshot.post_id == post_id)
        .order_by(MetricsSnapshot.snapshot_date.desc())
        .limit(1)
    )
    metrics = metrics_result.scalar_one_or_none()

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics available for this post yet",
        )

    return MetricsResponse.model_validate(metrics)


@router.get("/brands/{brand_id}/top-posts")
async def get_top_posts(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    metric: str = Query("engagement", regex="^(engagement|impressions|reach)$"),
    limit: int = Query(10, le=50),
):
    """Get top performing posts for a brand."""
    await get_brand(brand_id, current_user, db)

    order_column = {
        "engagement": (
            MetricsSnapshot.likes
            + MetricsSnapshot.comments
            + MetricsSnapshot.shares
        ),
        "impressions": MetricsSnapshot.impressions,
        "reach": MetricsSnapshot.reach,
    }[metric]

    result = await db.execute(
        select(ScheduledPost, MetricsSnapshot)
        .join(MetricsSnapshot, ScheduledPost.id == MetricsSnapshot.post_id)
        .join(SocialConnector)
        .where(
            SocialConnector.brand_id == brand_id,
            ScheduledPost.status == PostStatus.PUBLISHED,
        )
        .order_by(order_column.desc())
        .limit(limit)
    )

    top_posts = []
    for post, metrics in result.all():
        top_posts.append(
            {
                "post_id": str(post.id),
                "platform_post_url": post.platform_post_url,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "caption_preview": post.content_snapshot.get("caption", "")[:100],
                "impressions": metrics.impressions,
                "reach": metrics.reach,
                "likes": metrics.likes,
                "comments": metrics.comments,
                "shares": metrics.shares,
                "engagement_rate": metrics.engagement_rate,
            }
        )

    return {"posts": top_posts}


@router.get("/brands/{brand_id}/learning")
async def get_learning_insights(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get AI-generated learning insights from past performance."""
    brand = await get_brand(brand_id, current_user, db)

    # This would use the AI service in production
    # For now, return placeholder insights
    insights = {
        "summary": "Based on your last 30 days of content, here's what's working:",
        "what_works": [
            "Behind-the-scenes content gets 2.3x more engagement",
            "Posts with food close-ups perform best on Instagram",
            "Educational content drives more shares on LinkedIn",
        ],
        "recommendations": [
            "Post more video content - your audience responds well to motion",
            "Best posting times: Tue-Thu 12:00-14:00 and 18:00-20:00",
            "Include a call-to-action in your captions for better engagement",
        ],
        "content_mix_suggestion": {
            "education": 20,
            "entertainment": 25,
            "engagement": 20,
            "promotion": 15,
            "behind_scenes": 20,
        },
    }

    return insights
