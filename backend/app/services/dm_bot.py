"""
PresenceOS - DM Bot Service
Handles automated DM sending for UGC permission requests.
Uses Upload-Post API for sending messages when available.
"""
import structlog
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brain import UGCPost

logger = structlog.get_logger()


async def send_ugc_permission_dm(
    ugc_post_id: str,
    brand_name: str,
    db: AsyncSession,
) -> dict:
    """Send a DM to request permission to repost UGC content."""
    import uuid

    result = await db.execute(
        select(UGCPost).where(UGCPost.id == uuid.UUID(ugc_post_id))
    )
    post = result.scalar_one_or_none()
    if not post:
        return {"status": "not_found"}

    if not post.author_username:
        return {"status": "no_username"}

    # Generate the DM text
    dm_text = (
        f"Bonjour {post.author_username}, nous adorons votre contenu ! "
        f"Nous aimerions le partager sur le compte de {brand_name}. "
        f"Avez-vous la permission ? Répondez oui ou non."
    )

    # Mark as requested
    await db.execute(
        update(UGCPost)
        .where(UGCPost.id == post.id)
        .values(
            permission_status="requested",
            permission_requested_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    logger.info(
        "UGC permission DM prepared",
        ugc_id=ugc_post_id,
        author=post.author_username,
    )

    # Note: Actual DM sending would go through platform API (Instagram DM API, etc.)
    # For now, we return the DM text for manual sending or future automation
    return {
        "status": "requested",
        "dm_text": dm_text,
        "author_username": post.author_username,
        "platform": post.source_platform,
    }


async def batch_send_ugc_permissions(
    brand_id: str,
    brand_name: str,
    db: AsyncSession,
    limit: int = 5,
) -> list[dict]:
    """Send permission requests for all pending UGC posts."""
    import uuid

    result = await db.execute(
        select(UGCPost)
        .where(
            UGCPost.brand_id == uuid.UUID(brand_id),
            UGCPost.permission_status == "pending",
            UGCPost.author_username.isnot(None),
        )
        .limit(limit)
    )
    posts = result.scalars().all()

    results = []
    for post in posts:
        r = await send_ugc_permission_dm(str(post.id), brand_name, db)
        results.append(r)

    return results
