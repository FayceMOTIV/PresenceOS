"""
PresenceOS - Celery Tasks
"""
import asyncio
import structlog
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.connectors.factory import get_connector_handler
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    SocialPlatform,
    PublishJob,
    MetricsSnapshot,
    PostStatus,
    JobStatus,
    ConnectorStatus,
)
from app.models.brand import Brand
from app.models.content import ContentIdea, IdeaSource, IdeaStatus
from app.models.audit import AuditLog, AuditAction
from app.models.autopilot import (
    AutopilotConfig,
    PendingPost,
    PendingPostStatus,
    AutopilotFrequency,
)
from app.services.ai_service import AIService
from app.services.whatsapp import WhatsAppService

logger = structlog.get_logger()


def _make_session_maker():
    """Create a fresh engine + session maker for each Celery task.

    This avoids the 'Future attached to a different loop' error that happens
    when the module-level engine (created at import time) is reused across
    Celery forked workers with different event loops.
    """
    eng = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
    )
    return async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False), eng


def run_async(coro):
    """Helper to run async code in Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Exponential backoff: 10s, 30s, 90s
PUBLISH_RETRY_DELAYS = [10, 30, 90]


@celery_app.task(bind=True, max_retries=3)
def publish_post_task(self, scheduled_post_id: str):
    """Publish a scheduled post."""
    return run_async(_publish_post(self, scheduled_post_id))


async def _publish_post(task, scheduled_post_id: str):
    """Async implementation of post publishing."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            try:
                # Get scheduled post with connector
                result = await db.execute(
                    select(ScheduledPost)
                    .options(selectinload(ScheduledPost.connector))
                    .where(ScheduledPost.id == scheduled_post_id)
                )
                post = result.scalar_one_or_none()

                if not post:
                    logger.error("Scheduled post not found", post_id=scheduled_post_id)
                    return {"status": "error", "message": "Post not found"}

                if post.status != PostStatus.QUEUED:
                    logger.info("Post not in queued status", post_id=scheduled_post_id, status=post.status)
                    return {"status": "skipped", "message": f"Post status is {post.status}"}

                connector = post.connector
                if not connector or connector.status != ConnectorStatus.CONNECTED:
                    post.status = PostStatus.FAILED
                    post.last_error = "Connector not connected"
                    await db.commit()
                    return {"status": "error", "message": "Connector not connected"}

                # Create publish job
                job = PublishJob(
                    scheduled_post_id=post.id,
                    status=JobStatus.PROCESSING,
                    attempt_number=post.retry_count + 1,
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=task.request.id,
                )
                db.add(job)
                post.status = PostStatus.PUBLISHING
                await db.commit()

                # Get connector handler
                handler = get_connector_handler(connector.platform)

                # Decrypt access token
                access_token = handler.decrypt_token(connector.access_token_encrypted)

                # Prepare content
                content = post.content_snapshot.copy()
                content["account_id"] = connector.account_id
                content["account_username"] = connector.account_username
                if connector.platform_data:
                    content.update(connector.platform_data)

                # Publish
                try:
                    result = await handler.publish(
                        access_token=access_token,
                        content=content,
                        media_urls=post.content_snapshot.get("media_urls"),
                    )

                    # Update post with success
                    post.status = PostStatus.PUBLISHED
                    post.platform_post_id = result["post_id"]
                    post.platform_post_url = result.get("post_url")
                    post.published_at = result["published_at"]

                    # Update job
                    job.status = JobStatus.SUCCESS
                    job.completed_at = datetime.now(timezone.utc)
                    job.platform_response = result.get("platform_response")

                    # Update connector daily count
                    connector.daily_posts_count += 1

                    await db.commit()

                    logger.info(
                        "Post published successfully",
                        post_id=scheduled_post_id,
                        platform_post_id=result["post_id"],
                    )

                    return {"status": "success", "post_id": result["post_id"]}

                except Exception as e:
                    error_msg = str(e)
                    logger.error("Publishing failed", post_id=scheduled_post_id, error=error_msg)

                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(timezone.utc)
                    job.error_message = error_msg

                    post.retry_count += 1
                    post.last_error = error_msg

                    if post.retry_count < 3:
                        post.status = PostStatus.QUEUED
                        job.status = JobStatus.RETRYING
                        countdown = PUBLISH_RETRY_DELAYS[min(post.retry_count - 1, len(PUBLISH_RETRY_DELAYS) - 1)]
                        await db.commit()
                        task.retry(countdown=countdown)
                    else:
                        post.status = PostStatus.FAILED

                        audit_entry = AuditLog(
                            user_id=None,
                            action=AuditAction.POST_FAIL,
                            resource_type="scheduled_post",
                            resource_id=post.id,
                            details={
                                "connector_id": str(connector.id),
                                "platform": connector.platform.value if hasattr(connector.platform, "value") else str(connector.platform),
                                "retry_count": post.retry_count,
                                "error": error_msg[:500],
                            },
                            success=False,
                            error_message=error_msg[:1000],
                        )
                        db.add(audit_entry)

                    await db.commit()
                    raise

            except Exception as e:
                logger.exception("Publish task failed", post_id=scheduled_post_id)
                raise
    finally:
        await engine.dispose()


