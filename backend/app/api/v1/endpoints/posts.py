"""
PresenceOS - Scheduled Posts Endpoints
"""
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.content import ContentDraft, DraftStatus
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    PostStatus,
    ConnectorStatus,
    PublishJob,
)
from app.schemas.publishing import (
    SchedulePostRequest,
    SchedulePostUpdate,
    ScheduledPostResponse,
    ScheduledPostListResponse,
    PublishJobResponse,
    CalendarResponse,
    CalendarDay,
    BulkScheduleRequest,
    BulkScheduleResponse,
    BulkScheduleResult,
    QuickCreateRequest,
    QuickCreateResponse,
)

router = APIRouter()


@router.get("/brands/{brand_id}", response_model=list[ScheduledPostListResponse])
async def list_posts(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    status_filter: PostStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    """List scheduled posts for a brand."""
    await get_brand(brand_id, current_user, db)

    query = select(ScheduledPost).where(ScheduledPost.brand_id == brand_id)

    if status_filter:
        query = query.where(ScheduledPost.status == status_filter)
    if date_from:
        query = query.where(ScheduledPost.scheduled_at >= date_from)
    if date_to:
        query = query.where(ScheduledPost.scheduled_at <= date_to)

    query = query.order_by(ScheduledPost.scheduled_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    posts = result.scalars().all()

    return [ScheduledPostListResponse.model_validate(post) for post in posts]


@router.post("/brands/{brand_id}", response_model=ScheduledPostResponse)
async def schedule_post(
    brand_id: UUID,
    data: SchedulePostRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Schedule a post for publishing."""
    await get_brand(brand_id, current_user, db)

    # Validate connector
    result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == data.connector_id)
    )
    connector = result.scalar_one_or_none()

    if not connector or connector.brand_id != brand_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    if connector.status != ConnectorStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connector is not connected",
        )

    # Get content snapshot
    content_snapshot = None

    if data.draft_id:
        draft_result = await db.execute(
            select(ContentDraft).where(ContentDraft.id == data.draft_id)
        )
        draft = draft_result.scalar_one_or_none()

        if not draft or draft.brand_id != brand_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found",
            )

        content_snapshot = {
            "caption": draft.caption,
            "hashtags": draft.hashtags,
            "media_urls": draft.media_urls,
            "media_type": draft.media_type,
            "platform_data": draft.platform_data,
        }

        # Update draft status
        draft.status = DraftStatus.SCHEDULED

    elif data.content:
        content_snapshot = data.content.model_dump()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either draft_id or content must be provided",
        )

    # Validate scheduled time is in the future
    if data.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future",
        )

    # Create scheduled post
    post = ScheduledPost(
        brand_id=brand_id,
        draft_id=data.draft_id,
        connector_id=data.connector_id,
        scheduled_at=data.scheduled_at,
        timezone=data.timezone,
        content_snapshot=content_snapshot,
        status=PostStatus.SCHEDULED,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return ScheduledPostResponse.model_validate(post)


@router.patch("/bulk-schedule", response_model=BulkScheduleResponse)
async def bulk_reschedule_posts(
    data: BulkScheduleRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Reschedule multiple posts at once (for drag & drop operations).

    All posts must belong to workspaces the user has access to.
    Each post is processed independently - failures don't affect other posts.
    """
    results: list[BulkScheduleResult] = []
    successful = 0
    failed = 0

    for item in data.items:
        try:
            # Get the post
            result = await db.execute(
                select(ScheduledPost).where(ScheduledPost.id == item.scheduled_post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                results.append(BulkScheduleResult(
                    scheduled_post_id=item.scheduled_post_id,
                    success=False,
                    error="Post not found",
                ))
                failed += 1
                continue

            # Verify permissions
            try:
                await get_brand(post.brand_id, current_user, db)
            except HTTPException:
                results.append(BulkScheduleResult(
                    scheduled_post_id=item.scheduled_post_id,
                    success=False,
                    error="Access denied",
                ))
                failed += 1
                continue

            # Check if post can be rescheduled
            if post.status not in [PostStatus.SCHEDULED, PostStatus.QUEUED]:
                results.append(BulkScheduleResult(
                    scheduled_post_id=item.scheduled_post_id,
                    success=False,
                    error=f"Cannot reschedule a {post.status.value} post",
                ))
                failed += 1
                continue

            # Validate new time is in the future
            if item.new_scheduled_at <= datetime.now(timezone.utc):
                results.append(BulkScheduleResult(
                    scheduled_post_id=item.scheduled_post_id,
                    success=False,
                    error="Scheduled time must be in the future",
                ))
                failed += 1
                continue

            # Update the post
            post.scheduled_at = item.new_scheduled_at
            results.append(BulkScheduleResult(
                scheduled_post_id=item.scheduled_post_id,
                success=True,
                new_scheduled_at=item.new_scheduled_at,
            ))
            successful += 1

        except Exception as e:
            results.append(BulkScheduleResult(
                scheduled_post_id=item.scheduled_post_id,
                success=False,
                error=str(e),
            ))
            failed += 1

    await db.commit()

    return BulkScheduleResponse(
        total=len(data.items),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.get("/{post_id}", response_model=ScheduledPostResponse)
async def get_post(
    post_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get scheduled post details."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    await get_brand(post.brand_id, current_user, db)

    return ScheduledPostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=ScheduledPostResponse)
async def update_scheduled_post(
    post_id: UUID,
    data: SchedulePostUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update a scheduled post (reschedule or update content)."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    await get_brand(post.brand_id, current_user, db)

    if post.status != PostStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update a {post.status.value} post",
        )

    if data.scheduled_at:
        if data.scheduled_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future",
            )
        post.scheduled_at = data.scheduled_at

    if data.content:
        post.content_snapshot = data.content.model_dump()

    await db.commit()
    await db.refresh(post)

    return ScheduledPostResponse.model_validate(post)


@router.delete("/{post_id}")
async def cancel_post(
    post_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Cancel a scheduled post."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    await get_brand(post.brand_id, current_user, db)

    if post.status not in [PostStatus.SCHEDULED, PostStatus.QUEUED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a {post.status.value} post",
        )

    post.status = PostStatus.CANCELLED

    # Update draft status if linked
    if post.draft_id:
        draft_result = await db.execute(
            select(ContentDraft).where(ContentDraft.id == post.draft_id)
        )
        draft = draft_result.scalar_one_or_none()
        if draft:
            draft.status = DraftStatus.APPROVED

    await db.commit()

    return {"message": "Post cancelled"}


@router.get("/{post_id}/jobs", response_model=list[PublishJobResponse])
async def get_post_jobs(
    post_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get publish jobs for a scheduled post."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    await get_brand(post.brand_id, current_user, db)

    jobs_result = await db.execute(
        select(PublishJob)
        .where(PublishJob.scheduled_post_id == post_id)
        .order_by(PublishJob.attempt_number)
    )
    jobs = jobs_result.scalars().all()

    return [PublishJobResponse.model_validate(job) for job in jobs]


@router.get("/brands/{brand_id}/calendar", response_model=CalendarResponse)
async def get_calendar(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Get calendar view of scheduled posts.

    Args:
        month: Month in YYYY-MM format (e.g., 2026-03). Takes precedence over start_date/end_date.
        start_date: Start date for custom range
        end_date: End date for custom range
    """
    await get_brand(brand_id, current_user, db)

    # Parse month parameter if provided
    if month:
        year, month_num = map(int, month.split("-"))
        start_date = datetime(year, month_num, 1, tzinfo=timezone.utc)
        # Calculate last day of month
        if month_num == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month_num + 1, 1, tzinfo=timezone.utc) - timedelta(seconds=1)
    elif not start_date:
        start_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    if not end_date:
        end_date = start_date + timedelta(days=30)

    # Get posts in range
    result = await db.execute(
        select(ScheduledPost)
        .where(
            ScheduledPost.brand_id == brand_id,
            ScheduledPost.scheduled_at >= start_date,
            ScheduledPost.scheduled_at <= end_date,
        )
        .order_by(ScheduledPost.scheduled_at)
    )
    posts = result.scalars().all()

    # Group by day
    days_dict: dict[str, list] = {}
    current = start_date
    while current <= end_date:
        days_dict[current.strftime("%Y-%m-%d")] = []
        current += timedelta(days=1)

    for post in posts:
        day_key = post.scheduled_at.strftime("%Y-%m-%d")
        if day_key in days_dict:
            days_dict[day_key].append(
                ScheduledPostListResponse.model_validate(post)
            )

    days = [
        CalendarDay(
            date=datetime.strptime(day_key, "%Y-%m-%d").replace(tzinfo=timezone.utc),
            scheduled_posts=day_posts,
            ideas=[],  # TODO: Add ideas suggested for this date
        )
        for day_key, day_posts in sorted(days_dict.items())
    ]

    return CalendarResponse(
        brand_id=brand_id,
        start_date=start_date,
        end_date=end_date,
        days=days,
    )


@router.post("/brands/{brand_id}/quick", response_model=QuickCreateResponse)
async def quick_create_post(
    brand_id: UUID,
    data: QuickCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Quickly create and schedule a post from the calendar.

    Creates a draft and schedules it in one operation.
    """
    await get_brand(brand_id, current_user, db)

    # Validate connector
    result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == data.connector_id)
    )
    connector = result.scalar_one_or_none()

    if not connector or connector.brand_id != brand_id:
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

    # Create draft
    draft = ContentDraft(
        brand_id=brand_id,
        caption=data.caption,
        media_type=data.media_type,
        platform=data.platform,
        status=DraftStatus.SCHEDULED,
    )
    db.add(draft)
    await db.flush()  # Get draft ID

    # Create content snapshot
    content_snapshot = {
        "caption": data.caption,
        "hashtags": [],
        "media_urls": [],
        "media_type": data.media_type,
        "platform_data": {},
    }

    # Create scheduled post
    post = ScheduledPost(
        brand_id=brand_id,
        draft_id=draft.id,
        connector_id=data.connector_id,
        scheduled_at=data.scheduled_at,
        timezone=data.timezone,
        content_snapshot=content_snapshot,
        status=PostStatus.SCHEDULED,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return QuickCreateResponse(
        id=post.id,
        title=data.title,
        caption=data.caption,
        platform=data.platform,
        media_type=data.media_type,
        scheduled_at=post.scheduled_at,
        status=post.status,
        connector_id=post.connector_id,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )
