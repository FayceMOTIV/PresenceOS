"""
PresenceOS — Engager Module Tests (Sprint 5)

Tests for comment fetcher, classifier, reply generator, inbox manager, and API endpoints.
"""

import json
import sys
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.models.comment import Comment, DirectMessage, CommentPlatform, Sentiment, ReplyStatus


# ── Test Comment Model ──


class TestCommentModel:
    """Tests for Comment dataclass."""

    def test_default_values(self):
        c = Comment()
        assert c.sentiment == "neutral"
        assert c.urgency_score == 0.0
        assert c.reply_status == "pending"
        assert c.is_dm is False
        assert c.topics == []

    def test_to_dict(self):
        c = Comment(id="c1", text="Hello", platform="instagram", brand_id="b1")
        d = c.to_dict()
        assert d["id"] == "c1"
        assert d["text"] == "Hello"
        assert d["platform"] == "instagram"
        assert d["brand_id"] == "b1"

    def test_from_dict(self):
        data = {
            "id": "c2",
            "text": "Bonjour",
            "platform": "facebook",
            "sentiment": "positive",
            "urgency_score": 3.5,
            "unknown_field": "should be ignored",
        }
        c = Comment.from_dict(data)
        assert c.id == "c2"
        assert c.text == "Bonjour"
        assert c.sentiment == "positive"
        assert c.urgency_score == 3.5
        assert not hasattr(c, "unknown_field")

    def test_roundtrip(self):
        c = Comment(
            id="c3",
            text="Test",
            sentiment="negative",
            urgency_score=8.5,
            topics=["service", "attente"],
        )
        d = c.to_dict()
        c2 = Comment.from_dict(d)
        assert c2.id == c.id
        assert c2.sentiment == c.sentiment
        assert c2.urgency_score == c.urgency_score
        assert c2.topics == c.topics

    def test_enums(self):
        assert CommentPlatform.INSTAGRAM.value == "instagram"
        assert Sentiment.URGENT.value == "urgent"
        assert ReplyStatus.PUBLISHED.value == "published"
        assert ReplyStatus.SKIPPED.value == "skipped"


class TestDirectMessageModel:
    """Tests for DirectMessage dataclass."""

    def test_default_is_dm(self):
        dm = DirectMessage()
        assert dm.is_dm is True

    def test_to_dict(self):
        dm = DirectMessage(id="dm1", text="Private msg", platform="instagram")
        d = dm.to_dict()
        assert d["is_dm"] is True
        assert d["text"] == "Private msg"

    def test_from_dict_ignores_unknown(self):
        data = {"id": "dm2", "text": "Yo", "extra": "nope"}
        dm = DirectMessage.from_dict(data)
        assert dm.id == "dm2"


# ── Test Mock Fetcher ──


class TestMockCommentFetcher:
    """Tests for MockCommentFetcher."""

    @pytest.mark.asyncio
    async def test_returns_comments(self):
        from app.services.engager.comment_fetcher import MockCommentFetcher

        fetcher = MockCommentFetcher()
        comments = await fetcher.fetch_comments("brand123")
        assert len(comments) >= 5
        assert len(comments) <= 10
        assert all(isinstance(c, Comment) for c in comments)

    @pytest.mark.asyncio
    async def test_comments_have_brand_id(self):
        from app.services.engager.comment_fetcher import MockCommentFetcher

        fetcher = MockCommentFetcher()
        comments = await fetcher.fetch_comments("my-brand")
        for c in comments:
            assert c.brand_id == "my-brand"
            assert c.id.startswith("mock_")
            assert c.text != ""
            assert c.platform in ("instagram", "facebook")

    @pytest.mark.asyncio
    async def test_comments_have_timestamps(self):
        from app.services.engager.comment_fetcher import MockCommentFetcher

        fetcher = MockCommentFetcher()
        comments = await fetcher.fetch_comments("b1")
        for c in comments:
            assert c.created_at != ""
            assert c.fetched_at != ""


# ── Test Classifier ──


