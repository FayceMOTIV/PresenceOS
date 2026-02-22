"""
PresenceOS - Community Manager Celery Tasks

Polling Google Business Profile reviews and publishing AI-generated replies.
"""
import asyncio
import structlog
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.models.brand import Brand
from app.models.cm_interaction import CMInteraction
from app.services.cm_agent import CMAgent
from app.services.google_reviews import GoogleReviewsService

logger = structlog.get_logger()


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


# ── Google Rating Mapping ────────────────────────────────────────────────────
# Google uses string enum: STAR_RATING_UNSPECIFIED, ONE, TWO, THREE, FOUR, FIVE
GOOGLE_RATING_MAP = {
    "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
}


@celery_app.task(bind=True, max_retries=2)
def poll_google_reviews(self, brand_id: str):
    """Poll Google Business Profile reviews for a single brand."""
    return run_async(_poll_google_reviews(self, brand_id))


async def _poll_google_reviews(task, brand_id: str):
    """Async implementation: fetch new reviews, classify, and generate responses."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            # Load brand with voice and knowledge
            result = await db.execute(
                select(Brand)
                .options(
                    selectinload(Brand.voice),
                    selectinload(Brand.knowledge_items),
                )
                .where(Brand.id == UUID(brand_id))
            )
            brand = result.scalar_one_or_none()
            if not brand:
                logger.warning("Brand not found for CM polling", brand_id=brand_id)
                return

            # Check if brand has Google connection metadata
            constraints = brand.constraints or {}
            google_config = constraints.get("google_business", {})
            access_token = google_config.get("access_token")
            account_id = google_config.get("account_id")
            location_id = google_config.get("location_id")

            if not all([access_token, account_id, location_id]):
                logger.debug("Brand has no Google Business Profile configured", brand_id=brand_id)
                return

            # Fetch reviews from Google
            gbp = GoogleReviewsService(access_token, account_id, location_id)
            try:
                reviews_data = await gbp.list_reviews(page_size=50)
            except Exception as exc:
                logger.error("Failed to fetch Google reviews", brand_id=brand_id, error=str(exc))
                return

            reviews = reviews_data.get("reviews", [])
            if not reviews:
                return

            agent = CMAgent(brand)
            new_count = 0

            for review in reviews:
                review_id = review.get("reviewId", "")
                if not review_id:
                    continue

                external_id = f"google_{review_id}"

                # Skip already-processed reviews
                existing = await db.execute(
                    select(CMInteraction).where(CMInteraction.external_id == external_id)
                )
                if existing.scalar_one_or_none():
                    continue

                # Extract review data
                reviewer = review.get("reviewer", {})
                commenter_name = reviewer.get("displayName", "Client Google")
                comment_text = review.get("comment", "")
                star_rating = GOOGLE_RATING_MAP.get(review.get("starRating", ""), None)

                if not comment_text and star_rating is None:
                    continue

                content = comment_text or f"Avis {star_rating} étoiles (sans commentaire)"

                # Classify
                classification_result = await agent.classify_interaction(content, star_rating)

                # Create interaction record
                interaction = CMInteraction(
                    brand_id=brand.id,
                    platform="google",
                    interaction_type="review",
                    external_id=external_id,
                    commenter_name=commenter_name,
                    content=content,
                    rating=star_rating,
                    sentiment_score=classification_result["sentiment_score"],
                    classification=classification_result["classification"],
                    confidence_score=classification_result["confidence"],
                    response_status="pending",
                    extra_metadata={
                        "google_review_id": review_id,
                        "reviewer_photo": reviewer.get("profilePhotoUrl"),
                        "create_time": review.get("createTime"),
                        "update_time": review.get("updateTime"),
                        "should_escalate": classification_result["should_escalate"],
                    },
                )
                db.add(interaction)
                await db.flush()

                # Generate AI response
                try:
                    gen_result = await agent.generate_response(interaction)
                    interaction.ai_response_draft = gen_result["response"]
                    interaction.ai_reasoning = gen_result["reasoning"]
                    interaction.confidence_score = gen_result["confidence"]

                    if gen_result["should_auto_publish"]:
                        interaction.response_status = "auto_published"
                        interaction.final_response = gen_result["response"]
                        interaction.published_at = datetime.now(timezone.utc)
                        # Schedule actual publishing
                        publish_google_reply.delay(str(interaction.id))
                except Exception as exc:
                    logger.error(
                        "Response generation failed",
                        external_id=external_id,
                        error=str(exc),
                    )

                new_count += 1

            await db.commit()
            logger.info(
                "Google review polling complete",
                brand_id=brand_id,
                new_interactions=new_count,
            )
    finally:
        await engine.dispose()


@celery_app.task
def poll_google_reviews_all():
    """Poll Google reviews for all brands that have GBP configured."""
    return run_async(_poll_google_reviews_all())


async def _poll_google_reviews_all():
    """Dispatch per-brand polling tasks."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            result = await db.execute(
                select(Brand.id, Brand.constraints).where(Brand.is_active.is_(True))
            )
            brands = result.all()

            dispatched = 0
            for brand_id, constraints in brands:
                google_config = (constraints or {}).get("google_business", {})
                if google_config.get("access_token"):
                    poll_google_reviews.delay(str(brand_id))
                    dispatched += 1

            logger.info("Dispatched Google review polling", count=dispatched)
    finally:
        await engine.dispose()


