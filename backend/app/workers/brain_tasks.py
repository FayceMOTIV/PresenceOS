"""
PresenceOS - Brain Celery Tasks
"""
import structlog
from celery import shared_task

logger = structlog.get_logger()


@shared_task(name="app.workers.brain_tasks.weekly_reflection_all_brands")
def weekly_reflection_all_brands():
    """Run weekly reflection for all brands with autopilot enabled."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_weekly_reflection_all())
    finally:
        loop.close()


async def _weekly_reflection_all():
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.brand import Brand
    from app.services.brand_brain import BrandBrain

    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand).where(Brand.is_active.is_(True))
        )
        brands = result.scalars().all()

        for brand in brands:
            try:
                brain = BrandBrain(brand.id, db)
                await brain.weekly_reflection()
                logger.info("Reflection done", brand_id=str(brand.id))
            except Exception as e:
                logger.error("Reflection failed", brand_id=str(brand.id), error=str(e))


@shared_task(name="app.workers.brain_tasks.weekly_visual_reflection_all")
def weekly_visual_reflection_all():
    """Run visual reflection for all brands."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_weekly_visual_reflection_all())
    finally:
        loop.close()


async def _weekly_visual_reflection_all():
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.brand import Brand
    from app.services.visual_brain import VisualBrain

    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand).where(Brand.is_active.is_(True))
        )
        brands = result.scalars().all()

        for brand in brands:
            try:
                vb = VisualBrain(brand.id, db)
                await vb.weekly_visual_reflection()
                logger.info("Visual reflection done", brand_id=str(brand.id))
            except Exception as e:
                logger.error("Visual reflection failed", brand_id=str(brand.id), error=str(e))


@shared_task(name="app.workers.brain_tasks.post_published_learning")
def post_published_learning(brand_id: str, caption: str, platform: str, engagement: dict):
    """Learn from a published post."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_post_published_learning(brand_id, caption, platform, engagement))
    finally:
        loop.close()


async def _post_published_learning(brand_id: str, caption: str, platform: str, engagement: dict):
    import uuid
    from app.core.database import async_session_maker
    from app.services.brand_brain import BrandBrain

    async with async_session_maker() as db:
        brain = BrandBrain(uuid.UUID(brand_id), db)
        await brain.post_published_learning(caption, platform, engagement)