class TestCommentClassifier:
    """Tests for CommentClassifier with mocked Anthropic client."""

    @pytest.mark.asyncio
    async def test_classify_positive(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "sentiment": "positive",
                        "urgency_score": 2.0,
                        "topics": ["compliment"],
                        "needs_reply": True,
                    }
                )
            )
        ]

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(id="c1", text="Super restaurant !", platform="instagram")
            result = await classifier.classify(comment)

        assert result.sentiment == "positive"
        assert result.urgency_score == 2.0
        assert result.topics == ["compliment"]
        assert result.reply_status == "classified"

    @pytest.mark.asyncio
    async def test_classify_spam(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "sentiment": "spam",
                        "urgency_score": 0.0,
                        "topics": ["spam"],
                        "needs_reply": False,
                    }
                )
            )
        ]

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(id="c2", text="Follow me for free!", platform="instagram")
            result = await classifier.classify(comment)

        assert result.sentiment == "spam"
        assert result.reply_status == "skipped"

    @pytest.mark.asyncio
    async def test_classify_urgent(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "sentiment": "urgent",
                        "urgency_score": 9.0,
                        "topics": ["hygiene", "plainte"],
                        "needs_reply": True,
                    }
                )
            )
        ]

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(id="c3", text="Cheveu dans mon assiette!", platform="google")
            result = await classifier.classify(comment)

        assert result.sentiment == "urgent"
        assert result.urgency_score == 9.0
        assert result.reply_status == "classified"

    @pytest.mark.asyncio
    async def test_classify_handles_json_error(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not json at all")]

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(id="c4", text="Test", platform="instagram")
            result = await classifier.classify(comment)

        assert result.sentiment == "neutral"
        assert result.urgency_score == 5.0
        assert result.reply_status == "classified"

    @pytest.mark.asyncio
    async def test_classify_handles_api_error(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.side_effect = RuntimeError("API down")
            comment = Comment(id="c5", text="Test", platform="facebook")
            result = await classifier.classify(comment)

        assert result.sentiment == "neutral"
        assert result.urgency_score == 5.0

    @pytest.mark.asyncio
    async def test_classify_batch(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "sentiment": "positive",
                        "urgency_score": 1.0,
                        "topics": [],
                        "needs_reply": True,
                    }
                )
            )
        ]

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            comments = [
                Comment(id="b1", text="Cool", platform="instagram"),
                Comment(id="b2", text="Nice", platform="facebook"),
            ]
            results = await classifier.classify_batch(comments)

        assert len(results) == 2
        assert all(r.reply_status == "classified" for r in results)

    @pytest.mark.asyncio
    async def test_classify_strips_markdown_code_block(self):
        from app.services.engager.comment_classifier import CommentClassifier

        classifier = CommentClassifier()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text='```json\n{"sentiment": "question", "urgency_score": 4.0, "topics": ["horaires"], "needs_reply": true}\n```'
            )
        ]

        with patch.object(classifier, "_get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(id="c6", text="Ouvert dimanche ?", platform="instagram")
            result = await classifier.classify(comment)

        assert result.sentiment == "question"
        assert result.urgency_score == 4.0


# ── Test Reply Generator ──


class TestReplyGenerator:
    """Tests for ReplyGenerator with mocked Anthropic client."""

    @pytest.mark.asyncio
    async def test_generate_reply(self):
        from app.services.engager.reply_generator import ReplyGenerator

        gen = ReplyGenerator()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Merci beaucoup pour votre avis !")]

        with (
            patch.object(gen, "_get_client") as mock_client,
            patch.object(gen, "_get_dna_context", return_value=""),
        ):
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(
                id="r1",
                text="Super resto !",
                sentiment="positive",
                urgency_score=2.0,
                reply_status="classified",
                brand_id="b1",
            )
            result = await gen.generate_reply(comment)

        assert result.suggested_reply == "Merci beaucoup pour votre avis !"
        assert result.reply_status == "classified"

    @pytest.mark.asyncio
    async def test_skips_skipped_comments(self):
        from app.services.engager.reply_generator import ReplyGenerator

        gen = ReplyGenerator()
        comment = Comment(id="r2", text="spam", reply_status="skipped")
        result = await gen.generate_reply(comment)
        assert result.suggested_reply == ""

    @pytest.mark.asyncio
    async def test_handles_api_failure(self):
        from app.services.engager.reply_generator import ReplyGenerator

        gen = ReplyGenerator()

        with (
            patch.object(gen, "_get_client") as mock_client,
            patch.object(gen, "_get_dna_context", return_value=""),
        ):
            mock_client.return_value.messages.create.side_effect = RuntimeError("fail")
            comment = Comment(
                id="r3",
                text="Question",
                sentiment="question",
                reply_status="classified",
                brand_id="b1",
            )
            result = await gen.generate_reply(comment)

        assert result.suggested_reply == ""

    @pytest.mark.asyncio
    async def test_strips_quotes_from_reply(self):
        from app.services.engager.reply_generator import ReplyGenerator

        gen = ReplyGenerator()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='"Merci beaucoup !"')]

        with (
            patch.object(gen, "_get_client") as mock_client,
            patch.object(gen, "_get_dna_context", return_value=""),
        ):
            mock_client.return_value.messages.create.return_value = mock_response
            comment = Comment(
                id="r4",
                text="Genial",
                sentiment="positive",
                reply_status="classified",
                brand_id="b1",
            )
            result = await gen.generate_reply(comment)

        assert result.suggested_reply == "Merci beaucoup !"

    @pytest.mark.asyncio
    async def test_generate_replies_batch(self):
        from app.services.engager.reply_generator import ReplyGenerator

        gen = ReplyGenerator()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Merci !")]

        with (
            patch.object(gen, "_get_client") as mock_client,
            patch.object(gen, "_get_dna_context", return_value=""),
        ):
            mock_client.return_value.messages.create.return_value = mock_response
            comments = [
                Comment(id="rb1", text="Cool", reply_status="classified", brand_id="b1"),
                Comment(id="rb2", text="Nice", reply_status="classified", brand_id="b1"),
                Comment(id="rb3", text="Spam", reply_status="skipped", brand_id="b1"),
            ]
            results = await gen.generate_replies_batch(comments)

        assert len(results) == 3
        assert results[0].suggested_reply == "Merci !"
        assert results[2].suggested_reply == ""  # skipped


