"""
PresenceOS - Content Library Celery Tasks

Background tasks for KB rebuild, asset processing, FLUX Kontext
improvement, proposal generation, and daily brief notifications.
"""
from datetime import date, datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


def _get_sync_session():
    """Get a synchronous database session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings

    url = settings.database_url_sync or settings.database_url.replace(
        "+asyncpg", ""
    )
    engine = create_engine(url)
    return Session(engine)


def _get_async_session():
    """Get an async database session for Celery tasks."""
    import asyncio
    from app.core.database import async_session_factory
    return async_session_factory()


def _run_async(coro):
    """Run an async coroutine in a sync Celery task."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.content_tasks.rebuild_kb_task", bind=True, max_retries=2)
def rebuild_kb_task(self, brand_id: str):
    """Rebuild the Knowledge Base for a brand."""
    logger.info("Celery: rebuilding KB", brand_id=brand_id)

    async def _rebuild():
        async with _get_async_session() as db:
            from app.services.knowledge_base_service import KnowledgeBaseService
            service = KnowledgeBaseService(db)
            return await service.rebuild(brand_id)

    try:
        kb = _run_async(_rebuild())
        logger.info(
            "Celery: KB rebuilt",
            brand_id=brand_id,
            version=kb.kb_version,
            completeness=kb.completeness_score,
        )
        return {"brand_id": brand_id, "version": kb.kb_version}
    except Exception as exc:
        logger.error("Celery: KB rebuild failed", brand_id=brand_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.content_tasks.process_asset_task", bind=True, max_retries=2)
def process_asset_task(self, brand_id: str, asset_id: str):
    """Process an uploaded media asset (thumbnail, quality scoring)."""
    logger.info("Celery: processing asset", brand_id=brand_id, asset_id=asset_id)

    async def _process():
        async with _get_async_session() as db:
            from app.services.asset_processor import AssetProcessorService

            # Load asset to get file bytes from S3
            from app.models.media import MediaAsset
            stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
            result = await db.execute(stmt)
            asset = result.scalar_one_or_none()
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Download the original file from S3
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(asset.public_url, timeout=60.0)
                resp.raise_for_status()
                file_bytes = resp.content

            service = AssetProcessorService(db)
            return await service.process_upload(
                brand_id, asset_id, file_bytes, asset.mime_type
            )

    try:
        asset = _run_async(_process())
        logger.info("Celery: asset processed", asset_id=asset_id)
        return {"asset_id": asset_id, "status": asset.processing_status}
    except Exception as exc:
        logger.error("Celery: asset processing failed", asset_id=asset_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.content_tasks.improve_asset_task", bind=True, max_retries=1)
def improve_asset_task(self, brand_id: str, asset_id: str, prompt: str | None = None):
    """Improve an asset using fal.ai FLUX Kontext."""
    logger.info("Celery: improving asset with FLUX Kontext", asset_id=asset_id)

    async def _improve():
        async with _get_async_session() as db:
            from app.services.asset_processor import AssetProcessorService
            service = AssetProcessorService(db)
            return await service.improve_with_flux_kontext(
                brand_id,
                asset_id,
                prompt=prompt or "Enhance this food photo to look professional, well-lit, and appetizing for social media",
            )

    try:
        asset = _run_async(_improve())
        logger.info("Celery: asset improved", asset_id=asset_id)
        return {"asset_id": asset_id, "improved_url": asset.improved_url}
    except Exception as exc:
        logger.error("Celery: FLUX Kontext failed", asset_id=asset_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.workers.content_tasks.generate_proposal_task", bind=True, max_retries=2)
def generate_proposal_task(self, brand_id: str, source_type: str, source_data: dict):
    """Generate an AI proposal in the background."""
    logger.info(
        "Celery: generating proposal",
        brand_id=brand_id,
        source_type=source_type,
    )

    async def _generate():
        async with _get_async_session() as db:
            from app.services.proposal_generator import ProposalGenerator
            generator = ProposalGenerator(db)

            proposal_id = source_data.get("proposal_id")

            if source_type == "brief":
                return await generator.generate_from_brief(
                    brand_id, source_data.get("response", ""), proposal_id
                )
            elif source_type == "asset":
                return await generator.generate_from_asset(
                    brand_id, source_data.get("asset_id", ""), proposal_id
                )
            elif source_type == "request":
                return await generator.generate_from_request(
                    brand_id,
                    source_data.get("text", ""),
                    source_data.get("content_type", "post"),
                    source_data.get("platform", "instagram"),
                    proposal_id,
                )
            else:
                raise ValueError(f"Unknown source type: {source_type}")

    try:
        proposal = _run_async(_generate())
        logger.info("Celery: proposal generated", proposal_id=str(proposal.id))
        return {"proposal_id": str(proposal.id), "status": proposal.status}
    except Exception as exc:
        logger.error("Celery: proposal generation failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.content_tasks.send_daily_brief_notifications")
def send_daily_brief_notifications():
    """Create DailyBrief records for all active brands and send push notifications.

    Runs daily at 8 AM Europe/Paris via Celery Beat.
    """
    logger.info("Celery: sending daily brief notifications")

    async def _send():
        async with _get_async_session() as db:
            from app.models.brand import Brand
            from app.models.daily_brief import DailyBrief, BriefStatus

            today = date.today()

            # Get all active brands
            stmt = select(Brand).where(Brand.is_active == True)
            result = await db.execute(stmt)
            brands = result.scalars().all()

            created_count = 0
            for brand in brands:
                # Check if brief already exists
                check = select(DailyBrief).where(
                    DailyBrief.brand_id == brand.id,
                    DailyBrief.date == today,
                )
                existing = await db.execute(check)
                if existing.scalar_one_or_none():
                    continue

                brief = DailyBrief(
                    brand_id=brand.id,
                    date=today,
                    status=BriefStatus.PENDING.value,
                    notif_sent_at=datetime.now(timezone.utc),
                )
                db.add(brief)
                created_count += 1

                # TODO: Send Expo push notification to brand owner

            await db.commit()
            return created_count

    count = _run_async(_send())
    logger.info("Celery: daily briefs created", count=count)
    return {"briefs_created": count}
