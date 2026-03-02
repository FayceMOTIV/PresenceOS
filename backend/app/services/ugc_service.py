"""
PresenceOS - UGC (User Generated Content) Service
"""
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brain import UGCPost

logger = structlog.get_logger()


async def add_ugc_manual(
    brand_id: uuid.UUID,
    db: AsyncSession,
    source_platform: str,
    author_username: str,
    media_url: str | None = None,
    caption: str | None = None,
    source_url: str | None = None,
) -> UGCPost:
    """Add UGC manually."""
    post = UGCPost(
        brand_id=brand_id,
        source_platform=source_platform,
        author_username=author_username,
        media_url=media_url,
        caption=caption,
        source_url=source_url,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    logger.info("UGC added", brand_id=str(brand_id), author=author_username)
    return post


async def generate_permission_request_dm(author_username: str, brand_name: str) -> str:
    """Generate a DM text requesting repost permission."""
    return (
        f"Bonjour @{author_username} ! 👋\n\n"
        f"Merci d'avoir partagé votre expérience chez {brand_name} ! "
        f"Nous adorons votre photo/vidéo et aimerions la repartager sur notre compte.\n\n"
        f"Est-ce que vous nous donnez votre accord ? 🙏\n\n"
        f"Merci beaucoup !\n"
        f"L'équipe {brand_name}"
    )


async def list_ugc(
    brand_id: uuid.UUID,
    db: AsyncSession,
    status: str | None = None,
    limit: int = 20,
) -> list[UGCPost]:
    """List UGC posts for a brand."""
    stmt = select(UGCPost).where(UGCPost.brand_id == brand_id)
    if status:
        stmt = stmt.where(UGCPost.permission_status == status)
    stmt = stmt.order_by(UGCPost.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
