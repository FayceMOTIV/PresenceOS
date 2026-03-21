"""
EditorialCalendar — Génération et gestion du calendrier éditorial multi-niches.
Morpheus l'appelle via MCP. L'app mobile l'affiche avec swipe approve/reject.
"""
import json
import uuid
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.data.niches import detect_niche
from app.models.calendar_post import CalendarPost, PostStatus

logger = structlog.get_logger()

PLATFORM_SPECS = {
    "instagram_feed": {
        "aspect_ratio": "4:5",
        "caption_optimal": 150,
        "hashtags": "3-5",
        "best_hours": ["11:30", "14:00", "19:00"],
        "content_type": "image_or_video",
        "hook_required": False,
    },
    "instagram_reels": {
        "aspect_ratio": "9:16",
        "caption_optimal": 100,
        "hashtags": "3-5",
        "best_hours": ["09:00", "12:00", "18:00", "21:00"],
        "content_type": "video",
        "hook_required": True,
    },
    "instagram_story": {
        "aspect_ratio": "9:16",
        "caption_optimal": 0,
        "best_hours": ["08:00", "12:00", "20:00"],
        "content_type": "image_or_video",
        "ephemeral": True,
        "hook_required": False,
    },
    "facebook": {
        "aspect_ratio": "4:5",
        "caption_optimal": 300,
        "hashtags": "1-3",
        "best_hours": ["09:00", "12:30", "18:00"],
        "content_type": "image_or_video_or_text",
        "hook_required": False,
    },
    "tiktok": {
        "aspect_ratio": "9:16",
        "caption_optimal": 80,
        "hashtags": "3-5",
        "best_hours": ["07:00", "12:00", "18:00", "21:00"],
        "content_type": "video",
        "hook_required": True,
        "trending_audio": True,
    },
}


def _build_content_prompt(
    platform: str,
    content_type: str,
    niche_profile: dict,
    brand_dna: dict,
    pillar: str,
    date: datetime,
) -> str:
    spec_key = f"{platform}_{content_type}" if f"{platform}_{content_type}" in PLATFORM_SPECS else platform
    spec = PLATFORM_SPECS.get(spec_key, PLATFORM_SPECS.get("instagram_feed", {}))

    hook_note = "\n- HOOK obligatoire dans les 3 premières secondes" if spec.get("hook_required") else ""
    ephemeral_note = "\n- Contenu éphémère 24h : visuel seul suffit" if spec.get("ephemeral") else ""
    audio_note = "\n- Prévoir trending audio / son viral" if spec.get("trending_audio") else ""

    hooks_text = "\n".join(f"• {h}" for h in niche_profile.get("viral_hooks", [])[:3])
    constraints = ", ".join(niche_profile.get("legal_constraints", [])) or "Aucune"

    return f"""Génère un post {content_type} pour {platform} — {date.strftime('%A %d %B %Y')} — Business : {brand_dna.get('name', 'Ce business')} ({niche_profile['label']})

PILIER CONTENU : {pillar}

CONTRAINTES {platform.upper()} :
- Caption : maximum {spec.get('caption_optimal', 150)} caractères
- Hashtags : {spec.get('hashtags', '3-5')} hashtags pertinents{hook_note}{ephemeral_note}{audio_note}

HOOKS VIRAUX :
{hooks_text}

CONTRAINTES LÉGALES : {constraints}

Réponds UNIQUEMENT en JSON valide :
{{
  "caption": "texte du post",
  "hashtags": ["#hash1", "#hash2", "#hash3"],
  "visual_description": "description du visuel idéal",
  "hook": "accroche 3 premières secondes si vidéo, sinon null",
  "cta": "call to action adapté",
  "estimated_engagement": "low|medium|high|viral",
  "pillar": "{pillar}"
}}"""