@celery_app.task
def check_scheduled_posts():
    """Check for posts that need to be published."""
    return run_async(_check_scheduled_posts())


async def _check_scheduled_posts():
    """Find and queue posts scheduled for now."""
    session_maker, engine = _make_session_maker()
    try:
        async with session_maker() as db:
            now = datetime.now(timezone.utc)
            window = now + timedelta(minutes=1)

            result = await db.execute(
                select(ScheduledPost)
                .where(
                    ScheduledPost.status == PostStatus.SCHEDULED,
                    ScheduledPost.scheduled_at <= window,
                )
            )
            posts = result.scalars().all()

            queued_count = 0
            for post in posts:
                post.status = PostStatus.QUEUED
                queued_count += 1
                # Dispatch publish task
                publish_post_task.delay(str(post.id))

            await db.commit()

            logger.info("Checked scheduled posts", queued=queued_count)
            return {"queued": queued_count}
    finally:
        await engine.dispose()


@celery_app.task
def sync_connector_metrics(connector_id: str):
    """Sync metrics for a specific connector."""
    return run_async(_sync_connector_metrics(connector_id))


async def _sync_connector_metrics(connector_id: str):
    """Fetch and store latest metrics for a connector."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(SocialConnector).where(SocialConnector.id == connector_id)
        )
        connector = result.scalar_one_or_none()

        if not connector or connector.status != ConnectorStatus.CONNECTED:
            return {"status": "skipped"}

        handler = get_connector_handler(connector.platform)
        access_token = handler.decrypt_token(connector.access_token_encrypted)

        # Get account metrics
        try:
            account_metrics = await handler.get_account_metrics(access_token)

            # Create account-level snapshot
            snapshot = MetricsSnapshot(
                connector_id=connector.id,
                snapshot_date=datetime.now(timezone.utc),
                followers_count=account_metrics.get("followers_count"),
                followers_gained=account_metrics.get("followers_gained"),
                raw_data=account_metrics,
            )
            db.add(snapshot)

            connector.last_sync_at = datetime.now(timezone.utc)
            await db.commit()

            return {"status": "success"}

        except Exception as e:
            logger.error("Metrics sync failed", connector_id=connector_id, error=str(e))
            connector.last_error = str(e)
            await db.commit()
            return {"status": "error", "message": str(e)}


@celery_app.task
def sync_all_metrics():
    """Sync metrics for all active connectors."""
    return run_async(_sync_all_metrics())


async def _sync_all_metrics():
    """Find all active connectors and sync their metrics."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(SocialConnector).where(
                SocialConnector.status == ConnectorStatus.CONNECTED,
                SocialConnector.is_active == True,
            )
        )
        connectors = result.scalars().all()

        for connector in connectors:
            sync_connector_metrics.delay(str(connector.id))

        return {"dispatched": len(connectors)}


@celery_app.task
def generate_daily_ideas():
    """Generate daily content ideas for all active brands."""
    return run_async(_generate_daily_ideas())


