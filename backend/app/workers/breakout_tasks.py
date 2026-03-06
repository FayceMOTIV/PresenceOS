"""
PresenceOS — Celery task for Breakout video generation.

IMPORTANT: Uses asyncio.new_event_loop() pattern (NOT asyncio.run()).
asyncio.run() fails in Celery workers. See CLAUDE.md §4.5 note.
"""

import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="breakout.generate", time_limit=300, soft_time_limit=280)
def generate_breakout_task(
    self,
    job_id: str,
    brand_id: str,
    source_type: str,
    source_url: str = None,
    ai_prompt: str = None,
):
    """
    Pipeline Breakout en tâche Celery.
    time_limit=300s (5 min) pour couvrir le pire cas.
    """
    loop = asyncio.new_event_loop()
    try:
        self.update_state(state="PROGRESS", meta={"progress": 5})

        from app.services.breakout.breakout_engine import BreakoutEngine
        engine = BreakoutEngine()

        result = loop.run_until_complete(
            engine.generate(
                source_type=source_type,
                source_url=source_url,
                ai_prompt=ai_prompt,
                brand_id=brand_id,
            )
        )

        logger.info(
            "Breakout generation complete",
            extra={"job_id": job_id, "brand_id": brand_id, "video_url": result.get("video_url")},
        )

        return result

    except Exception as exc:
        logger.error(
            "Breakout generation failed",
            extra={"job_id": job_id, "brand_id": brand_id, "error": str(exc)},
        )
        raise
    finally:
        loop.close()
