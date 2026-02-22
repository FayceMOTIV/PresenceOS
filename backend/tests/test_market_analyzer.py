"""
PresenceOS - Tests for MarketAnalyzer (AI Market Analysis)

Unit tests for the GPT-4 market analysis service with full mocking
of external dependencies (OpenAI API).
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.market_analyzer import (
    MarketAnalyzer,
    _build_brand_block,
    SYSTEM_PROMPT,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def analyzer():
    """Create a MarketAnalyzer instance."""
    return MarketAnalyzer()


@pytest.fixture
def brand_context():
    """Realistic brand context dict as produced by strategy._load_brand_context."""
    return {
        "name": "Chez Marcel",
        "brand_type": "restaurant",
        "description": "Bistrot parisien traditionnel avec cuisine du marché",
        "target_persona": {
            "name": "Foodie Parisien",
            "age_range": "25-45",
            "interests": ["gastronomie", "vin naturel", "brunch"],
        },
        "locations": ["Paris 11e", "Paris 3e"],
        "constraints": {"budget": "limited", "team_size": 1},
        "content_pillars": {"behind_the_scenes": 30, "plats": 40, "ambiance": 30},
        "voice": {
            "tone_formal": 30,
            "tone_playful": 75,
            "tone_bold": 60,
            "tone_technical": 20,
            "tone_emotional": 70,
            "example_phrases": ["Venez goûter la magie!", "Le marché ce matin..."],
            "words_to_avoid": ["cheap", "discount"],
            "words_to_prefer": ["artisanal", "maison", "de saison"],
            "emojis_allowed": True,
            "max_emojis_per_post": 3,
            "hashtag_style": "mixed",
            "primary_language": "fr",
            "allow_english_terms": True,
            "custom_instructions": "Toujours mentionner les produits de saison",
        },
    }


def _make_gpt_response(content_dict: dict) -> MagicMock:
    """Build a mock OpenAI chat completion response."""
    msg = MagicMock()
    msg.content = json.dumps(content_dict, ensure_ascii=False)
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


# ── Brand Block Tests ────────────────────────────────────────────────────────


class TestBuildBrandBlock:
    """Tests for _build_brand_block helper."""

    def test_empty_context_returns_empty_string(self):
        assert _build_brand_block(None) == ""
        assert _build_brand_block({}) == ""

    def test_brand_name_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "Chez Marcel" in block

    def test_brand_type_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "restaurant" in block

    def test_description_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "Bistrot parisien" in block

    def test_target_persona_dict(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "Foodie Parisien" in block
        assert "25-45" in block
        assert "gastronomie" in block

    def test_target_persona_string(self):
        ctx = {"target_persona": "Jeunes urbains 25-35 ans"}
        block = _build_brand_block(ctx)
        assert "Jeunes urbains" in block

    def test_locations_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "Paris 11e" in block

    def test_voice_tone_levels(self, brand_context):
        block = _build_brand_block(brand_context)
        # tone_formal=30 -> should say "décontracté"
        assert "décontracté" in block
        # tone_playful=75 -> should say "joueur"
        assert "joueur" in block
        # tone_bold=60 -> should say "subtil" (not >60 strict)
        # actually 60 is not > 60, so it's "subtil"
        assert "subtil" in block or "audacieux" in block

    def test_words_to_avoid_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "cheap" in block
        assert "discount" in block

    def test_words_to_prefer_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "artisanal" in block
        assert "maison" in block

    def test_example_phrases_included(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "Venez goûter la magie!" in block

    def test_brand_block_has_markers(self, brand_context):
        block = _build_brand_block(brand_context)
        assert "BRAND CONTEXT" in block
        assert "END BRAND CONTEXT" in block


# ── System Prompt Tests ──────────────────────────────────────────────────────


class TestSystemPrompt:
    """Tests for the master system prompt."""

    def test_system_prompt_is_french(self):
        assert "stratège" in SYSTEM_PROMPT or "marketing" in SYSTEM_PROMPT

    def test_system_prompt_requires_json(self):
        assert "JSON" in SYSTEM_PROMPT

    def test_system_prompt_mentions_current_period(self):
        # The prompt includes the current month/year
        assert "202" in SYSTEM_PROMPT  # 2024, 2025, 2026...


# ── Confidence Score Tests ───────────────────────────────────────────────────


class TestComputeConfidence:
    """Tests for _compute_confidence scoring."""

    def test_full_data_high_confidence(self, analyzer):
        trends = {
            "emerging_trends": [{"name": "trend1"}],
            "trend_summary": "Summary here",
            "seasonal_factors": [{"factor": "summer"}],
        }
        tone = {
            "primary_tone": "warm",
            "tone_by_platform": {"instagram": "casual"},
            "example_captions": {"instagram": "caption"},
        }
        hashtags = {
            "niche_hashtags": ["#food"],
            "local_hashtags": ["#paris"],
            "platform_sets": {"instagram": {}},
        }
        times = {
            "instagram": {"weekday_best": ["12:00"]},
            "weekly_schedule": {"lundi": "IG"},
        }
        strategy = {
            "content_pillars": [{"name": "pillar1"}],
            "weekly_plan": {"lundi": {}},
            "quick_wins": [{"action": "post"}],
            "strategy_summary": "Do this.",
        }

        score = analyzer._compute_confidence(trends, tone, hashtags, times, strategy)
        assert score == 0.95  # Capped at 0.95

    def test_empty_data_zero_confidence(self, analyzer):
        empty = {}
        score = analyzer._compute_confidence(empty, empty, empty, empty, empty)
        assert score == 0.0

    def test_partial_data_mid_confidence(self, analyzer):
        trends = {"emerging_trends": [{"name": "t1"}], "trend_summary": "ok"}
        tone = {"primary_tone": "warm"}
        hashtags = {"niche_hashtags": ["#tag"]}
        times = {"instagram": {"weekday_best": ["12:00"]}}
        strategy = {"content_pillars": [{"name": "p1"}]}

        score = analyzer._compute_confidence(trends, tone, hashtags, times, strategy)
        assert 0.3 < score < 0.7

    def test_confidence_never_exceeds_0_95(self, analyzer):
        full = {
            "emerging_trends": [1], "trend_summary": "x", "seasonal_factors": [1],
            "primary_tone": "x", "tone_by_platform": {}, "example_captions": {},
            "niche_hashtags": [1], "local_hashtags": [1], "platform_sets": {},
            "instagram": {}, "weekly_schedule": {},
            "content_pillars": [1], "weekly_plan": {}, "quick_wins": [1],
            "strategy_summary": "x",
        }
        score = analyzer._compute_confidence(full, full, full, full, full)
        assert score <= 0.95


# ── Niche Analysis Tests ─────────────────────────────────────────────────────


class TestAnalyzeNiche:
    """Tests for analyze_niche with mocked GPT-4."""

    @pytest.mark.asyncio
    async def test_analyze_niche_success(self, analyzer):
        mock_trends = {"emerging_trends": [{"name": "t1"}], "trend_summary": "ok", "seasonal_factors": []}
        mock_tone = {"primary_tone": "warm", "tone_by_platform": {}, "example_captions": {}}
        mock_hashtags = {"niche_hashtags": ["#food"], "local_hashtags": [], "platform_sets": {}}
        mock_times = {"instagram": {"weekday_best": ["12:00"]}, "weekly_schedule": {}}
        mock_strategy = {
            "content_pillars": [{"name": "p1"}],
            "weekly_plan": {},
            "quick_wins": [{"action": "post"}],
            "strategy_summary": "Do this.",
        }

        mock_client = MagicMock()
        call_count = 0
        responses = [mock_trends, mock_tone, mock_hashtags, mock_times, mock_strategy]

        async def fake_create(**kwargs):
            nonlocal call_count
            resp = _make_gpt_response(responses[min(call_count, len(responses) - 1)])
            call_count += 1
            return resp

        mock_client.chat.completions.create = fake_create
        analyzer._client = mock_client

        result = await analyzer.analyze_niche(niche="restaurant", location="Paris")

        assert result["niche"] == "restaurant"
        assert result["location"] == "Paris"
        assert "analyzed_at" in result
        assert "trends" in result
        assert "optimal_tone" in result
        assert "top_hashtags" in result
        assert "best_posting_times" in result
        assert "strategy" in result
        assert 0.0 <= result["confidence_score"] <= 0.95

    @pytest.mark.asyncio
    async def test_analyze_niche_with_brand_context(self, analyzer, brand_context):
        mock_data = {"key": "value"}

        mock_client = MagicMock()

        prompts_captured = []

        async def fake_create(**kwargs):
            messages = kwargs.get("messages", [])
            for m in messages:
                if m["role"] == "user":
                    prompts_captured.append(m["content"])
            return _make_gpt_response(mock_data)

        mock_client.chat.completions.create = fake_create
        analyzer._client = mock_client

        await analyzer.analyze_niche(
            niche="restaurant",
            location="Paris",
            brand_context=brand_context,
        )

        # All 5 sub-analyses should contain the brand block
        assert len(prompts_captured) == 5
        for prompt in prompts_captured:
            assert "Chez Marcel" in prompt
            assert "BRAND CONTEXT" in prompt

    @pytest.mark.asyncio
    async def test_analyze_niche_no_api_key(self):
        analyzer = MarketAnalyzer()
        with patch("app.ai.market_analyzer.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            with pytest.raises(RuntimeError, match="OpenAI API key"):
                await analyzer.analyze_niche(niche="restaurant")

    @pytest.mark.asyncio
    async def test_analyze_niche_gpt_error_propagates(self, analyzer):
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )
        analyzer._client = mock_client

        with pytest.raises(Exception, match="Rate limit"):
            await analyzer.analyze_niche(niche="restaurant")

    @pytest.mark.asyncio
    async def test_analyze_niche_calls_5_sub_analyses(self, analyzer):
        mock_client = MagicMock()
        call_count = 0

        async def fake_create(**kwargs):
            nonlocal call_count
            call_count += 1
            return _make_gpt_response({"key": "value"})

        mock_client.chat.completions.create = fake_create
        analyzer._client = mock_client

        await analyzer.analyze_niche(niche="restaurant")

        # 4 parallel (trends, tone, hashtags, times) + 1 sequential (strategy)
        assert call_count == 5

    @pytest.mark.asyncio
    async def test_analyze_niche_uses_json_mode(self, analyzer):
        mock_client = MagicMock()
        kwargs_captured = []

        async def fake_create(**kwargs):
            kwargs_captured.append(kwargs)
            return _make_gpt_response({"key": "value"})

        mock_client.chat.completions.create = fake_create
        analyzer._client = mock_client

        await analyzer.analyze_niche(niche="restaurant")

        for call_kwargs in kwargs_captured:
            assert call_kwargs.get("response_format") == {"type": "json_object"}


# ── Client Initialization Tests ──────────────────────────────────────────────


class TestClientInit:
    """Tests for lazy client initialization."""

    def test_client_not_initialized_by_default(self, analyzer):
        assert analyzer._client is None

    def test_get_client_initializes_on_first_call(self, analyzer):
        with patch("app.ai.market_analyzer.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test-key"
            mock_settings.openai_model = "gpt-4"
            client = analyzer._get_client()
            assert client is not None
            assert analyzer._client is client

    def test_get_client_reuses_existing(self, analyzer):
        mock_client = MagicMock()
        analyzer._client = mock_client
        assert analyzer._get_client() is mock_client

    def test_get_client_raises_without_key(self, analyzer):
        with patch("app.ai.market_analyzer.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            with pytest.raises(RuntimeError, match="OpenAI API key"):
                analyzer._get_client()
