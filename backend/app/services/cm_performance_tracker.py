"""
PresenceOS - CM Performance Tracker (F2: Boucle de Performance)

Detects when a CM Chat proposal gets published, then feeds the engagement
data back into BrandBrain so the AI learns what works.

Zero additional cost: uses existing BrandBrain.post_published_learning().
"""
import structlog
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_proposal import AIProposal
from app.models.publishing import MetricsSnapshot, ScheduledPost, PostStatus
from app.services.brand_brain import BrandBrain

logger = structlog.get_logger()


class CMPerformanceTracker:
    """
    Scans published posts that originated from CM Chat proposals,
    collects their metrics, and feeds them to BrandBrain for learning.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_published_proposals(self, brand_id: UUID) -> int:
        """
        Find CM Chat proposals that were published and have metrics,
        then feed the learnings to BrandBrain.

        Returns the number of proposals processed.
        """
        # Find recent published posts with metrics, from CM Chat source
        # Look at posts published in the last 7 days that haven't been tracked yet
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        result = await self.db.execute(
            select(AIProposal)
            .where(
                AIProposal.brand_id == brand_id,
                AIProposal.source == "cm_chat",
                AIProposal.status == "published",
            )
            .order_by(AIProposal.updated_at.desc())
            .limit(20)
        )
        proposals = result.scalars().all()

        if not proposals:
            return 0

        brain = BrandBrain(brand_id, self.db)
        processed = 0

        for proposal in proposals:
            # Check if we already learned from this proposal
            brain_ctx = proposal.brain_context or {}
            if brain_ctx.get("brain_learned"):
                continue

            # Try to find matching ScheduledPost with metrics
            caption = proposal.caption or ""
            platform = proposal.platform or "instagram"

            # Look for a published post that matches this proposal's caption
            post_result = await self.db.execute(
                select(ScheduledPost)
                .options(selectinload(ScheduledPost.metrics))
                .where(
                    ScheduledPost.brand_id == brand_id,
                    ScheduledPost.status == PostStatus.PUBLISHED,
                    ScheduledPost.published_at >= cutoff,
                )
                .order_by(ScheduledPost.published_at.desc())
                .limit(50)
            )
            published_posts = post_result.scalars().all()

            # Match by caption similarity (simple substring check)
            matched_post = None
            for post in published_posts:
                snapshot = post.content_snapshot or {}
                post_caption = snapshot.get("caption", "")
                # Match if the caption starts with the same 50 chars
                if caption[:50] and post_caption[:50] and caption[:50] == post_caption[:50]:
                    matched_post = post
                    break

            if not matched_post or not matched_post.metrics:
                continue

            # Extract engagement from MetricsSnapshot
            metrics: MetricsSnapshot = matched_post.metrics
            engagement = {
                "likes": metrics.likes or 0,
                "comments": metrics.comments or 0,
                "shares": metrics.shares or 0,
                "saves": metrics.saves or 0,
                "impressions": metrics.impressions or 0,
                "reach": metrics.reach or 0,
                "engagement_rate": metrics.engagement_rate or 0.0,
            }

            # Feed to BrandBrain
            await brain.post_published_learning(
                caption=caption[:200],
                platform=platform,
                engagement=engagement,
            )

            # Mark proposal as learned (avoid double-counting)
            if hasattr(proposal, "metadata_json"):
                proposal.metadata_json = {
                    **(proposal.metadata_json or {}),
                    "brain_learned": True,
                    "learned_at": datetime.now(timezone.utc).isoformat(),
                }

            processed += 1
            logger.info(
                "CM Performance tracked",
                brand_id=str(brand_id),
                proposal_id=str(proposal.id),
                engagement_rate=engagement["engagement_rate"],
            )

        if processed > 0:
            await self.db.commit()

        return processed