async def _generate_daily_ideas():
    """Generate ideas for each active brand."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(Brand)
            .options(selectinload(Brand.voice))
            .where(Brand.is_active == True)
        )
        brands = result.scalars().all()

        ai_service = AIService()
        generated_count = 0

        for brand in brands:
            try:
                ideas = await ai_service.generate_ideas(brand=brand, count=3)

                for idea_data in ideas:
                    idea = ContentIdea(
                        brand_id=brand.id,
                        title=idea_data.title,
                        description=idea_data.description,
                        source=IdeaSource.AI_GENERATED,
                        status=IdeaStatus.NEW,
                        content_pillar=idea_data.content_pillar,
                        target_platforms=idea_data.target_platforms,
                        hooks=idea_data.hooks,
                        ai_reasoning=idea_data.ai_reasoning,
                        suggested_date=idea_data.suggested_date,
                    )
                    db.add(idea)
                    generated_count += 1

            except Exception as e:
                logger.error("Failed to generate ideas for brand", brand_id=str(brand.id), error=str(e))

        await db.commit()
        logger.info("Daily ideas generated", count=generated_count)
        return {"generated": generated_count}


@celery_app.task
def refresh_expiring_tokens():
    """Refresh tokens that are about to expire."""
    return run_async(_refresh_expiring_tokens())


async def _refresh_expiring_tokens():
    """Find connectors with expiring tokens and refresh them."""
    async with async_session_maker() as db:
        # Find tokens expiring in the next 7 days
        expiry_threshold = datetime.now(timezone.utc) + timedelta(days=7)

        result = await db.execute(
            select(SocialConnector).where(
                SocialConnector.status == ConnectorStatus.CONNECTED,
                SocialConnector.token_expires_at <= expiry_threshold,
                SocialConnector.refresh_token_encrypted.isnot(None),
            )
        )
        connectors = result.scalars().all()

        refreshed_count = 0
        for connector in connectors:
            try:
                handler = get_connector_handler(connector.platform)
                refresh_token = handler.decrypt_token(connector.refresh_token_encrypted)

                token_data = await handler.refresh_token(refresh_token)

                connector.access_token_encrypted = handler.encrypt_token(token_data["access_token"])
                if token_data.get("refresh_token"):
                    connector.refresh_token_encrypted = handler.encrypt_token(token_data["refresh_token"])
                connector.token_expires_at = token_data.get("expires_at")
                connector.last_error = None

                refreshed_count += 1

            except Exception as e:
                logger.error("Token refresh failed", connector_id=str(connector.id), error=str(e))
                connector.status = ConnectorStatus.EXPIRED
                connector.last_error = str(e)

        await db.commit()
        logger.info("Tokens refreshed", count=refreshed_count)
        return {"refreshed": refreshed_count}


# ── Autopilot Tasks (Sprint 9) ─────────────────────────────────────


@celery_app.task
def autopilot_daily_generate():
    """Generate autopilot content for all enabled brands."""
    return run_async(_autopilot_daily_generate())


async def _autopilot_daily_generate():
    """Generate posts for each brand with autopilot enabled."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(AutopilotConfig)
            .options(selectinload(AutopilotConfig.brand))
            .where(
                AutopilotConfig.is_enabled == True,
            )
        )
        configs = result.scalars().all()

        wa = WhatsAppService()
        ai_service = AIService()
        generated_count = 0

        for config in configs:
            # Check frequency (skip if not a generation day)
            if not _should_generate_today(config.frequency):
                continue

            brand = config.brand
            if not brand or not brand.is_active:
                continue

            platforms = config.platforms or ["instagram"]

            for platform in platforms:
                try:
                    # Generate content using AI
                    topic_hint = ""
                    if config.topics:
                        import random
                        topic_hint = random.choice(config.topics)

                    prompt = _build_autopilot_prompt(brand, platform, topic_hint)
                    raw = await ai_service._complete(
                        prompt=prompt,
                        system="Tu es un expert en contenu social media. Reponds en JSON.",
                        max_tokens=2000,
                        temperature=0.8,
                    )

                    parsed = ai_service._parse_json_response(raw)
                    caption = parsed.get("caption", "")
                    hashtags = parsed.get("hashtags", [])

                    if not caption:
                        continue

                    # Calculate expiry
                    expires_at = datetime.now(timezone.utc) + timedelta(
                        hours=config.approval_window_hours
                    )

                    # Create pending post
                    pending = PendingPost(
                        config_id=config.id,
                        brand_id=brand.id,
                        platform=platform,
                        caption=caption,
                        hashtags=hashtags,
                        ai_reasoning=parsed.get("ai_reasoning"),
                        virality_score=parsed.get("virality_score"),
                        status=PendingPostStatus.PENDING,
                        expires_at=expires_at,
                    )
                    db.add(pending)
                    await db.flush()

                    # Update stats
                    config.total_generated += 1
                    generated_count += 1

                    # Send WhatsApp notification
                    if config.whatsapp_enabled and config.whatsapp_phone:
                        wamid = await wa.send_approval_message(
                            to_phone=config.whatsapp_phone,
                            pending_post_id=str(pending.id),
                            platform=platform,
                            caption_preview=caption,
                        )
                        if wamid:
                            pending.whatsapp_message_id = wamid

                except Exception as e:
                    logger.error(
                        "Autopilot generation failed",
                        brand_id=str(brand.id),
                        platform=platform,
                        error=str(e),
                    )

        await db.commit()
        logger.info("Autopilot daily generation complete", generated=generated_count)
        return {"generated": generated_count}


