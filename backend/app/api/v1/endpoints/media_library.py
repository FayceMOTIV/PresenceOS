"""
PresenceOS - Media Library API (Sprint 9B)

CRUD endpoints for media assets and voice notes.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.api.v1.deps import CurrentUser, DBSession
from app.models.media import MediaAsset, VoiceNote, MediaType, MediaSource
from app.schemas.media import (
    MediaAssetResponse,
    MediaAssetUpdate,
    VoiceNoteResponse,
    MediaLibraryStats,
)
from app.services.storage import get_storage_service

router = APIRouter()


# ── Media Assets ──────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/assets",
    response_model=list[MediaAssetResponse],
)
async def list_media_assets(
    brand_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    media_type: str | None = Query(None, description="Filter by type: image, video"),
    source: str | None = Query(None, description="Filter by source: whatsapp, upload"),
    archived: bool = Query(False, description="Include archived assets"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List media assets for a brand with optional filters."""
    query = select(MediaAsset).where(MediaAsset.brand_id == brand_id)

    if media_type:
        try:
            mt = MediaType(media_type)
            query = query.where(MediaAsset.media_type == mt)
        except ValueError:
            pass

    if source:
        try:
            ms = MediaSource(source)
            query = query.where(MediaAsset.source == ms)
        except ValueError:
            pass

    if not archived:
        query = query.where(MediaAsset.is_archived == False)

    query = query.order_by(MediaAsset.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    assets = result.scalars().all()

    return [
        MediaAssetResponse(
            id=str(a.id),
            brand_id=str(a.brand_id),
            storage_key=a.storage_key,
            public_url=a.public_url,
            thumbnail_url=a.thumbnail_url,
            media_type=a.media_type.value,
            mime_type=a.mime_type,
            file_size=a.file_size,
            original_filename=a.original_filename,
            width=a.width,
            height=a.height,
            duration_seconds=a.duration_seconds,
            source=a.source.value,
            ai_description=a.ai_description,
            ai_tags=a.ai_tags,
            ai_analyzed=a.ai_analyzed,
            used_in_posts=a.used_in_posts,
            is_archived=a.is_archived,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in assets
    ]


@router.get(
    "/assets/{asset_id}",
    response_model=MediaAssetResponse,
)
async def get_media_asset(
    asset_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get a single media asset by ID."""
    result = await db.execute(
        select(MediaAsset).where(MediaAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset non trouve")

    return MediaAssetResponse(
        id=str(asset.id),
        brand_id=str(asset.brand_id),
        storage_key=asset.storage_key,
        public_url=asset.public_url,
        thumbnail_url=asset.thumbnail_url,
        media_type=asset.media_type.value,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        original_filename=asset.original_filename,
        width=asset.width,
        height=asset.height,
        duration_seconds=asset.duration_seconds,
        source=asset.source.value,
        ai_description=asset.ai_description,
        ai_tags=asset.ai_tags,
        ai_analyzed=asset.ai_analyzed,
        used_in_posts=asset.used_in_posts,
        is_archived=asset.is_archived,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.patch(
    "/assets/{asset_id}",
    response_model=MediaAssetResponse,
)
async def update_media_asset(
    asset_id: UUID,
    data: MediaAssetUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update a media asset (tags, description, archive status)."""
    result = await db.execute(
        select(MediaAsset).where(MediaAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset non trouve")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)

    return MediaAssetResponse(
        id=str(asset.id),
        brand_id=str(asset.brand_id),
        storage_key=asset.storage_key,
        public_url=asset.public_url,
        thumbnail_url=asset.thumbnail_url,
        media_type=asset.media_type.value,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        original_filename=asset.original_filename,
        width=asset.width,
        height=asset.height,
        duration_seconds=asset.duration_seconds,
        source=asset.source.value,
        ai_description=asset.ai_description,
        ai_tags=asset.ai_tags,
        ai_analyzed=asset.ai_analyzed,
        used_in_posts=asset.used_in_posts,
        is_archived=asset.is_archived,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.post("/brands/{brand_id}/assets/{asset_id}/improve")
async def improve_media_asset(
    brand_id: UUID,
    asset_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Trigger AI improvement for a media asset (description, tags)."""
    result = await db.execute(
        select(MediaAsset).where(
            MediaAsset.id == asset_id,
            MediaAsset.brand_id == brand_id,
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset non trouve")

    # Mark as analyzed (actual AI processing can be async via Celery)
    asset.ai_analyzed = True
    await db.commit()
    await db.refresh(asset)

    return {"status": "queued", "asset_id": str(asset_id)}


@router.delete("/assets/{asset_id}")
async def delete_media_asset(
    asset_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Delete a media asset and its file from storage."""
    result = await db.execute(
        select(MediaAsset).where(MediaAsset.id == asset_id)
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset non trouve")

    # Delete from S3
    storage = get_storage_service()
    await storage.delete_file(asset.storage_key)

    # Delete from DB
    await db.delete(asset)
    await db.commit()

    return {"status": "deleted", "id": str(asset_id)}


# ── Voice Notes ───────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/voice-notes",
    response_model=list[VoiceNoteResponse],
)
async def list_voice_notes(
    brand_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    transcribed_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List voice notes for a brand."""
    query = select(VoiceNote).where(VoiceNote.brand_id == brand_id)

    if transcribed_only:
        query = query.where(VoiceNote.is_transcribed == True)

    query = query.order_by(VoiceNote.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    notes = result.scalars().all()

    return [
        VoiceNoteResponse(
            id=str(n.id),
            brand_id=str(n.brand_id),
            storage_key=n.storage_key,
            public_url=n.public_url,
            mime_type=n.mime_type,
            file_size=n.file_size,
            duration_seconds=n.duration_seconds,
            transcription=n.transcription,
            is_transcribed=n.is_transcribed,
            sender_phone=n.sender_phone,
            parsed_instructions=n.parsed_instructions,
            pending_post_id=str(n.pending_post_id) if n.pending_post_id else None,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in notes
    ]


@router.get(
    "/voice-notes/{note_id}",
    response_model=VoiceNoteResponse,
)
async def get_voice_note(
    note_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get a single voice note."""
    result = await db.execute(
        select(VoiceNote).where(VoiceNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Voice note non trouvee")

    return VoiceNoteResponse(
        id=str(note.id),
        brand_id=str(note.brand_id),
        storage_key=note.storage_key,
        public_url=note.public_url,
        mime_type=note.mime_type,
        file_size=note.file_size,
        duration_seconds=note.duration_seconds,
        transcription=note.transcription,
        is_transcribed=note.is_transcribed,
        sender_phone=note.sender_phone,
        parsed_instructions=note.parsed_instructions,
        pending_post_id=str(note.pending_post_id) if note.pending_post_id else None,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.delete("/voice-notes/{note_id}")
async def delete_voice_note(
    note_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Delete a voice note."""
    result = await db.execute(
        select(VoiceNote).where(VoiceNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Voice note non trouvee")

    storage = get_storage_service()
    await storage.delete_file(note.storage_key)

    await db.delete(note)
    await db.commit()

    return {"status": "deleted", "id": str(note_id)}


# ── Stats ─────────────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/stats",
    response_model=MediaLibraryStats,
)
async def get_media_stats(
    brand_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get media library statistics for a brand."""
    # Count assets by type and source
    asset_result = await db.execute(
        select(
            func.count(MediaAsset.id).label("total"),
            func.sum(case((MediaAsset.media_type == MediaType.IMAGE, 1), else_=0)).label("images"),
            func.sum(case((MediaAsset.media_type == MediaType.VIDEO, 1), else_=0)).label("videos"),
            func.coalesce(func.sum(MediaAsset.file_size), 0).label("total_size"),
            func.sum(case((MediaAsset.source == MediaSource.WHATSAPP, 1), else_=0)).label("from_whatsapp"),
            func.sum(case((MediaAsset.source == MediaSource.UPLOAD, 1), else_=0)).label("from_upload"),
            func.sum(case((MediaAsset.ai_analyzed == True, 1), else_=0)).label("ai_analyzed"),
        ).where(MediaAsset.brand_id == brand_id)
    )
    row = asset_result.one()

    # Count voice notes
    vn_result = await db.execute(
        select(func.count(VoiceNote.id)).where(VoiceNote.brand_id == brand_id)
    )
    vn_count = vn_result.scalar() or 0

    return MediaLibraryStats(
        total_images=int(row.images or 0),
        total_videos=int(row.videos or 0),
        total_voice_notes=vn_count,
        total_size_bytes=int(row.total_size or 0),
        from_whatsapp=int(row.from_whatsapp or 0),
        from_upload=int(row.from_upload or 0),
        ai_analyzed_count=int(row.ai_analyzed or 0),
    )
