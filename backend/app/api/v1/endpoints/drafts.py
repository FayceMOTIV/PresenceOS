"""
PresenceOS - Content Drafts Endpoints
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.content import ContentDraft, ContentVariant, DraftStatus, Platform
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    PostStatus,
    ConnectorStatus,
)
from app.schemas.content import (
    ContentDraftCreate,
    ContentDraftUpdate,
    ContentDraftResponse,
    ContentDraftListResponse,
    ContentVariantResponse,
)
from app.schemas.publishing import DraftScheduleRequest, DraftScheduleResponse

router = APIRouter()


@router.get("/brands/{brand_id}", response_model=list[ContentDraftListResponse])
async def list_drafts(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    status_filter: DraftStatus | None = None,
    platform: Platform | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    """List content drafts for a brand."""
    await get_brand(brand_id, current_user, db)

    query = select(ContentDraft).where(ContentDraft.brand_id == brand_id)

    if status_filter:
        query = query.where(ContentDraft.status == status_filter)
    if platform:
        query = query.where(ContentDraft.platform == platform)

    query = query.order_by(ContentDraft.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    drafts = result.scalars().all()

    return [ContentDraftListResponse.model_validate(draft) for draft in drafts]


@router.post("/brands/{brand_id}", response_model=ContentDraftResponse)
async def create_draft(
    brand_id: UUID,
    data: ContentDraftCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a new content draft manually."""
    await get_brand(brand_id, current_user, db)

    draft = ContentDraft(brand_id=brand_id, **data.model_dump())
    db.add(draft)
    await db.commit()

    # Reload with variants
    result = await db.execute(
        select(ContentDraft)
        .options(selectinload(ContentDraft.variants))
        .where(ContentDraft.id == draft.id)
    )
    draft = result.scalar_one()

    return ContentDraftResponse.model_validate(draft)


@router.get("/{draft_id}", response_model=ContentDraftResponse)
async def get_draft(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get a specific content draft with variants."""
    result = await db.execute(
        select(ContentDraft)
        .options(selectinload(ContentDraft.variants))
        .where(ContentDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    return ContentDraftResponse.model_validate(draft)


@router.patch("/{draft_id}", response_model=ContentDraftResponse)
async def update_draft(
    draft_id: UUID,
    data: ContentDraftUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update a content draft."""
    result = await db.execute(
        select(ContentDraft)
        .options(selectinload(ContentDraft.variants))
        .where(ContentDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    if draft.status in [DraftStatus.SCHEDULED, DraftStatus.PUBLISHED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit a {draft.status.value} draft",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)

    await db.commit()
    await db.refresh(draft)

    return ContentDraftResponse.model_validate(draft)


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete a content draft."""
    result = await db.execute(select(ContentDraft).where(ContentDraft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    if draft.status in [DraftStatus.SCHEDULED, DraftStatus.PUBLISHED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete a {draft.status.value} draft",
        )

    await db.delete(draft)
    await db.commit()

    return {"message": "Draft deleted"}


@router.post("/{draft_id}/approve", response_model=ContentDraftResponse)
async def approve_draft(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Approve a draft for scheduling."""
    result = await db.execute(
        select(ContentDraft)
        .options(selectinload(ContentDraft.variants))
        .where(ContentDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    draft.status = DraftStatus.APPROVED
    await db.commit()
    await db.refresh(draft)

    return ContentDraftResponse.model_validate(draft)


@router.get("/{draft_id}/variants", response_model=list[ContentVariantResponse])
async def list_variants(
    draft_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """List all variants for a draft."""
    result = await db.execute(select(ContentDraft).where(ContentDraft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    result = await db.execute(
        select(ContentVariant).where(ContentVariant.draft_id == draft_id)
    )
    variants = result.scalars().all()

    return [ContentVariantResponse.model_validate(v) for v in variants]


@router.post("/{draft_id}/variants/{variant_id}/select", response_model=ContentDraftResponse)
async def select_variant(
    draft_id: UUID,
    variant_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Select a variant to use for the draft."""
    result = await db.execute(
        select(ContentDraft)
        .options(selectinload(ContentDraft.variants))
        .where(ContentDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    # Find the variant
    variant = None
    for v in draft.variants:
        if v.id == variant_id:
            variant = v
            v.is_selected = True
        else:
            v.is_selected = False

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found",
        )

    # Update draft with variant content
    draft.caption = variant.caption
    draft.hashtags = variant.hashtags

    await db.commit()
    await db.refresh(draft)

    return ContentDraftResponse.model_validate(draft)


@router.patch("/{draft_id}/schedule", response_model=DraftScheduleResponse)
async def schedule_draft(
    draft_id: UUID,
    data: DraftScheduleRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Schedule or reschedule a draft for publishing.

    This creates a new ScheduledPost entry linked to the draft.
    If the draft is already scheduled, the existing ScheduledPost is updated.
    """
    # Get the draft
    result = await db.execute(
        select(ContentDraft).where(ContentDraft.id == draft_id)
    )
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found",
        )

    await get_brand(draft.brand_id, current_user, db)

    # Validate connector
    connector_result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == data.connector_id)
    )
    connector = connector_result.scalar_one_or_none()

    if not connector or connector.brand_id != draft.brand_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    if connector.status != ConnectorStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connector is not connected",
        )

    # Validate scheduled time is in the future
    if data.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future",
        )

    # Check if draft already has a scheduled post
    existing_post_result = await db.execute(
        select(ScheduledPost).where(
            ScheduledPost.draft_id == draft_id,
            ScheduledPost.status.in_([PostStatus.SCHEDULED, PostStatus.QUEUED]),
        )
    )
    existing_post = existing_post_result.scalar_one_or_none()

    if existing_post:
        # Update existing scheduled post
        existing_post.scheduled_at = data.scheduled_at
        existing_post.timezone = data.timezone
        existing_post.connector_id = data.connector_id
        scheduled_post = existing_post
        message = "Draft rescheduled successfully"
    else:
        # Create content snapshot
        content_snapshot = {
            "caption": draft.caption,
            "hashtags": draft.hashtags,
            "media_urls": draft.media_urls,
            "media_type": draft.media_type,
            "platform_data": draft.platform_data,
        }

        # Create new scheduled post
        scheduled_post = ScheduledPost(
            brand_id=draft.brand_id,
            draft_id=draft_id,
            connector_id=data.connector_id,
            scheduled_at=data.scheduled_at,
            timezone=data.timezone,
            content_snapshot=content_snapshot,
            status=PostStatus.SCHEDULED,
        )
        db.add(scheduled_post)

        # Update draft status
        draft.status = DraftStatus.SCHEDULED
        message = "Draft scheduled successfully"

    await db.commit()
    await db.refresh(scheduled_post)

    return DraftScheduleResponse(
        draft_id=draft_id,
        scheduled_post_id=scheduled_post.id,
        scheduled_at=scheduled_post.scheduled_at,
        status=scheduled_post.status,
        message=message,
    )
