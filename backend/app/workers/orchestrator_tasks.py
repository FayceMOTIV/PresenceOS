"""
PresenceOS - Orchestrator Celery Tasks
Periodic tasks for autopilot content generation and publishing.
"""
import structlog
from celery import shared_task

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.workers.orchestrator_tasks.autopilot_daily_orchestrate")
def autopilot_daily_orchestrate():
    """Run daily content orchestration for all autopilot-enabled brands."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_autopilot_daily_orchestrate_async())
    finally:
        loop.close()


async def _autopilot_daily_orchestrate_async():
    """Async implementation of daily orchestration."""
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.brand import Brand

    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand).where(Brand.autopilot_enabled.is_(True))
        )
        brands = result.scalars().all()

        logger.info("Orchestrator daily run", brands_count=len(brands))

        for brand in brands:
            try:
                from app.services.orchestrator import AutoPilotOrchestrator
                orchestrator = AutoPilotOrchestrator(brand.id, db)
                await orchestrator.run_daily_generation(
                    posts_count=1,
                    stories_count=2,
                    niche=brand.niche or "restaurant",
                    brand_name=brand.name,
                )

                # Send push notification
                if brand.expo_push_token:
                    from app.services.push_service import send_validation_notification
                    await send_validation_notification(
                        expo_push_token=brand.expo_push_token,
                        posts_count=1,
                        brand_name=brand.name,
                    )

            except Exception as e:
                logger.error(
                    "Orchestrator failed for brand",
                    brand_id=str(brand.id),
                    error=str(e),
                )


@celery_app.task(name="app.workers.orchestrator_tasks.autopilot_check_publish")
def autopilot_check_publish():
    """Check for approved posts that should be auto-published."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_autopilot_check_publish_async())
    finally:
        loop.close()


async def _autopilot_check_publish_async():
    """Auto-publish approved posts that are past their scheduled time."""
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.ai_proposal import AIProposal
    from app.models.brand import Brand

    async with async_session_maker() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(AIProposal)
            .where(
                AIProposal.status == "approved",
                AIProposal.scheduled_at.isnot(None),
                AIProposal.scheduled_at <= now,
            )
            .limit(10)
        )
        proposals = result.scalars().all()

        for proposal in proposals:
            try:
                # Get brand for publishing
                brand_result = await db.execute(
                    select(Brand).where(Brand.id == proposal.brand_id)
                )
                brand = brand_result.scalar_one_or_none()
                if not brand:
                    continue

                # Publish via SocialPublisher
                if proposal.image_url:
                    from app.services.social_publisher import SocialPublisher
                    try:
                        publisher = SocialPublisher()
                        await publisher.publish_photo(
                            brand_id=str(brand.id),
                            image_url=proposal.image_url,
                            caption=proposal.caption or "",
                            platforms=[proposal.platform or "instagram"],
                            hashtags=proposal.hashtags or [],
                        )
                        proposal.status = "published"
                        proposal.published_at = now

                        # Learn from publication
                        from app.services.brand_brain import BrandBrain
                        brain = BrandBrain(brand.id, db)
                        await brain.post_published_learning(
                            caption=proposal.caption or "",
                            platform=proposal.platform or "instagram",
                            engagement={},
                        )

                        # Send push notification
                        if brand.expo_push_token:
                            from app.services.push_service import send_published_notification
                            await send_published_notification(
                                expo_push_token=brand.expo_push_token,
                                platform=proposal.platform or "instagram",
                                brand_name=brand.name,
                            )

                    except Exception as pub_err:
                        logger.error("Auto-publish failed", proposal_id=str(proposal.id), error=str(pub_err))
                        proposal.status = "publish_failed"

                await db.commit()

            except Exception as e:
                logger.error("Auto-publish check error", proposal_id=str(proposal.id), error=str(e))