# ── Test Inbox Manager ──


class TestInboxManager:
    """Tests for InboxManager orchestration."""

    @pytest.mark.asyncio
    async def test_scan_and_process_full_pipeline(self):
        from app.services.engager.inbox_manager import InboxManager

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_comments.return_value = [
            Comment(id="im1", text="Super", brand_id="b1"),
            Comment(id="im2", text="Spam spam", brand_id="b1"),
        ]

        mock_classifier = AsyncMock()

        async def classify_batch(comments):
            comments[0].sentiment = "positive"
            comments[0].reply_status = "classified"
            comments[1].sentiment = "spam"
            comments[1].reply_status = "skipped"
            return comments

        mock_classifier.classify_batch = classify_batch

        mock_reply_gen = AsyncMock()

        async def gen_batch(comments):
            for c in comments:
                c.suggested_reply = "Merci !"
            return comments

        mock_reply_gen.generate_replies_batch = gen_batch

        mock_firestore = AsyncMock()
        mock_firestore.set_subcollection_doc.return_value = True

        manager = InboxManager(
            fetcher=mock_fetcher,
            classifier=mock_classifier,
            reply_generator=mock_reply_gen,
            firestore=mock_firestore,
        )

        result = await manager.scan_and_process("b1")

        assert result["fetched"] == 2
        assert result["classified"] == 2
        assert result["replies_generated"] == 1  # only non-skipped
        assert result["stored"] == 2

    @pytest.mark.asyncio
    async def test_scan_empty_comments(self):
        from app.services.engager.inbox_manager import InboxManager

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_comments.return_value = []

        manager = InboxManager(fetcher=mock_fetcher)
        result = await manager.scan_and_process("b1")

        assert result["fetched"] == 0
        assert result["classified"] == 0

    @pytest.mark.asyncio
    async def test_approve_reply(self):
        from app.services.engager.inbox_manager import InboxManager

        comment_data = Comment(
            id="ap1",
            text="Question",
            suggested_reply="Oui !",
            reply_status="classified",
        ).to_dict()

        mock_firestore = AsyncMock()
        mock_firestore.get_subcollection_doc.return_value = comment_data
        mock_firestore.set_subcollection_doc.return_value = True

        manager = InboxManager(firestore=mock_firestore)
        result = await manager.approve_reply("b1", "ap1")

        assert result is not None
        assert result.reply_status == "approved"
        assert result.final_reply == "Oui !"

    @pytest.mark.asyncio
    async def test_approve_with_edited_reply(self):
        from app.services.engager.inbox_manager import InboxManager

        comment_data = Comment(
            id="ap2",
            text="Q",
            suggested_reply="Auto reply",
            reply_status="classified",
        ).to_dict()

        mock_firestore = AsyncMock()
        mock_firestore.get_subcollection_doc.return_value = comment_data
        mock_firestore.set_subcollection_doc.return_value = True

        manager = InboxManager(firestore=mock_firestore)
        result = await manager.approve_reply("b1", "ap2", final_reply="Edited reply")

        assert result.final_reply == "Edited reply"

    @pytest.mark.asyncio
    async def test_approve_not_found(self):
        from app.services.engager.inbox_manager import InboxManager

        mock_firestore = AsyncMock()
        mock_firestore.get_subcollection_doc.return_value = None

        manager = InboxManager(firestore=mock_firestore)
        result = await manager.approve_reply("b1", "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_reject_reply(self):
        from app.services.engager.inbox_manager import InboxManager

        comment_data = Comment(id="rj1", text="Bad", reply_status="classified").to_dict()

        mock_firestore = AsyncMock()
        mock_firestore.get_subcollection_doc.return_value = comment_data
        mock_firestore.set_subcollection_doc.return_value = True

        manager = InboxManager(firestore=mock_firestore)
        result = await manager.reject_reply("b1", "rj1")

        assert result.reply_status == "rejected"

    @pytest.mark.asyncio
    async def test_get_stats_placeholder(self):
        from app.services.engager.inbox_manager import InboxManager

        manager = InboxManager()
        stats = await manager.get_stats("b1")
        assert stats["brand_id"] == "b1"
        assert "total" in stats
        assert "pending" in stats


# ── Test API Endpoints ──


class TestEngageAPI:
    """Tests for engage v2 API endpoints."""

    def test_engage_routes_registered(self):
        """Verify the engage router is included in v2."""
        from app.api.v2.router import api_v2_router

        routes = [r.path for r in api_v2_router.routes]
        # Check at least one engage path exists
        assert any("/engage" in r for r in routes), f"No engage routes found in: {routes}"

    def test_scan_route_exists(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("scan" in p for p in paths)

    def test_inbox_route_exists(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("inbox" in p for p in paths)

    def test_stats_route_exists(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("stats" in p for p in paths)