@celery_app.task
def autopilot_check_auto_publish():
    """Check pending posts past their approval window and auto-publish if configured."""
    return run_async(_autopilot_check_auto_publish())


async def _autopilot_check_auto_publish():
    """Auto-publish expired pending posts when auto_publish is enabled."""
    async with async_session_maker() as db:
        now = datetime.now(timezone.utc)

        # Find pending posts past their expiry
        result = await db.execute(
            select(PendingPost)
            .options(selectinload(PendingPost.config))
            .where(
                PendingPost.status == PendingPostStatus.PENDING,
                PendingPost.expires_at <= now,
            )
        )
        expired_posts = result.scalars().all()

        published_count = 0
        expired_count = 0

        for pending in expired_posts:
            config = pending.config
            if config and config.auto_publish:
                # Auto-publish: find a connector and create scheduled post
                platform_enum = _str_to_platform_enum(pending.platform)
                connector_result = await db.execute(
                    select(SocialConnector).where(
                        SocialConnector.brand_id == pending.brand_id,
                        SocialConnector.platform == platform_enum,
                        SocialConnector.status == ConnectorStatus.CONNECTED,
                        SocialConnector.is_active == True,
                    )
                )
                connector = connector_result.scalar_one_or_none()

                if connector:
                    scheduled = ScheduledPost(
                        brand_id=pending.brand_id,
                        connector_id=connector.id,
                        scheduled_at=now,
                        status=PostStatus.SCHEDULED,
                        content_snapshot={
                            "caption": pending.caption,
                            "hashtags": pending.hashtags or [],
                            "media_urls": pending.media_urls or [],
                        },
                    )
                    db.add(scheduled)
                    pending.status = PendingPostStatus.AUTO_PUBLISHED
                    pending.reviewed_at = now
                    pending.scheduled_post_id = scheduled.id

                    if config:
                        config.total_published += 1

                    published_count += 1

                    # Notify via WhatsApp
                    if config.whatsapp_enabled and config.whatsapp_phone:
                        wa = WhatsAppService()
                        await wa.send_text_message(
                            config.whatsapp_phone,
                            f"Post {pending.platform} auto-publie (pas de reponse dans le delai).",
                        )
                else:
                    pending.status = PendingPostStatus.EXPIRED
                    pending.reviewed_at = now
                    expired_count += 1
            else:
                # No auto-publish — just expire
                pending.status = PendingPostStatus.EXPIRED
                pending.reviewed_at = now
                expired_count += 1

        await db.commit()
        logger.info(
            "Autopilot auto-publish check",
            published=published_count,
            expired=expired_count,
        )
        return {"published": published_count, "expired": expired_count}


