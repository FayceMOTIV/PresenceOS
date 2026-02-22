"""
PresenceOS - Knowledge Base Service (Content Library)

Compiles all brand data into a single cached KB used for AI prompt generation.
Supports debounced rebuilds via Redis to avoid excessive recompilation.
"""
import json
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.brand import Brand, BrandVoice, KnowledgeItem
from app.models.compiled_kb import CompiledKB
from app.models.dish import Dish
from app.models.media import MediaAsset
from app.models.daily_brief import DailyBrief, BriefStatus
from app.models.publishing import ScheduledPost

logger = structlog.get_logger()

DEBOUNCE_TTL_SECONDS = 30
DEBOUNCE_KEY_PREFIX = "kb:rebuild:debounce:"


class KnowledgeBaseService:
    """Compiles and caches the brand Knowledge Base for AI prompts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Public API ────────────────────────────────────────────────────────

    async def rebuild(self, brand_id: str) -> CompiledKB:
        """Rebuild the compiled KB for a brand.

        Gathers identity, menu, media, today's brief, posting history,
        and performance data, then upserts the CompiledKB record.
        """
        logger.info("Rebuilding KB", brand_id=brand_id)

        # Load brand with relationships
        stmt = (
            select(Brand)
            .options(
                selectinload(Brand.voice),
                selectinload(Brand.knowledge_items),
            )
            .where(Brand.id == brand_id)
        )
        result = await self.db.execute(stmt)
        brand = result.scalar_one_or_none()
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")

        # Compile each section (resilient — log errors, use defaults)
        identity = self._compile_identity(brand)

        try:
            menu = await self._compile_menu(brand_id)
        except Exception as exc:
            logger.error("KB: _compile_menu failed", brand_id=brand_id, error=str(exc))
            menu = {"total_dishes": 0, "categories": {}}

        try:
            media = await self._compile_media(brand_id)
        except Exception as exc:
            logger.error("KB: _compile_media failed", brand_id=brand_id, error=str(exc))
            media = {"total_assets": 0, "assets": []}

        try:
            today = await self._compile_today(brand_id)
        except Exception as exc:
            logger.error("KB: _compile_today failed", brand_id=brand_id, error=str(exc))
            today = {"has_brief": False, "date": datetime.now(timezone.utc).date().isoformat()}

        try:
            posting_history = await self._compile_posting_history(brand_id)
        except Exception as exc:
            logger.error("KB: _compile_posting_history failed", brand_id=brand_id, error=str(exc))
            posting_history = {"last_7_days_count": 0, "posts": []}

        try:
            performance = await self._compile_performance(brand_id)
        except Exception as exc:
            logger.error("KB: _compile_performance failed", brand_id=brand_id, error=str(exc))
            performance = {"avg_engagement_rate": None, "top_content_types": [], "best_posting_times": []}

        completeness = self._calculate_completeness_from_sections(
            brand, identity, menu, media
        )

        # Upsert CompiledKB
        stmt = select(CompiledKB).where(CompiledKB.brand_id == brand_id)
        result = await self.db.execute(stmt)
        kb = result.scalar_one_or_none()

        if kb:
            kb.kb_version += 1
            kb.identity = identity
            kb.menu = menu
            kb.media = media
            kb.today = today
            kb.posting_history = posting_history
            kb.performance = performance
            kb.completeness_score = completeness
            kb.compiled_at = datetime.now(timezone.utc)
        else:
            kb = CompiledKB(
                brand_id=brand_id,
                kb_version=1,
                identity=identity,
                menu=menu,
                media=media,
                today=today,
                posting_history=posting_history,
                performance=performance,
                completeness_score=completeness,
                compiled_at=datetime.now(timezone.utc),
            )
            self.db.add(kb)

        await self.db.commit()
        await self.db.refresh(kb)

        logger.info(
            "KB rebuilt",
            brand_id=brand_id,
            version=kb.kb_version,
            completeness=completeness,
        )
        return kb

    async def rebuild_debounced(self, brand_id: str) -> bool:
        """Debounced rebuild: max 1 per 30s per brand using Redis SET NX.

        Returns True if rebuild was dispatched, False if debounced.
        """
        key = f"{DEBOUNCE_KEY_PREFIX}{brand_id}"
        try:
            r = aioredis.from_url(settings.redis_url)
            acquired = await r.set(key, "1", nx=True, ex=DEBOUNCE_TTL_SECONDS)
            await r.aclose()

            if acquired:
                # Dispatch async task
                from app.workers.content_tasks import rebuild_kb_task
                rebuild_kb_task.delay(str(brand_id))
                logger.info("KB rebuild dispatched", brand_id=brand_id)
                return True
            else:
                logger.debug("KB rebuild debounced", brand_id=brand_id)
                return False
        except Exception as exc:
            logger.error("KB debounce error, rebuilding directly", error=str(exc))
            # Fallback: dispatch anyway
            from app.workers.content_tasks import rebuild_kb_task
            rebuild_kb_task.delay(str(brand_id))
            return True

    async def get_kb(self, brand_id: str) -> CompiledKB | None:
        """Get the current compiled KB for a brand."""
        stmt = select(CompiledKB).where(CompiledKB.brand_id == brand_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def calculate_completeness(self, brand_id: str) -> int:
        """Calculate completeness score (0-100) for a brand."""
        try:
            stmt = (
                select(Brand)
                .options(selectinload(Brand.voice))
                .where(Brand.id == brand_id)
            )
            result = await self.db.execute(stmt)
            brand = result.scalar_one_or_none()
            if not brand:
                return 0

            identity = self._compile_identity(brand)
            menu = await self._compile_menu(brand_id)
            media = await self._compile_media(brand_id)

            return self._calculate_completeness_from_sections(brand, identity, menu, media)
        except Exception as exc:
            logger.error("calculate_completeness failed", brand_id=brand_id, error=str(exc))
            return 0

    # ── Section Compilers ─────────────────────────────────────────────────

    def _compile_identity(self, brand: Brand) -> dict:
        """Compile brand identity section."""
        voice = brand.voice
        return {
            "name": brand.name,
            "type": brand.brand_type.value if brand.brand_type else "other",
            "description": brand.description,
            "logo_url": brand.logo_url,
            "locations": brand.locations or [],
            "constraints": brand.constraints or {},
            "content_pillars": brand.content_pillars or {},
            "target_persona": brand.target_persona or {},
            "voice": {
                "tone_formal": voice.tone_formal if voice else 50,
                "tone_playful": voice.tone_playful if voice else 50,
                "tone_bold": voice.tone_bold if voice else 50,
                "emojis_allowed": bool(voice and voice.emojis_allowed),
                "words_to_avoid": voice.words_to_avoid or [] if voice else [],
                "words_to_prefer": voice.words_to_prefer or [] if voice else [],
                "custom_instructions": voice.custom_instructions if voice else None,
                "language": voice.primary_language if voice else "fr",
            },
        }

    async def _compile_menu(self, brand_id: str) -> dict:
        """Compile menu section from dishes."""
        stmt = (
            select(Dish)
            .where(Dish.brand_id == brand_id, Dish.is_available == True)
            .order_by(Dish.display_order, Dish.name)
        )
        result = await self.db.execute(stmt)
        dishes = result.scalars().all()

        categories: dict[str, list] = {}
        for dish in dishes:
            cat = dish.category or "autres"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "id": str(dish.id),
                "name": dish.name,
                "price": float(dish.price) if dish.price else None,
                "description": dish.description,
                "is_featured": dish.is_featured,
                "has_photo": dish.cover_asset_id is not None,
                "ai_post_count": dish.ai_post_count,
                "last_posted_at": dish.last_posted_at.isoformat() if dish.last_posted_at else None,
            })

        return {
            "total_dishes": len(dishes),
            "categories": categories,
        }

    async def _compile_media(self, brand_id: str) -> dict:
        """Compile media section — top 20 assets by quality score."""
        stmt = (
            select(MediaAsset)
            .where(
                MediaAsset.brand_id == brand_id,
                MediaAsset.is_archived == False,
                MediaAsset.processing_status == "ready",
            )
            .order_by(MediaAsset.quality_score.desc().nulls_last())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        assets = result.scalars().all()

        return {
            "total_assets": len(assets),
            "assets": [
                {
                    "id": str(a.id),
                    "url": a.improved_url or a.public_url,
                    "type": a.media_type.value,
                    "quality_score": a.quality_score,
                    "label": a.asset_label,
                    "linked_dish_id": str(a.linked_dish_id) if a.linked_dish_id else None,
                    "used_in_posts": a.used_in_posts,
                }
                for a in assets
            ],
        }

    async def _compile_today(self, brand_id: str) -> dict:
        """Compile today's brief response if available."""
        today = datetime.now(timezone.utc).date()
        stmt = (
            select(DailyBrief)
            .where(
                DailyBrief.brand_id == brand_id,
                DailyBrief.date == today,
            )
        )
        result = await self.db.execute(stmt)
        brief = result.scalar_one_or_none()

        if brief and brief.status == BriefStatus.ANSWERED.value:
            return {
                "has_brief": True,
                "response": brief.response,
                "date": today.isoformat(),
            }
        return {"has_brief": False, "date": today.isoformat()}

    async def _compile_posting_history(self, brand_id: str) -> dict:
        """Compile last 7 days of posting history."""
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        stmt = (
            select(ScheduledPost)
            .where(
                ScheduledPost.brand_id == brand_id,
                ScheduledPost.scheduled_at >= seven_days_ago,
            )
            .order_by(desc(ScheduledPost.scheduled_at))
        )
        result = await self.db.execute(stmt)
        posts = result.scalars().all()

        return {
            "last_7_days_count": len(posts),
            "posts": [
                {
                    "id": str(p.id),
                    "caption": (p.content_snapshot.get("caption", "") or "")[:100] if p.content_snapshot else "",
                    "platform": None,
                    "scheduled_time": p.scheduled_at.isoformat() if p.scheduled_at else None,
                }
                for p in posts[:10]  # Cap at 10 for prompt size
            ],
        }

    async def _compile_performance(self, brand_id: str) -> dict:
        """Compile performance metrics placeholder."""
        # TODO: pull from MetricsSnapshot when available
        return {
            "avg_engagement_rate": None,
            "top_content_types": [],
            "best_posting_times": [],
        }

    def _calculate_completeness_from_sections(
        self,
        brand: Brand,
        identity: dict,
        menu: dict,
        media: dict,
    ) -> int:
        """Calculate completeness 0-100.

        Scoring:
        - Has dishes (20pts)
        - Has photos (20pts)
        - Has logo (15pts)
        - Has voice configured (15pts)
        - Has description (15pts)
        - Has locations (15pts)
        """
        score = 0

        if menu.get("total_dishes", 0) > 0:
            score += 20
        if media.get("total_assets", 0) > 0:
            score += 20
        if brand.logo_url:
            score += 15
        if brand.voice:
            score += 15
        if brand.description:
            score += 15
        if brand.locations:
            score += 15

        return min(score, 100)