class EditorialCalendar:

    def _select_platform_format(
        self,
        platforms: list[str],
        post_idx: int,
        niche: dict,
    ) -> tuple[str, str]:
        priority = niche.get("platforms_priority", platforms)
        available = [p for p in priority if p in platforms]
        if not available:
            available = platforms if platforms else ["instagram"]

        platform = available[post_idx % len(available)]
        video_ratio = niche.get("content_ratio", {}).get("video", 0.4)
        content_type = "reels" if (post_idx % 3 == 0 and video_ratio > 0.3) else "feed"

        return platform, content_type

    async def _generate_content(
        self,
        platform: str,
        content_type: str,
        niche: dict,
        brand_dna: dict,
        pillar: str,
        date: datetime,
    ) -> dict:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            prompt = _build_content_prompt(platform, content_type, niche, brand_dna, pillar, date)

            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except Exception as e:
            logger.error("Calendar content generation failed", error=str(e))
            return {
                "caption": f"Découvrez notre {pillar.lower()} !",
                "hashtags": ["#business"],
                "visual_description": f"Photo pour {pillar}",
                "cta": "En savoir plus",
                "estimated_engagement": "medium",
                "pillar": pillar,
            }

    async def generate_month(
        self,
        brand_id: uuid.UUID,
        posts_per_day: int,
        stories_per_day: int,
        platforms: list[str],
        month: datetime,
        db: AsyncSession,
    ) -> dict:
        from app.models.brand import Brand

        result = await db.execute(
            select(Brand).where(Brand.id == brand_id)
        )
        brand = result.scalar_one_or_none()
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")

        business_type = brand.niche or (brand.brand_type.value if brand.brand_type else "restaurant")
        niche = detect_niche(business_type)
        brand_dna = {
            "name": brand.name,
            "description": brand.description or "",
        }

        # Days of the month
        days: list[datetime] = []
        current = month.replace(day=1)
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        while current < next_month:
            days.append(current)
            current += timedelta(days=1)

        pillars = niche.get("content_pillars", ["Contenu générique"])
        created = 0

        for day in days:
            day_idx = day.day - 1

            # Posts
            for post_idx in range(posts_per_day):
                pillar = pillars[(day_idx + post_idx) % len(pillars)]
                platform, content_type = self._select_platform_format(
                    platforms, post_idx, niche
                )
                spec_key = f"{platform}_{content_type}"
                spec = PLATFORM_SPECS.get(spec_key, PLATFORM_SPECS.get(platform, {}))
                best_hours = spec.get("best_hours", ["12:00"])
                scheduled_time = best_hours[post_idx % len(best_hours)]

                content = await self._generate_content(
                    platform, content_type, niche, brand_dna, pillar, day
                )

                post = CalendarPost(
                    brand_id=brand_id,
                    platform=platform,
                    content_type=content_type,
                    caption=content.get("caption", ""),
                    hashtags=content.get("hashtags", []),
                    visual_description=content.get("visual_description", ""),
                    cta=content.get("cta", ""),
                    scheduled_date=day.strftime("%Y-%m-%d"),
                    scheduled_time=scheduled_time,
                    status=PostStatus.PENDING.value,
                    estimated_engagement=content.get("estimated_engagement", "medium"),
                    pillar=pillar,
                )
                db.add(post)
                created += 1

            # Stories
            for story_idx in range(stories_per_day):
                pillar = pillars[(day_idx + story_idx) % len(pillars)]
                spec = PLATFORM_SPECS.get("instagram_story", {})
                best_hours = spec.get("best_hours", ["08:00"])
                scheduled_time = best_hours[story_idx % len(best_hours)]

                content = await self._generate_content(
                    "instagram", "story", niche, brand_dna, pillar, day
                )

                story = CalendarPost(
                    brand_id=brand_id,
                    platform="instagram",
                    content_type="story",
                    caption=content.get("caption", ""),
                    hashtags=[],
                    visual_description=content.get("visual_description", ""),
                    cta="",
                    scheduled_date=day.strftime("%Y-%m-%d"),
                    scheduled_time=scheduled_time,
                    status=PostStatus.PENDING.value,
                    estimated_engagement="medium",
                    pillar=pillar,
                )
                db.add(story)
                created += 1

        await db.commit()

        return {
            "brand_id": str(brand_id),
            "month": month.strftime("%B %Y"),
            "total_posts": created,
            "posts_per_day": posts_per_day,
            "stories_per_day": stories_per_day,
            "platforms": platforms,
            "status": "generated",
            "pending_approval": created,
        }

    async def approve_post(
        self,
        post_id: uuid.UUID,
        brand_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict:
        result = await db.execute(
            select(CalendarPost).where(
                CalendarPost.id == post_id,
                CalendarPost.brand_id == brand_id,
            )
        )
        post = result.scalar_one_or_none()
        if not post:
            raise ValueError(f"Post {post_id} not found")

        post.status = PostStatus.APPROVED.value
        await db.commit()
        return {"post_id": str(post_id), "status": "approved"}

    async def reject_post(
        self,
        post_id: uuid.UUID,
        brand_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict:
        result = await db.execute(
            select(CalendarPost).where(
                CalendarPost.id == post_id,
                CalendarPost.brand_id == brand_id,
            )
        )
        post = result.scalar_one_or_none()
        if not post:
            raise ValueError(f"Post {post_id} not found")

        post.status = PostStatus.REJECTED.value
        await db.commit()
        return {"post_id": str(post_id), "status": "rejected"}

    async def approve_all_pending(
        self,
        brand_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict:
        result = await db.execute(
            select(CalendarPost).where(
                CalendarPost.brand_id == brand_id,
                CalendarPost.status == PostStatus.PENDING.value,
            )
        )
        pending = list(result.scalars().all())

        for post in pending:
            post.status = PostStatus.APPROVED.value
        await db.commit()

        return {"approved": len(pending), "message": f"{len(pending)} posts approuvés"}

    async def get_calendar(
        self,
        brand_id: uuid.UUID,
        db: AsyncSession,
        month: str | None = None,
        platform: str | None = None,
        status: str | None = None,
    ) -> dict:
        query = select(CalendarPost).where(CalendarPost.brand_id == brand_id)

        if month:
            query = query.where(CalendarPost.scheduled_date.like(f"{month}%"))
        if platform:
            query = query.where(CalendarPost.platform == platform)
        if status:
            query = query.where(CalendarPost.status == status)

        query = query.order_by(CalendarPost.scheduled_date, CalendarPost.scheduled_time)

        result = await db.execute(query)
        posts = list(result.scalars().all())

        return {
            "brand_id": str(brand_id),
            "total": len(posts),
            "posts": [
                {
                    "id": str(p.id),
                    "platform": p.platform,
                    "content_type": p.content_type,
                    "caption": p.caption or "",
                    "hashtags": p.hashtags or [],
                    "visual_description": p.visual_description or "",
                    "visual_url": p.visual_url,
                    "video_url": p.video_url,
                    "cta": p.cta or "",
                    "scheduled_date": p.scheduled_date,
                    "scheduled_time": p.scheduled_time,
                    "status": p.status,
                    "estimated_engagement": p.estimated_engagement or "medium",
                    "pillar": p.pillar or "",
                }
                for p in posts
            ],
        }


editorial_calendar = EditorialCalendar()
