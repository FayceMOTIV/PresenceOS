"""
PresenceOS - Publisher Service (Sprint 10)

Orchestrates the full publishing pipeline:
  1. Resolve connector for target platform
  2. Prepare content (caption, hashtags, media)
  3. Publish via the appropriate connector
  4. Record result in scheduled_posts
  5. Send confirmation (WhatsApp or in-app)

Works with all connectors: Upload-Post (Instagram/Facebook/TikTok), LinkedIn, Meta native.
"""
import structlog
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.factory import get_connector_handler
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    PostStatus,
    PublishJob,
)
from app.services.whatsapp import WhatsAppService

logger = structlog.get_logger()


class PublisherService:
    """
    Publish content across social platforms.

    Handles the full lifecycle: connector resolution, content preparation,
    platform-specific publishing, status tracking, and notifications.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.whatsapp = WhatsAppService()

    async def publish_post(self, post_id: UUID) -> dict:
        """
        Publish a scheduled post.

        Args:
            post_id: ScheduledPost UUID

        Returns:
            {"success": bool, "post_url": str | None, "error": str | None}
        """
        # Load the post with connector
        result = await self.db.execute(
            select(ScheduledPost).where(ScheduledPost.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            return {"success": False, "post_url": None, "error": "Post not found"}

        if post.status == PostStatus.PUBLISHED:
            return {
                "success": True,
                "post_url": post.platform_post_url,
                "error": None,
            }

        # Load the connector
        connector_result = await self.db.execute(
            select(SocialConnector).where(SocialConnector.id == post.connector_id)
        )
        connector_row = connector_result.scalar_one_or_none()

        if not connector_row:
            await self._mark_failed(post, "Connector not found")
            return {"success": False, "post_url": None, "error": "Connector not found"}

        try:
            # Update status to publishing
            post.status = PostStatus.PUBLISHING
            await self.db.commit()

            # Get platform connector
            connector = get_connector_handler(connector_row.platform)

            # Build content dict
            content = {
                "caption": post.content_snapshot.get("caption", ""),
                "hashtags": post.content_snapshot.get("hashtags", []),
                "account_username": connector_row.account_username,
                "account_id": connector_row.account_id,
                "platform": connector_row.platform.value,
            }

            media_urls = post.content_snapshot.get("media_urls", [])

            # Publish
            publish_result = await connector.publish(
                access_token=connector_row.access_token_encrypted,
                content=content,
                media_urls=media_urls if media_urls else None,
            )

            # Update post with result
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.now(timezone.utc)
            post.platform_post_id = publish_result.get("post_id")
            post.platform_post_url = publish_result.get("post_url")
            post.last_error = None

            await self.db.commit()

            logger.info(
                "Post published",
                post_id=str(post_id),
                platform=connector_row.platform.value,
                post_url=post.platform_post_url,
            )

            return {
                "success": True,
                "post_url": post.platform_post_url,
                "error": None,
            }

        except Exception as e:
            error_msg = str(e)[:500]
            await self._mark_failed(post, error_msg)

            logger.error(
                "Publish failed",
                post_id=str(post_id),
                error=error_msg,
            )

            return {"success": False, "post_url": None, "error": error_msg}

    async def publish_batch(self, post_ids: list[UUID]) -> list[dict]:
        """Publish multiple posts, returning results for each."""
        results = []
        for post_id in post_ids:
            result = await self.publish_post(post_id)
            results.append({"post_id": str(post_id), **result})
        return results

    async def notify_result(
        self,
        post_id: UUID,
        phone: str | None = None,
        success: bool = True,
        post_url: str | None = None,
        error: str | None = None,
    ) -> None:
        """
        Send a notification about publish result.

        If phone is provided, sends via WhatsApp.
        """
        if not phone or not self.whatsapp.is_configured:
            return

        if success:
            message = f"Votre post a ete publie avec succes!"
            if post_url:
                message += f"\n\nVoir le post: {post_url}"
        else:
            message = f"La publication a echoue."
            if error:
                message += f"\n\nErreur: {error}"

        try:
            await self.whatsapp.send_text_message(phone, message)
        except Exception as e:
            logger.warning(
                "Failed to send publish notification",
                phone=phone,
                error=str(e),
            )

    async def _mark_failed(self, post: ScheduledPost, error: str) -> None:
        """Mark a post as failed with error message."""
        post.status = PostStatus.FAILED
        post.last_error = error
        post.retry_count = (post.retry_count or 0) + 1
        await self.db.commit()

    async def retry_failed(self, post_id: UUID, max_retries: int = 3) -> dict:
        """Retry a failed post if under max retries."""
        result = await self.db.execute(
            select(ScheduledPost).where(ScheduledPost.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            return {"success": False, "error": "Post not found"}

        if post.status != PostStatus.FAILED:
            return {"success": False, "error": "Post is not in failed state"}

        if (post.retry_count or 0) >= max_retries:
            return {
                "success": False,
                "error": f"Max retries ({max_retries}) exceeded",
            }

        # Reset to scheduled and re-publish
        post.status = PostStatus.SCHEDULED
        await self.db.commit()

        return await self.publish_post(post_id)
