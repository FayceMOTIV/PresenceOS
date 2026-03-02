"""
PresenceOS — A/B Testing Tests (Sprint 8)
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.ab_testing import ABTestingService, ABTest


class TestABTestModel:
    """Tests for ABTest dataclass."""

    def test_engagement_with_reach(self):
        test = ABTest(likes_a=100, comments_a=20, reach_a=1000)
        assert test.engagement_a == pytest.approx(0.12)

    def test_engagement_no_reach(self):
        test = ABTest(likes_a=50, comments_a=10, reach_a=0)
        assert test.engagement_a == 60.0

    def test_engagement_b(self):
        test = ABTest(likes_b=80, comments_b=20, reach_b=500)
        assert test.engagement_b == pytest.approx(0.2)

    def test_to_dict(self):
        test = ABTest(id="t1", business_id="b1", platform="instagram", caption_a="A", caption_b="B")
        d = test.to_dict()
        assert d["id"] == "t1"
        assert d["caption_a"] == "A"
        assert d["caption_b"] == "B"

    def test_default_status(self):
        test = ABTest()
        assert test.status == "pending"
        assert test.winner is None


class TestABTestingService:
    """Tests for ABTestingService."""

    @pytest.fixture
    def service(self):
        with patch("app.services.ab_testing.anthropic"):
            return ABTestingService()

    @pytest.mark.asyncio
    async def test_generate_variants_returns_two_captions(self, service):
        mock_resp = MagicMock()
        mock_resp.content = [
            MagicMock(
                text='{"caption_a":"Version courte #food","caption_b":"Version longue avec question... #food","strategy":"Court vs long","hypothesis":"La version courte performe mieux"}'
            )
        ]
        service._claude = MagicMock()
        service._claude.messages.create.return_value = mock_resp

        result = await service.generate_variants("Caption originale")
        assert "caption_a" in result
        assert "caption_b" in result
        assert result["caption_a"] != result["caption_b"]
        assert "strategy" in result

    @pytest.mark.asyncio
    async def test_generate_variants_fallback_on_error(self, service):
        service._claude = MagicMock()
        service._claude.messages.create.side_effect = Exception("API error")

        result = await service.generate_variants("Ma caption")
        assert "caption_a" in result
        assert "caption_b" in result
        assert len(result["caption_a"]) > 0

    @pytest.mark.asyncio
    async def test_create_ab_test_returns_test_object(self, service):
        mock_resp = MagicMock()
        mock_resp.content = [
            MagicMock(
                text='{"caption_a":"Variante A","caption_b":"Variante B","strategy":"test","hypothesis":"A gagne"}'
            )
        ]
        service._claude = MagicMock()
        service._claude.messages.create.return_value = mock_resp

        test = await service.create_ab_test("biz-123", "instagram", "Caption originale")
        assert test.business_id == "biz-123"
        assert test.caption_a == "Variante A"
        assert test.caption_b == "Variante B"
        assert test.status == "pending"
        assert test.id != ""

    @pytest.mark.asyncio
    async def test_analyze_results_picks_winner_b(self, service):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="Les questions generent plus d'engagement.")]
        service._claude = MagicMock()
        service._claude.messages.create.return_value = mock_resp

        test = ABTest(
            id="test_1",
            business_id="biz-1",
            likes_a=100,
            reach_a=1000,
            likes_b=200,
            reach_b=1000,
        )

        result = await service.analyze_results(test)
        assert result.winner == "B"
        assert result.status == "complete"
        assert len(result.winner_insight) > 0
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_analyze_results_picks_winner_a(self, service):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="La version courte performe mieux.")]
        service._claude = MagicMock()
        service._claude.messages.create.return_value = mock_resp

        test = ABTest(
            id="test_2",
            business_id="biz-1",
            likes_a=300,
            reach_a=1000,
            likes_b=100,
            reach_b=1000,
        )

        result = await service.analyze_results(test)
        assert result.winner == "A"

    @pytest.mark.asyncio
    async def test_analyze_handles_api_failure(self, service):
        service._claude = MagicMock()
        service._claude.messages.create.side_effect = Exception("API down")

        test = ABTest(id="test_3", likes_a=100, reach_a=1000)
        result = await service.analyze_results(test)
        assert result.winner == "A"
        assert "performe" in result.winner_insight

    @pytest.mark.asyncio
    async def test_get_tests_returns_list(self, service):
        tests = await service.get_tests_for_business("biz-123")
        assert isinstance(tests, list)

    @pytest.mark.asyncio
    async def test_generate_variants_with_dna_context(self, service):
        mock_resp = MagicMock()
        mock_resp.content = [
            MagicMock(
                text='{"caption_a":"A avec DNA","caption_b":"B avec DNA","strategy":"test","hypothesis":"hyp"}'
            )
        ]
        service._claude = MagicMock()
        service._claude.messages.create.return_value = mock_resp

        result = await service.generate_variants(
            "Caption",
            business_dna={"business_name": "Le Family's", "editorial_tone": "chaleureux"},
        )
        assert "caption_a" in result


class TestABTestingEndpoints:
    """Tests for A/B testing API route registration."""

    def test_ab_routes_registered(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("/ab" in p for p in paths), f"No AB routes in: {paths}"

    def test_create_route_exists(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("create" in p for p in paths)

    def test_tests_route_exists(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("tests" in p for p in paths)
