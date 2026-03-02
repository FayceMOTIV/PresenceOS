# PresenceOS — Inbox Manager (Sprint 5: Engager)
# Orchestrates: fetch → classify → generate replies → store in Firestore

from __future__ import annotations

import logging
from datetime import datetime

from app.models.comment import Comment, ReplyStatus
from app.services.engager.comment_fetcher import BaseCommentFetcher, MockCommentFetcher
from app.services.engager.comment_classifier import CommentClassifier
from app.services.engager.reply_generator import ReplyGenerator
from app.services.firebase_firestore import FirestoreService

logger = logging.getLogger(__name__)


class InboxManager:
    """Orchestrates the full engagement pipeline: fetch → classify → reply → store."""

    def __init__(
        self,
        fetcher: BaseCommentFetcher | None = None,
        classifier: CommentClassifier | None = None,
        reply_generator: ReplyGenerator | None = None,
        firestore: FirestoreService | None = None,
    ) -> None:
        self.fetcher = fetcher or MockCommentFetcher()
        self.classifier = classifier or CommentClassifier()
        self.reply_generator = reply_generator or ReplyGenerator()
        self.firestore = firestore or FirestoreService()

    async def scan_and_process(
        self,
        brand_id: str,
        access_token: str = "",
        since_hours: int = 24,
    ) -> dict:
        """Full pipeline: fetch → classify → generate replies → store."""
        # 1. Fetch
        comments = await self.fetcher.fetch_comments(
            brand_id, access_token, since_hours
        )
        logger.info(
            "Comments fetched",
            extra={"brand_id": brand_id, "count": len(comments)},
        )

        if not comments:
            return {"fetched": 0, "classified": 0, "replies_generated": 0}

        # 2. Classify
        classified = await self.classifier.classify_batch(comments)

        # 3. Generate replies (skip spam/skipped)
        needs_reply = [
            c for c in classified if c.reply_status != ReplyStatus.SKIPPED.value
        ]
        with_replies = await self.reply_generator.generate_replies_batch(needs_reply)

        # Merge back skipped comments
        all_comments = with_replies + [
            c for c in classified if c.reply_status == ReplyStatus.SKIPPED.value
        ]

        # 4. Store in Firestore
        stored = 0
        for comment in all_comments:
            success = await self.firestore.set_subcollection_doc(
                "businesses",
                brand_id,
                "inbox",
                comment.id,
                comment.to_dict(),
                merge=True,
            )
            if success:
                stored += 1

        result = {
            "fetched": len(comments),
            "classified": len(classified),
            "replies_generated": len(with_replies),
            "stored": stored,
        }
        logger.info("Scan complete", extra={"brand_id": brand_id, **result})
        return result

    async def get_inbox(
        self,
        brand_id: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Comment]:
        """Get inbox items from Firestore."""
        # Firestore doesn't have a list-subcollection method yet.
        # For now, we use get_document on the brand to check inbox state.
        # Full Firestore query will be added when needed.
        # Return empty list — the API endpoint serves from mock data in dev.
        return []

    async def approve_reply(self, brand_id: str, comment_id: str, final_reply: str | None = None) -> Comment | None:
        """Approve a suggested reply (optionally with edits)."""
        data = await self.firestore.get_subcollection_doc(
            "businesses", brand_id, "inbox", comment_id
        )
        if not data:
            return None

        comment = Comment.from_dict(data)
        comment.reply_status = ReplyStatus.APPROVED.value
        if final_reply:
            comment.final_reply = final_reply
        else:
            comment.final_reply = comment.suggested_reply

        await self.firestore.set_subcollection_doc(
            "businesses", brand_id, "inbox", comment_id,
            comment.to_dict(), merge=True,
        )
        return comment

    async def reject_reply(self, brand_id: str, comment_id: str) -> Comment | None:
        """Reject a suggested reply."""
        data = await self.firestore.get_subcollection_doc(
            "businesses", brand_id, "inbox", comment_id
        )
        if not data:
            return None

        comment = Comment.from_dict(data)
        comment.reply_status = ReplyStatus.REJECTED.value

        await self.firestore.set_subcollection_doc(
            "businesses", brand_id, "inbox", comment_id,
            comment.to_dict(), merge=True,
        )
        return comment

    async def get_stats(self, brand_id: str) -> dict:
        """Get inbox statistics for a brand."""
        # Placeholder stats — will be computed from Firestore queries later
        return {
            "brand_id": brand_id,
            "total": 0,
            "pending": 0,
            "classified": 0,
            "approved": 0,
            "published": 0,
            "skipped": 0,
            "avg_urgency": 0.0,
            "last_scan": None,
        }
