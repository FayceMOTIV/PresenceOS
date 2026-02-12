"""
PresenceOS - Knowledge Base Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.brand import KnowledgeItem, KnowledgeType
from app.schemas.brand import (
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItemResponse,
    KnowledgeImport,
    KnowledgeImportResult,
)
from app.services.embeddings import EmbeddingService

router = APIRouter()


@router.get("/brands/{brand_id}", response_model=list[KnowledgeItemResponse])
async def list_knowledge_items(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    knowledge_type: KnowledgeType | None = None,
    category: str | None = None,
    is_active: bool = True,
    is_featured: bool | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    """List knowledge items for a brand with filtering."""
    await get_brand(brand_id, current_user, db)

    query = select(KnowledgeItem).where(
        KnowledgeItem.brand_id == brand_id,
        KnowledgeItem.is_active == is_active,
    )

    if knowledge_type:
        query = query.where(KnowledgeItem.knowledge_type == knowledge_type)
    if category:
        query = query.where(KnowledgeItem.category == category)
    if is_featured is not None:
        query = query.where(KnowledgeItem.is_featured == is_featured)

    query = query.order_by(KnowledgeItem.title).limit(limit).offset(offset)

    result = await db.execute(query)
    items = result.scalars().all()

    return [KnowledgeItemResponse.model_validate(item) for item in items]


@router.post("/brands/{brand_id}", response_model=KnowledgeItemResponse)
async def create_knowledge_item(
    brand_id: UUID,
    data: KnowledgeItemCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a new knowledge item."""
    await get_brand(brand_id, current_user, db)

    item = KnowledgeItem(brand_id=brand_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Generate embedding asynchronously (fire and forget for now)
    # In production, this would be a background task
    try:
        embedding_service = EmbeddingService()
        embedding = await embedding_service.generate_embedding(
            f"{item.title}\n{item.content}"
        )
        item.embedding = embedding
        await db.commit()
    except Exception:
        pass  # Log error but don't fail the request

    return KnowledgeItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get a specific knowledge item."""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        )

    # Verify access
    await get_brand(item.brand_id, current_user, db)

    return KnowledgeItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge_item(
    item_id: UUID,
    data: KnowledgeItemUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update a knowledge item."""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        )

    await get_brand(item.brand_id, current_user, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    # Re-generate embedding if content changed
    if "content" in update_data or "title" in update_data:
        try:
            embedding_service = EmbeddingService()
            embedding = await embedding_service.generate_embedding(
                f"{item.title}\n{item.content}"
            )
            item.embedding = embedding
            await db.commit()
        except Exception:
            pass

    return KnowledgeItemResponse.model_validate(item)


@router.delete("/{item_id}")
async def delete_knowledge_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete a knowledge item (soft delete)."""
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        )

    await get_brand(item.brand_id, current_user, db)

    item.is_active = False
    await db.commit()

    return {"message": "Knowledge item deleted"}


@router.post("/brands/{brand_id}/import", response_model=KnowledgeImportResult)
async def import_knowledge_items(
    brand_id: UUID,
    data: KnowledgeImport,
    current_user: CurrentUser,
    db: DBSession,
):
    """Bulk import knowledge items from CSV/JSON."""
    await get_brand(brand_id, current_user, db)

    created = 0
    updated = 0
    errors = []

    for idx, item_data in enumerate(data.items):
        try:
            # Check if item with same title exists
            existing = None
            if data.overwrite_existing:
                result = await db.execute(
                    select(KnowledgeItem).where(
                        KnowledgeItem.brand_id == brand_id,
                        KnowledgeItem.title == item_data.title,
                        KnowledgeItem.knowledge_type == item_data.knowledge_type,
                    )
                )
                existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.content = item_data.content
                existing.category = item_data.category
                existing.metadata = item_data.metadata
                existing.image_urls = item_data.image_urls
                updated += 1
            else:
                # Create new
                item = KnowledgeItem(
                    brand_id=brand_id,
                    knowledge_type=item_data.knowledge_type,
                    title=item_data.title,
                    content=item_data.content,
                    category=item_data.category,
                    metadata=item_data.metadata,
                    image_urls=item_data.image_urls,
                )
                db.add(item)
                created += 1

        except Exception as e:
            errors.append({"index": idx, "title": item_data.title, "error": str(e)})

    await db.commit()

    return KnowledgeImportResult(
        total=len(data.items),
        created=created,
        updated=updated,
        errors=errors,
    )


@router.get("/brands/{brand_id}/categories")
async def get_knowledge_categories(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get all unique categories for a brand."""
    await get_brand(brand_id, current_user, db)

    result = await db.execute(
        select(KnowledgeItem.category)
        .where(
            KnowledgeItem.brand_id == brand_id,
            KnowledgeItem.category.isnot(None),
            KnowledgeItem.is_active == True,
        )
        .distinct()
    )
    categories = [row[0] for row in result.all() if row[0]]

    return {"categories": sorted(categories)}
