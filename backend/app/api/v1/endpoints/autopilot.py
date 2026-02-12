"""
PresenceOS - Autopilot API Endpoints (Sprint 9)
"""
import structlog
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, CurrentBrand, DBSession
from app.models.autopilot import (
    AutopilotConfig,
    PendingPost,
    PendingPostStatus,
    AutopilotFrequency,
)
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    PostStatus,
    ConnectorStatus,
    SocialPlatform,
)
from app.schemas.autopilot import (
    AutopilotConfigCreate,
    AutopilotConfigUpdate,
    AutopilotConfigResponse,
    PendingPostResponse,
    PendingPostAction,
)

logger = structlog.get_logger()

router = APIRouter()

FREQUENCY_MAP = {
    "daily": AutopilotFrequency.DAILY,
    "weekdays": AutopilotFrequency.WEEKDAYS,
    "3_per_week": AutopilotFrequency.THREE_PER_WEEK,
    "weekly": AutopilotFrequency.WEEKLY,
}


# ── Config CRUD ─────────────────────────────────────────────────────


@router.get("/brands/{brand_id}/autopilot", response_model=AutopilotConfigResponse)
async def get_autopilot_config(
    brand: CurrentBrand,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get autopilot configuration for a brand."""
    result = await db.execute(
        select(AutopilotConfig).where(AutopilotConfig.brand_id == brand.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autopilot config not found. Create one first.",
        )

    return config


@router.post(
    "/brands/{brand_id}/autopilot",
    response_model=AutopilotConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_autopilot_config(
    data: AutopilotConfigCreate,
    brand: CurrentBrand,
    db: DBSession,
    current_user: CurrentUser,
):
    """Create autopilot configuration for a brand."""
    # Check if config already exists
    existing = await db.execute(
        select(AutopilotConfig).where(AutopilotConfig.brand_id == brand.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Autopilot config already exists. Use PATCH to update.",
        )

    frequency = FREQUENCY_MAP.get(data.frequency, AutopilotFrequency.DAILY)

    config = AutopilotConfig(
        brand_id=brand.id,
        is_enabled=True,
        platforms=data.platforms,
        frequency=frequency,
        generation_hour=data.generation_hour,
        auto_publish=data.auto_publish,
        approval_window_hours=data.approval_window_hours,
        whatsapp_enabled=data.whatsapp_enabled,
        whatsapp_phone=data.whatsapp_phone,
        preferred_posting_time=data.preferred_posting_time,
        topics=data.topics,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    return config


@router.patch("/brands/{brand_id}/autopilot", response_model=AutopilotConfigResponse)
async def update_autopilot_config(
    data: AutopilotConfigUpdate,
    brand: CurrentBrand,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update autopilot configuration."""
    result = await db.execute(
        select(AutopilotConfig).where(AutopilotConfig.brand_id == brand.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autopilot config not found.",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Convert frequency string to enum
    if "frequency" in update_data:
        update_data["frequency"] = FREQUENCY_MAP.get(
            update_data["frequency"], AutopilotFrequency.DAILY
        )

    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


@router.post("/brands/{brand_id}/autopilot/toggle", response_model=AutopilotConfigResponse)
async def toggle_autopilot(
    brand: CurrentBrand,
    db: DBSession,
    current_user: CurrentUser,
):
    """Toggle autopilot on/off."""
    result = await db.execute(
        select(AutopilotConfig).where(AutopilotConfig.brand_id == brand.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autopilot config not found.",
        )

    config.is_enabled = not config.is_enabled
    await db.commit()
    await db.refresh(config)

    return config


# ── Pending Posts ────────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/autopilot/pending",
    response_model=list[PendingPostResponse],
)
async def list_pending_posts(
    brand: CurrentBrand,
    db: DBSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List pending posts for a brand."""
    query = (
        select(PendingPost)
        .where(PendingPost.brand_id == brand.id)
        .order_by(PendingPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status_filter:
        try:
            status_enum = PendingPostStatus(status_filter)
            query = query.where(PendingPost.status == status_enum)
        except ValueError:
            pass

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/autopilot/pending/{pending_post_id}",
    response_model=PendingPostResponse,
)
async def get_pending_post(
    pending_post_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get a single pending post."""
    result = await db.execute(
        select(PendingPost).where(PendingPost.id == pending_post_id)
    )
    pending = result.scalar_one_or_none()

    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending post not found.",
        )

    return pending


@router.post(
    "/autopilot/pending/{pending_post_id}/action",
    response_model=PendingPostResponse,
)
async def action_pending_post(
    pending_post_id: UUID,
    data: PendingPostAction,
    db: DBSession,
    current_user: CurrentUser,
):
    """Approve or reject a pending post from the dashboard."""
    result = await db.execute(
        select(PendingPost)
        .options(selectinload(PendingPost.config))
        .where(PendingPost.id == pending_post_id)
    )
    pending = result.scalar_one_or_none()

    if not pending:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending post not found.",
        )

    if pending.status != PendingPostStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post already processed: {pending.status.value}",
        )

    if data.action == "reject":
        pending.status = PendingPostStatus.REJECTED
        pending.reviewed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(pending)
        return pending

    # Approve: find connector
    platform_enum = _str_to_platform(pending.platform)

    connector_query = select(SocialConnector).where(
        SocialConnector.brand_id == pending.brand_id,
        SocialConnector.platform == platform_enum,
        SocialConnector.status == ConnectorStatus.CONNECTED,
        SocialConnector.is_active == True,
    )

    if data.connector_id:
        connector_query = connector_query.where(
            SocialConnector.id == data.connector_id
        )

    connector_result = await db.execute(connector_query)
    connector = connector_result.scalar_one_or_none()

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active connector found for {pending.platform}",
        )

    # Determine posting time
    posting_time = datetime.now(timezone.utc)
    if pending.config and pending.config.preferred_posting_time:
        try:
            h, m = pending.config.preferred_posting_time.split(":")
            posting_time = posting_time.replace(
                hour=int(h), minute=int(m), second=0
            )
            if posting_time < datetime.now(timezone.utc):
                posting_time += timedelta(days=1)
        except ValueError:
            pass

    # Create scheduled post
    scheduled = ScheduledPost(
        brand_id=pending.brand_id,
        connector_id=connector.id,
        scheduled_at=posting_time,
        status=PostStatus.SCHEDULED,
        content_snapshot={
            "caption": pending.caption,
            "hashtags": pending.hashtags or [],
            "media_urls": pending.media_urls or [],
        },
    )
    db.add(scheduled)

    pending.status = PendingPostStatus.APPROVED
    pending.reviewed_at = datetime.now(timezone.utc)
    pending.scheduled_post_id = scheduled.id

    if pending.config:
        pending.config.total_published += 1

    await db.commit()
    await db.refresh(pending)

    return pending


