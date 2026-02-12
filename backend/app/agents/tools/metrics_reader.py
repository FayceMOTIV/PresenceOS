"""Outil CrewAI pour lire les metriques de performance sociale."""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
from sqlalchemy import select, func
from app.core.database import async_session_maker
from app.models.publishing import ScheduledPost, PostStatus


class MetricsReaderInput(BaseModel):
    brand_id: str = Field(description="UUID de la marque")
    days: int = Field(default=30, description="Nombre de jours a analyser")


class MetricsReaderTool(BaseTool):
    name: str = "metrics_reader"
    description: str = (
        "Lit les metriques de performance des posts publies d'une marque. "
        "Retourne le nombre de posts, taux d'engagement, et meilleures performances."
    )
    args_schema: type[BaseModel] = MetricsReaderInput

    def _run(self, brand_id: str, days: int = 30) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self._async_run(brand_id, days),
                    ).result()
            return loop.run_until_complete(self._async_run(brand_id, days))
        except RuntimeError:
            return asyncio.run(self._async_run(brand_id, days))

    async def _async_run(self, brand_id: str, days: int) -> str:
        from datetime import datetime, timezone, timedelta

        async with async_session_maker() as session:
            since = datetime.now(timezone.utc) - timedelta(days=days)

            result = await session.execute(
                select(ScheduledPost).where(
                    ScheduledPost.brand_id == brand_id,
                    ScheduledPost.status == PostStatus.PUBLISHED,
                    ScheduledPost.published_at >= since,
                )
            )
            posts = result.scalars().all()

            total = len(posts)
            output = f"# Metriques ({days} derniers jours)\n\n"
            output += f"- Posts publies: {total}\n"

            if total == 0:
                output += "- Aucun post publie sur cette periode.\n"
                return output

            # Scheduled posts count
            sched_result = await session.execute(
                select(func.count(ScheduledPost.id)).where(
                    ScheduledPost.brand_id == brand_id,
                    ScheduledPost.status == PostStatus.SCHEDULED,
                )
            )
            scheduled = sched_result.scalar() or 0
            output += f"- Posts programmes: {scheduled}\n"

            return output
