"""
PresenceOS - AutoPilot Orchestrator
Coordinates daily content generation: images, captions, stories, scheduling.
Uses BrandBrain + VisualBrain + CalendarService + CaptionGenerator.
"""
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.brain import OrchestratorJob, InstagramStory, StoryType
from app.services.brand_brain import BrandBrain
from app.services.image_studio import ImageStudio
from app.services.caption_generator import generate_caption_with_brain
from app.services.calendar_service import get_upcoming_events, get_next_optimal_slot

logger = structlog.get_logger()


class AutoPilotOrchestrator:
    """Orchestrates daily autonomous content generation."""

    def __init__(self, brand_id: uuid.UUID, db: AsyncSession):
        self.brand_id = brand_id
        self.db = db
        self.brain = BrandBrain(brand_id, db)
        self.image_studio = ImageStudio(brand_id, db)

    async def run_daily_generation(
        self,
        posts_count: int = 1,
        stories_count: int = 2,
        platforms: list[str] | None = None,
        niche: str = "restaurant",
        brand_name: str | None = None,
    ) -> dict:
        """Run the full daily content generation pipeline.

        1. Create OrchestratorJob
        2. Get calendar context (events, optimal slots)
        3. Get Brain context (memories, rules)
        4. Generate images via ImageStudio
        5. Generate captions via CaptionGenerator
        6. Generate story ideas
        7. Create AIProposals with scheduling
        8. Update job status
        """
        if platforms is None:
            platforms = ["instagram"]

        # Step 1: Create job
        job = OrchestratorJob(
            brand_id=self.brand_id,
            job_type="daily_generation",
            status="running",
            config={
                "posts_count": posts_count,
                "stories_count": stories_count,
                "platforms": platforms,
                "niche": niche,
            },
            posts_planned=posts_count,
            stories_planned=stories_count,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        logger.info(
            "Orchestrator daily generation started",
            brand_id=str(self.brand_id),
            job_id=str(job.id),
        )

        try:
            # Step 2: Calendar context
            upcoming_events = get_upcoming_events(days_ahead=7)
            event_topics = [e["name"] for e in upcoming_events[:2]] if upcoming_events else []

            # Step 3: Brain context
            brain_context = await self.brain.get_context_for_generation(
                topic=event_topics[0] if event_topics else "contenu du jour",
                platform=platforms[0],
            )

            # Step 4: Generate posts
            posts_generated = 0
            for i in range(posts_count):
                try:
                    topic = event_topics[i] if i < len(event_topics) else "plat du jour signature"
                    await self._generate_single_post(
                        topic=topic,
                        platform=platforms[0],
                        niche=niche,
                        brand_name=brand_name,
                        job_id=job.id,
                    )
                    posts_generated += 1
                except Exception as e:
                    logger.error("Post generation failed", index=i, error=str(e))

            # Step 5: Generate stories
            stories_generated = 0
            for i in range(stories_count):
                try:
                    story_type = [StoryType.POLL, StoryType.BEHIND_SCENES, StoryType.PROMO][i % 3]
                    await self._generate_story(
                        story_type=story_type.value,
                        niche=niche,
                        brand_name=brand_name,
                        job_id=job.id,
                    )
                    stories_generated += 1
                except Exception as e:
                    logger.error("Story generation failed", index=i, error=str(e))

            # Step 6: Update job
            await self.db.execute(
                update(OrchestratorJob)
                .where(OrchestratorJob.id == job.id)
                .values(
                    status="completed",
                    posts_generated=posts_generated,
                    stories_generated=stories_generated,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await self.db.commit()

            result = {
                "job_id": str(job.id),
                "status": "completed",
                "posts_generated": posts_generated,
                "stories_generated": stories_generated,
            }
            logger.info("Orchestrator daily generation completed", **result)
            return result

        except Exception as exc:
            await self.db.execute(
                update(OrchestratorJob)
                .where(OrchestratorJob.id == job.id)
                .values(
                    status="failed",
                    error_log=str(exc)[:500],
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await self.db.commit()
            logger.error("Orchestrator daily generation failed", error=str(exc))
            raise

    async def _generate_single_post(
        self,
        topic: str,
        platform: str,
        niche: str,
        brand_name: str | None,
        job_id: uuid.UUID,
    ) -> None:
        """Generate a single post: image + caption + scheduling."""
        # Generate image
        image_result = await self.image_studio.generate_for_post(
            topic=topic,
            platform=platform,
            niche=niche,
            brand_name=brand_name,
        )

        # Generate caption
        caption_result = await generate_caption_with_brain(
            brand_id=self.brand_id,
            db=self.db,
            topic=topic,
            platform=platform,
            niche=niche,
        )

        # Get optimal scheduling slot
        optimal_slot = get_next_optimal_slot(platform)

        # Create AIProposal
        from app.models.ai_proposal import AIProposal
        proposal = AIProposal(
            brand_id=self.brand_id,
            caption=caption_result["caption"],
            hashtags=caption_result.get("hashtags", []),
            image_url=image_result.get("image_url"),
            platform=platform,
            content_type="post",
            status="pending",
            confidence_score=0.85,
            orchestrator_job_id=job_id,
            brain_context={
                "brain_used": caption_result.get("brain_context_used", False),
                "brain_optimized_image": image_result.get("brain_optimized", False),
                "topic": topic,
            },
            scheduled_at=optimal_slot,
        )
        self.db.add(proposal)
        await self.db.commit()

    async def _generate_story(
        self,
        story_type: str,
        niche: str,
        brand_name: str | None,
        job_id: uuid.UUID,
    ) -> None:
        """Generate a story idea."""
        from openai import AsyncOpenAI

        if not settings.openai_api_key:
            return

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"Tu es un expert en stories Instagram pour {niche}. Génère une idée de story de type '{story_type}'.",
                },
                {
                    "role": "user",
                    "content": f"Crée une story {story_type} pour {brand_name or 'un restaurant'}. Réponds en JSON: {{\"text_overlay\": \"...\", \"interactive_data\": {{}}}}",
                },
            ],
            max_tokens=200,
            temperature=0.8,
            response_format={"type": "json_object"},
        )

        import json
        try:
            data = json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning("Story JSON parse failed — using fallback", story_type=story_type, error=str(e))
            data = {"text_overlay": f"Story {story_type}", "interactive_data": {}}

        story = InstagramStory(
            brand_id=self.brand_id,
            orchestrator_job_id=job_id,
            story_type=story_type,
            text_overlay=data.get("text_overlay", ""),
            interactive_data=data.get("interactive_data", {}),
            status="draft",
        )
        self.db.add(story)
        await self.db.commit()


async def get_orchestrator_job_status(job_id: uuid.UUID, db: AsyncSession) -> dict | None:
    """Get status of an orchestrator job."""
    result = await db.execute(
        select(OrchestratorJob).where(OrchestratorJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return None
    return {
        "job_id": str(job.id),
        "job_type": job.job_type,
        "status": job.status,
        "posts_planned": job.posts_planned,
        "posts_generated": job.posts_generated,
        "stories_planned": job.stories_planned,
        "stories_generated": job.stories_generated,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_log": job.error_log,
    }
