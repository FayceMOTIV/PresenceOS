"""
PresenceOS - Proactive CM Tasks (F3: Session Hebdomadaire Proactive)

Monday 8 AM Paris (7 UTC): generates proactive content proposals for all
active brands, then sends an Expo push notification to open CM Chat.

Zero additional cost: uses existing CMChatService + Expo push (free tier).
"""
import asyncio
import structlog
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.models.brand import Brand
from app.services.cm_chat_service import CMChatService
from app.services.cm_performance_tracker import CMPerformanceTracker

logger = structlog.get_logger()

PROACTIVE_PROMPT = (
    "C'est lundi matin ! En tant que CM, propose-moi un plan de contenu "
    "pour cette semaine avec 3-5 idées de posts Instagram adaptés à mon activité, "
    "la saison et les événements à venir. "
    "Pour chaque idée, donne le type (post/reel/story), un hook accrocheur, "
    "et une légende complète. Utilise le bloc <proposals> pour chaque proposition."
)


# ── Async helpers (same pattern as cm_tasks.py) ──────────────────────────────

def _make_session_maker():
    eng = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
    )
    return async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False), eng


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Push notification sender ─────────────────────────────────────────────────

async def _send_expo_push(token: str, title: str, body: str, data: dict | None = None):
    """Send an Expo push notification (free, no key required for low volume)."""
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
        "channelId": "default",
    }
    if data:
        payload["data"] = data

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("data", {}).get("status") == "error":
                logger.warning(
                    "Expo push error",
                    token=token[:20],
                    detail=result.get("data", {}).get("message"),
                )
    except Exception as exc:
        logger.warning("Expo push send failed", error=str(exc), token=token[:20])


# ── Celery tasks ─────────────────────────────────────────────────────────────

@celery_app.task
def proactive_weekly_all():
    """Dispatch proactive weekly content for all active brands (Monday 8 AM Paris)."""
    return run_async(_proactive_weekly_all())


async def _proactive_weekly_all():
    """Find all active brands and dispatch per-brand proactive tasks."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            result = await db.execute(
                select(Brand.id).where(Brand.is_active.is_(True))
            )
            brand_ids = [row[0] for row in result.all()]

            for brand_id in brand_ids:
                proactive_weekly_brand.delay(str(brand_id))

            logger.info("Proactive weekly dispatched", brand_count=len(brand_ids))
    finally:
        await engine.dispose()


@celery_app.task(bind=True, max_retries=1)
def proactive_weekly_brand(self, brand_id: str):
    """Generate proactive weekly content for a single brand + send push."""
    return run_async(_proactive_weekly_brand(self, brand_id))


async def _proactive_weekly_brand(task, brand_id: str):
    """Async: generate proactive proposals, run performance loop, send push."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            # Load brand with voice + knowledge
            result = await db.execute(
                select(Brand)
                .options(
                    selectinload(Brand.voice),
                    selectinload(Brand.knowledge_items),
                )
                .where(Brand.id == UUID(brand_id), Brand.is_active.is_(True))
            )
            brand = result.scalar_one_or_none()
            if not brand:
                logger.debug("Brand not found or inactive", brand_id=brand_id)
                return

            # F2: Performance loop — learn from recently published proposals
            try:
                tracker = CMPerformanceTracker(db)
                learned = await tracker.track_published_proposals(brand.id)
                if learned > 0:
                    logger.info(
                        "Performance loop completed",
                        brand_id=brand_id,
                        proposals_learned=learned,
                    )
            except Exception as exc:
                logger.warning("Performance tracking failed", brand_id=brand_id, error=str(exc))

            # F3: Generate proactive weekly content via CM Chat
            try:
                svc = CMChatService(db)
                session = await svc.get_or_create_session(brand.id)
                assistant_msg = await svc.send_message(brand, session, PROACTIVE_PROMPT)
                proposal_count = len(assistant_msg.proposals) if assistant_msg.proposals else 0

                logger.info(
                    "Proactive weekly generated",
                    brand_id=brand_id,
                    session_id=str(session.id),
                    proposals=proposal_count,
                )
            except Exception as exc:
                logger.error(
                    "Proactive weekly generation failed",
                    brand_id=brand_id,
                    error=str(exc),
                )
                return

            # Send push notification if brand has token
            push_token = brand.expo_push_token
            if push_token and proposal_count > 0:
                await _send_expo_push(
                    token=push_token,
                    title=f"📋 {brand.name} — Plan de la semaine",
                    body=f"Ton CM a préparé {proposal_count} idées de posts pour cette semaine !",
                    data={
                        "screen": "CMChat",
                        "sessionId": str(session.id),
                    },
                )
                logger.info("Push notification sent", brand_id=brand_id)
    finally:
        await engine.dispose()