@router.post(
    "/brands/{brand_id}/autopilot/generate",
    response_model=list[PendingPostResponse],
)
async def trigger_generation(
    brand: CurrentBrand,
    db: DBSession,
    current_user: CurrentUser,
):
    """Manually trigger content generation for this brand."""
    from app.services.ai_service import AIService
    from app.workers.tasks import _build_autopilot_prompt
    from app.services.whatsapp import WhatsAppService

    result = await db.execute(
        select(AutopilotConfig).where(AutopilotConfig.brand_id == brand.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autopilot config not found.",
        )

    ai_service = AIService()
    wa = WhatsAppService()
    platforms = config.platforms or ["instagram"]
    created = []

    for platform in platforms:
        try:
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

            if not caption:
                continue

            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=config.approval_window_hours
            )

            pending = PendingPost(
                config_id=config.id,
                brand_id=brand.id,
                platform=platform,
                caption=caption,
                hashtags=parsed.get("hashtags", []),
                ai_reasoning=parsed.get("ai_reasoning"),
                virality_score=parsed.get("virality_score"),
                status=PendingPostStatus.PENDING,
                expires_at=expires_at,
            )
            db.add(pending)
            await db.flush()

            config.total_generated += 1

            # Send WhatsApp
            if config.whatsapp_enabled and config.whatsapp_phone:
                wamid = await wa.send_approval_message(
                    to_phone=config.whatsapp_phone,
                    pending_post_id=str(pending.id),
                    platform=platform,
                    caption_preview=caption,
                )
                if wamid:
                    pending.whatsapp_message_id = wamid

            created.append(pending)

        except Exception as e:
            logger.error(
                "Manual generation failed",
                brand_id=str(brand.id),
                platform=platform,
                error=str(e),
            )

    await db.commit()

    # Refresh all
    for p in created:
        await db.refresh(p)

    return created


# ── Helpers ──────────────────────────────────────────────────────────


def _str_to_platform(platform_str: str) -> SocialPlatform:
    mapping = {
        "instagram": SocialPlatform.INSTAGRAM,
        "tiktok": SocialPlatform.TIKTOK,
        "linkedin": SocialPlatform.LINKEDIN,
        "facebook": SocialPlatform.FACEBOOK,
    }
    return mapping.get(platform_str.lower(), SocialPlatform.INSTAGRAM)
