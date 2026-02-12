"""
PresenceOS - Content Ideas Endpoints
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.content import ContentIdea, IdeaStatus
from app.schemas.content import (
    ContentIdeaCreate,
    ContentIdeaUpdate,
    ContentIdeaResponse,
    ContentIdeaListResponse,
)

router = APIRouter()


@router.get("/brands/{brand_id}", response_model=list[ContentIdeaListResponse])
async def list_ideas(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    status_filter: IdeaStatus | None = None,
    content_pillar: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    """List content ideas for a brand."""
    await get_brand(brand_id, current_user, db)

    query = select(ContentIdea).where(ContentIdea.brand_id == brand_id)

    if status_filter:
        query = query.where(ContentIdea.status == status_filter)
    if content_pillar:
        query = query.where(ContentIdea.content_pillar == content_pillar)
    if date_from:
        query = query.where(ContentIdea.suggested_date >= date_from)
    if date_to:
        query = query.where(ContentIdea.suggested_date <= date_to)

    query = query.order_by(ContentIdea.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    ideas = result.scalars().all()

    return [ContentIdeaListResponse.model_validate(idea) for idea in ideas]


@router.post("/brands/{brand_id}", response_model=ContentIdeaResponse)
async def create_idea(
    brand_id: UUID,
    data: ContentIdeaCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a new content idea manually."""
    await get_brand(brand_id, current_user, db)

    idea = ContentIdea(brand_id=brand_id, **data.model_dump())
    db.add(idea)
    await db.commit()
    await db.refresh(idea)

    return ContentIdeaResponse.model_validate(idea)


@router.get("/{idea_id}", response_model=ContentIdeaResponse)
async def get_idea(
    idea_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get a specific content idea."""
    result = await db.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    await get_brand(idea.brand_id, current_user, db)

    return ContentIdeaResponse.model_validate(idea)


@router.patch("/{idea_id}", response_model=ContentIdeaResponse)
async def update_idea(
    idea_id: UUID,
    data: ContentIdeaUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update a content idea."""
    result = await db.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    await get_brand(idea.brand_id, current_user, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(idea, field, value)

    await db.commit()
    await db.refresh(idea)

    return ContentIdeaResponse.model_validate(idea)


@router.delete("/{idea_id}")
async def delete_idea(
    idea_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete a content idea."""
    result = await db.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    await get_brand(idea.brand_id, current_user, db)

    idea.status = IdeaStatus.ARCHIVED
    await db.commit()

    return {"message": "Idea archived"}


@router.post("/{idea_id}/approve", response_model=ContentIdeaResponse)
async def approve_idea(
    idea_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Approve a content idea for production."""
    result = await db.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    await get_brand(idea.brand_id, current_user, db)

    idea.status = IdeaStatus.APPROVED
    await db.commit()
    await db.refresh(idea)

    return ContentIdeaResponse.model_validate(idea)


@router.post("/{idea_id}/reject", response_model=ContentIdeaResponse)
async def reject_idea(
    idea_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Reject a content idea."""
    result = await db.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
    idea = result.scalar_one_or_none()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    await get_brand(idea.brand_id, current_user, db)

    idea.status = IdeaStatus.REJECTED
    await db.commit()
    await db.refresh(idea)

    return ContentIdeaResponse.model_validate(idea)


@router.get("/brands/{brand_id}/daily", response_model=list[ContentIdeaListResponse])
async def get_daily_ideas(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    count: int = Query(3, le=10),
):
    """Get today's AI-generated content ideas (morning digest)."""
    await get_brand(brand_id, current_user, db)

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(ContentIdea)
        .where(
            ContentIdea.brand_id == brand_id,
            ContentIdea.status == IdeaStatus.NEW,
            ContentIdea.created_at >= today,
        )
        .order_by(ContentIdea.created_at.desc())
        .limit(count)
    )
    ideas = result.scalars().all()

    return [ContentIdeaListResponse.model_validate(idea) for idea in ideas]
