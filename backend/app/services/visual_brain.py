"""
PresenceOS - VisualBrain Service
Learns which visuals work best and rewrites prompts.
CRITICAL: VisualBrain NEVER generates images — only manages prompts.
Bug Fix #2: ImageStudio calls VisualBrain, never the reverse.
"""
import json
import uuid

import structlog
from openai import AsyncOpenAI
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.brain import VisualMemory, VisualPromptTemplate

logger = structlog.get_logger()


class VisualBrain:
    def __init__(self, brand_id: uuid.UUID, db: AsyncSession):
        self.brand_id = brand_id
        self.db = db

    async def remember_visual_performance(
        self,
        template_key: str,
        prompt_used: str,
        image_url: str | None = None,
        engagement_score: float | None = None,
        impressions: int | None = None,
        likes: int | None = None,
        saves: int | None = None,
        style_tags: list[str] | None = None,
    ) -> VisualMemory:
        """Record how a visual performed. Bug Fix #1: template_key required from creation."""
        memory = VisualMemory(
            brand_id=self.brand_id,
            template_key=template_key,
            prompt_used=prompt_used,
            image_url=image_url,
            engagement_score=engagement_score,
            impressions=impressions,
            likes=likes,
            saves=saves,
            style_tags=style_tags or [],
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def reoptimize_prompt(self, template_key: str, base_prompt: str) -> str:
        """Rewrite a prompt based on past visual performance. Returns optimized prompt string."""
        if not settings.openai_api_key:
            return base_prompt

        # Get top performing visuals for this template
        stmt = (
            select(VisualMemory)
            .where(
                VisualMemory.brand_id == self.brand_id,
                or_(
                    VisualMemory.template_key == template_key,
                    VisualMemory.template_key == "general",
                ),
                VisualMemory.engagement_score.isnot(None),
            )
            .order_by(VisualMemory.engagement_score.desc())
            .limit(5)
        )
        result = await self.db.execute(stmt)
        top_visuals = result.scalars().all()

        if not top_visuals:
            return base_prompt

        # Build context from best performing prompts
        context = "\n".join([
            f"- Prompt: {v.prompt_used[:200]} | Score: {v.engagement_score} | Tags: {v.style_tags}"
            for v in top_visuals
        ])

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un expert en prompts pour génération d'images food. Optimise le prompt donné en te basant sur les meilleurs prompts passés. Garde le même sujet mais améliore le style.",
                },
                {
                    "role": "user",
                    "content": f"Meilleurs prompts passés:\n{context}\n\nPrompt à optimiser: {base_prompt}\n\nRéponds avec UNIQUEMENT le prompt optimisé, rien d'autre.",
                },
            ],
            max_tokens=300,
            temperature=0.7,
        )

        optimized = response.choices[0].message.content.strip()
        logger.info("Prompt reoptimized", template_key=template_key, brand_id=str(self.brand_id))
        return optimized

    async def get_best_prompt(self, template_key: str) -> str | None:
        """Get the best performing prompt for a template key."""
        stmt = (
            select(VisualMemory.prompt_used)
            .where(
                VisualMemory.brand_id == self.brand_id,
                VisualMemory.template_key == template_key,
                VisualMemory.engagement_score.isnot(None),
            )
            .order_by(VisualMemory.engagement_score.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def weekly_visual_reflection(self) -> str:
        """Analyze visual performance and update prompt templates."""
        if not settings.openai_api_key:
            return "No API key"

        # Get recent visual memories with engagement data
        stmt = (
            select(VisualMemory)
            .where(
                VisualMemory.brand_id == self.brand_id,
                VisualMemory.engagement_score.isnot(None),
            )
            .order_by(VisualMemory.created_at.desc())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        visuals = result.scalars().all()

        if len(visuals) < 3:
            return "Not enough visual data for reflection"

        # Analyze patterns
        visual_data = [
            {
                "template": v.template_key,
                "prompt": v.prompt_used[:150],
                "score": v.engagement_score,
                "tags": v.style_tags,
            }
            for v in visuals
        ]

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Analyse les performances visuelles et génère des recommandations pour les futurs prompts. Réponds en JSON.",
                },
                {
                    "role": "user",
                    "content": f"Données visuelles:\n{json.dumps(visual_data, ensure_ascii=False)}\n\nGénère: {{\"insights\": [\"...\"], \"recommended_style_tags\": [\"...\"], \"avoid_tags\": [\"...\"]}}",
                },
            ],
            max_tokens=500,
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        try:
            insights = json.loads(response.choices[0].message.content)
            logger.info("Visual reflection done", brand_id=str(self.brand_id), insights_count=len(insights.get("insights", [])))
            return json.dumps(insights, ensure_ascii=False)
        except Exception as e:
            logger.error("Visual reflection failed", error=str(e))
            return f"Failed: {str(e)}"

    async def get_visual_brain_status(self) -> dict:
        """Get visual brain stats."""
        total = await self.db.execute(
            select(func.count(VisualMemory.id)).where(VisualMemory.brand_id == self.brand_id)
        )
        total_count = total.scalar() or 0

        with_score = await self.db.execute(
            select(func.count(VisualMemory.id)).where(
                VisualMemory.brand_id == self.brand_id,
                VisualMemory.engagement_score.isnot(None),
            )
        )
        scored_count = with_score.scalar() or 0

        templates = await self.db.execute(
            select(func.count(VisualPromptTemplate.id)).where(
                VisualPromptTemplate.brand_id == self.brand_id,
                VisualPromptTemplate.is_active.is_(True),
            )
        )
        template_count = templates.scalar() or 0

        return {
            "total_visuals": total_count,
            "scored_visuals": scored_count,
            "active_templates": template_count,
            "maturity": min(100, total_count * 5),  # 20 visuals = 100%
        }