@celery_app.task(name="app.workers.orchestrator_tasks.detect_trends_daily")
def detect_trends_daily():
    """Detect daily trends and store as brain memories."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_detect_trends_daily_async())
    finally:
        loop.close()


async def _detect_trends_daily_async():
    """Detect trends and store relevant ones in BrandBrain."""
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.brand import Brand
    from app.services.trend_detector import detect_trends
    from app.services.brand_brain import BrandBrain

    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand).where(Brand.autopilot_enabled.is_(True))
        )
        brands = result.scalars().all()

        for brand in brands:
            try:
                trends = await detect_trends(niche=brand.niche or "restaurant")
                if trends.get("trends"):
                    brain = BrandBrain(brand.id, db)
                    for trend in trends["trends"][:3]:
                        await brain.remember(
                            content=f"Trending: {trend.get('topic', '')} — {trend.get('content_idea', '')}",
                            memory_type="episodic",
                            source="trend_detector",
                            confidence=0.6,
                        )
            except Exception as e:
                logger.error("Trend detection failed for brand", brand_id=str(brand.id), error=str(e))


@celery_app.task(name="app.workers.orchestrator_tasks.run_weekly_planning_all_brands")
def run_weekly_planning_all_brands():
    """Generate weekly content plans for all autopilot-enabled brands."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run_weekly_planning_async())
    finally:
        loop.close()


async def _run_weekly_planning_async():
    """Async implementation of weekly planning."""
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.brand import Brand

    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand).where(Brand.autopilot_enabled.is_(True))
        )
        brands = result.scalars().all()

        logger.info("Weekly planning run", brands_count=len(brands))

        for brand in brands:
            try:
                from app.services.orchestrator import AutoPilotOrchestrator
                orchestrator = AutoPilotOrchestrator(brand.id, db)
                await orchestrator.run_weekly_planning(
                    niche=brand.niche or "restaurant",
                    brand_name=brand.name,
                )

                # Send push notification
                if brand.expo_push_token:
                    from app.services.push_service import send_templated_notification
                    await send_templated_notification(
                        expo_push_token=brand.expo_push_token,
                        template_key="weekly_plan_ready",
                        brand_name=brand.name,
                        count=7,
                    )

            except Exception as e:
                logger.error(
                    "Weekly planning failed for brand",
                    brand_id=str(brand.id),
                    error=str(e),
                )


@celery_app.task(name="app.workers.orchestrator_tasks.check_calendar_gaps")
def check_calendar_gaps():
    """Check for gaps in the content calendar and fill them."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_check_calendar_gaps_async())
    finally:
        loop.close()


async def _check_calendar_gaps_async():
    """Check for days without scheduled content and auto-generate."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func
    from app.core.database import async_session_maker
    from app.models.brand import Brand
    from app.models.ai_proposal import AIProposal

    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand).where(Brand.autopilot_enabled.is_(True))
        )
        brands = result.scalars().all()

        now = datetime.now(timezone.utc)
        next_3_days = [now.date() + timedelta(days=i) for i in range(1, 4)]

        for brand in brands:
            try:
                # Count scheduled/approved proposals for next 3 days
                for day in next_3_days:
                    day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
                    day_end = day_start + timedelta(days=1)

                    count_result = await db.execute(
                        select(func.count(AIProposal.id)).where(
                            AIProposal.brand_id == brand.id,
                            AIProposal.status.in_(["approved", "pending", "scheduled"]),
                            AIProposal.scheduled_at >= day_start,
                            AIProposal.scheduled_at < day_end,
                        )
                    )
                    count = count_result.scalar() or 0

                    if count == 0:
                        logger.info(
                            "Calendar gap detected",
                            brand_id=str(brand.id),
                            date=str(day),
                        )
                        # Trigger generation for this gap
                        from app.services.orchestrator import AutoPilotOrchestrator
                        orchestrator = AutoPilotOrchestrator(brand.id, db)
                        await orchestrator.run_daily_generation(
                            posts_count=1,
                            stories_count=0,
                            niche=brand.niche or "restaurant",
                            brand_name=brand.name,
                            target_date=day,
                        )

            except Exception as e:
                logger.error(
                    "Calendar gap check failed for brand",
                    brand_id=str(brand.id),
                    error=str(e),
                )