@celery_app.task(bind=True, max_retries=3)
def publish_google_reply(self, interaction_id: str):
    """Publish an approved reply to Google Business Profile."""
    return run_async(_publish_google_reply(self, interaction_id))


async def _publish_google_reply(task, interaction_id: str):
    """Async implementation: publish reply via GBP API."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            result = await db.execute(
                select(CMInteraction).where(CMInteraction.id == UUID(interaction_id))
            )
            interaction = result.scalar_one_or_none()
            if not interaction:
                logger.warning("Interaction not found", interaction_id=interaction_id)
                return

            response_text = interaction.final_response or interaction.ai_response_draft
            if not response_text:
                logger.warning("No response to publish", interaction_id=interaction_id)
                return

            # Load brand for Google config
            brand_result = await db.execute(
                select(Brand).where(Brand.id == interaction.brand_id)
            )
            brand = brand_result.scalar_one_or_none()
            if not brand:
                return

            google_config = (brand.constraints or {}).get("google_business", {})
            access_token = google_config.get("access_token")
            account_id = google_config.get("account_id")
            location_id = google_config.get("location_id")

            if not all([access_token, account_id, location_id]):
                logger.error("Missing Google config for publishing", brand_id=str(brand.id))
                return

            google_review_id = (interaction.extra_metadata or {}).get("google_review_id")
            if not google_review_id:
                logger.error("Missing Google review ID", interaction_id=interaction_id)
                return

            gbp = GoogleReviewsService(access_token, account_id, location_id)
            try:
                reply_result = await gbp.reply_to_review(google_review_id, response_text)

                interaction.response_status = "auto_published"
                interaction.published_at = datetime.now(timezone.utc)
                interaction.platform_response_id = reply_result.get("name", "")
                await db.commit()

                logger.info(
                    "Google reply published",
                    interaction_id=interaction_id,
                    review_id=google_review_id,
                )
            except Exception as exc:
                logger.error(
                    "Failed to publish Google reply",
                    interaction_id=interaction_id,
                    error=str(exc),
                )
                try:
                    task.retry(countdown=30)
                except task.MaxRetriesExceededError:
                    interaction.response_status = "pending"
                    interaction.extra_metadata = {
                        **(interaction.extra_metadata or {}),
                        "publish_error": str(exc),
                    }
                    await db.commit()
    finally:
        await engine.dispose()