def _should_generate_today(frequency: AutopilotFrequency) -> bool:
    """Check if content should be generated based on frequency setting."""
    today = datetime.now(timezone.utc).weekday()  # 0=Monday, 6=Sunday

    if frequency == AutopilotFrequency.DAILY:
        return True
    elif frequency == AutopilotFrequency.WEEKDAYS:
        return today < 5  # Mon-Fri
    elif frequency == AutopilotFrequency.THREE_PER_WEEK:
        return today in (0, 2, 4)  # Mon, Wed, Fri
    elif frequency == AutopilotFrequency.WEEKLY:
        return today == 0  # Monday
    return True


def _build_autopilot_prompt(brand: Brand, platform: str, topic_hint: str = "") -> str:
    """Build AI prompt for autopilot content generation."""
    voice = brand.voice
    tone_info = ""
    if voice:
        tone_info = f"""
Ton formel: {voice.tone_formal}/100
Ton joueur: {voice.tone_playful}/100
Ton audacieux: {voice.tone_bold}/100
Mots a eviter: {', '.join(voice.words_to_avoid or [])}
Mots a privilegier: {', '.join(voice.words_to_prefer or [])}
Instructions: {voice.custom_instructions or 'aucune'}
"""

    topic_line = f"\nTheme suggere: {topic_hint}" if topic_hint else ""

    return f"""Genere un post {platform} pour la marque "{brand.name}".

Description: {brand.description or 'Non specifie'}
Type: {brand.brand_type.value if hasattr(brand.brand_type, 'value') else brand.brand_type}
Cible: {brand.target_persona or 'Non specifie'}
Localisations: {', '.join(brand.locations or []) or 'Non specifie'}

VOIX DE MARQUE:
{tone_info}
{topic_line}

Reponds en JSON:
{{
  "caption": "le texte du post (adapte au format {platform})",
  "hashtags": ["hashtag1", "hashtag2"],
  "ai_reasoning": "pourquoi ce contenu est pertinent",
  "virality_score": 7.5
}}
"""


def _str_to_platform_enum(platform_str: str) -> SocialPlatform:
    """Convert platform string to SocialPlatform enum."""
    mapping = {
        "instagram": SocialPlatform.INSTAGRAM,
        "tiktok": SocialPlatform.TIKTOK,
        "linkedin": SocialPlatform.LINKEDIN,
        "facebook": SocialPlatform.FACEBOOK,
    }
    return mapping.get(platform_str.lower(), SocialPlatform.INSTAGRAM)


# ── AI Agent Crew Tasks (Phase 1) ─────────────────────────────────


@celery_app.task(bind=True, max_retries=1, time_limit=300, soft_time_limit=280)
def agent_generate_content(
    self,
    brand_id: str,
    platforms: list[str],
    num_posts: int = 3,
    topic: str | None = None,
    industry: str | None = None,
    tone: str | None = None,
):
    """Run the Content Crew via Celery for async processing."""
    try:
        from app.agents.crews.content_crew import run_content_crew

        result = run_content_crew(
            brand_id=brand_id,
            platforms=platforms,
            num_posts=num_posts,
            topic=topic,
            industry=industry,
            tone=tone,
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.error("Agent content generation failed", brand_id=brand_id, error=str(e))
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=1, time_limit=180, soft_time_limit=160)
def agent_scan_trends(
    self,
    brand_id: str,
    industry: str,
    platforms: list[str] | None = None,
):
    """Run the Trends Crew via Celery for async processing."""
    try:
        from app.agents.crews.trends_crew import run_trends_crew

        result = run_trends_crew(
            brand_id=brand_id,
            industry=industry,
            platforms=platforms or ["instagram", "linkedin"],
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.error("Agent trend scan failed", brand_id=brand_id, error=str(e))
        return {"status": "failed", "error": str(e)}


@celery_app.task(bind=True, max_retries=1, time_limit=180, soft_time_limit=160)
def agent_analyze_brand(self, website_url: str):
    """Run the Onboarding Crew extraction via Celery."""
    try:
        from app.agents.crews.onboarding_crew import run_onboarding_extraction

        result = run_onboarding_extraction(website_url)
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.error("Agent brand analysis failed", url=website_url, error=str(e))
        return {"status": "failed", "error": str(e)}


# ── WhatsApp Content Generation (Sprint 9C) ─────────────────────────


@celery_app.task(bind=True, max_retries=2)
def generate_whatsapp_content(self, pending_post_id: str):
    """
    Generate enhanced content for a WhatsApp-created pending post.

    This task:
    1. Loads the pending post + brand context
    2. Uses AI to enhance the caption
    3. Optionally produces a video if media is available
    4. Updates the pending post with enhanced content
    5. Sends WhatsApp approval message
    """
    return run_async(_generate_whatsapp_content(self, pending_post_id))


async def _generate_whatsapp_content(task, pending_post_id: str):
    """Async implementation of WhatsApp content generation."""
    async with async_session_maker() as db:
        try:
            # Load pending post with config and brand
            result = await db.execute(
                select(PendingPost)
                .options(
                    selectinload(PendingPost.config).selectinload(AutopilotConfig.brand).selectinload(Brand.voice),
                )
                .where(PendingPost.id == pending_post_id)
            )
            pending = result.scalar_one_or_none()

            if not pending:
                logger.error("Pending post not found for content gen", id=pending_post_id)
                return {"status": "error", "message": "Not found"}

            if pending.status != PendingPostStatus.PENDING:
                return {"status": "skipped", "message": f"Status is {pending.status}"}

            brand = pending.config.brand if pending.config else None
            if not brand:
                logger.error("No brand found for pending post", id=pending_post_id)
                return {"status": "error", "message": "No brand"}

            ai_service = AIService()
            wa = WhatsAppService()

            # Step 1: Enhance caption with AI + brand voice
            try:
                enhanced = await ai_service.enhance_caption(
                    brand=brand,
                    caption=pending.caption,
                    platform=pending.platform,
                )
                if enhanced.get("caption"):
                    pending.caption = enhanced["caption"]
                if enhanced.get("hashtags"):
                    pending.hashtags = enhanced["hashtags"]
            except Exception as e:
                logger.warning("Caption enhancement failed", error=str(e))

            # Step 2: Produce video if we have media
            if pending.media_urls:
                try:
                    from app.services.video_producer import VideoProducer

                    producer = VideoProducer()
                    media_types = ["image" if not u.endswith(".mp4") else "video" for u in pending.media_urls]

                    video_result = await producer.produce(
                        media_urls=pending.media_urls,
                        media_types=media_types,
                        caption=pending.caption,
                        brand_id=str(pending.brand_id),
                        include_voiceover=True,
                        include_music=True,
                        include_broll=True,
                    )

                    if video_result:
                        # Add video URL to media_urls
                        pending.media_urls = list(pending.media_urls or []) + [video_result["url"]]
                        pending.ai_reasoning = (pending.ai_reasoning or "") + " | Video produite automatiquement"

                except Exception as e:
                    logger.warning("Video production failed in task", error=str(e))

            # Step 3: Update and save
            await db.commit()

            # Step 4: Send WhatsApp approval message
            if pending.config and pending.config.whatsapp_enabled and pending.config.whatsapp_phone:
                caption_preview = pending.caption[:300]
                wamid = await wa.send_approval_message(
                    to_phone=pending.config.whatsapp_phone,
                    pending_post_id=str(pending.id),
                    platform=pending.platform,
                    caption_preview=caption_preview,
                )
                if wamid:
                    pending.whatsapp_message_id = wamid
                    await db.commit()

            logger.info(
                "WhatsApp content generated",
                pending_post_id=pending_post_id,
                has_video=bool(pending.media_urls),
            )

            return {"status": "success", "pending_post_id": pending_post_id}

        except Exception as e:
            logger.error("WhatsApp content generation failed", error=str(e))
            try:
                task.retry(countdown=30)
            except Exception:
                pass
            return {"status": "error", "message": str(e)}
