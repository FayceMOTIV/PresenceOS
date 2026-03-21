"""
Tests for the War Room — StrategicAnalyzer service, war_room endpoints, imports.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.strategic_analyzer import StrategicAnalyzer, strategic_analyzer


def _make_mock_claude(response_text: str) -> MagicMock:
    """Create a mock Anthropic client with a preset response."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = response_text
    mock.messages = AsyncMock()
    mock.messages.create = AsyncMock(return_value=mock_response)
    return mock


# ── StrategicAnalyzer ──


def test_strategic_analyzer_importable():
    assert strategic_analyzer is not None
    assert isinstance(strategic_analyzer, StrategicAnalyzer)


def test_parse_json_valid():
    result = strategic_analyzer._parse_json('{"key": "value"}')
    assert result["key"] == "value"


def test_parse_json_with_backticks():
    result = strategic_analyzer._parse_json('```json\n{"key": "value"}\n```')
    assert result["key"] == "value"


def test_parse_json_fallback_on_invalid():
    result = strategic_analyzer._parse_json("texte non-JSON quelconque")
    assert "ilyas_response" in result
    assert result["urgency"] == "medium"


def test_parse_json_complex():
    raw = '```json\n{"action_plan": {"this_week": ["a", "b"]}, "ilyas_response": "test"}\n```'
    result = strategic_analyzer._parse_json(raw)
    assert result["action_plan"]["this_week"] == ["a", "b"]
    assert result["ilyas_response"] == "test"


def test_parse_json_empty_string():
    result = strategic_analyzer._parse_json("")
    assert "ilyas_response" in result


# ── Analyze text (mocked Claude) ──


@pytest.mark.asyncio
async def test_analyze_text_returns_structured():
    """analyze_text returns structured JSON with action_plan."""
    analyzer = StrategicAnalyzer()
    analyzer._claude = _make_mock_claude(
        '{"understanding": "test", "key_insight": "insight", "action_plan": {"this_week": ["a"]}, "ilyas_response": "OK"}'
    )

    with patch.object(analyzer, "_save_to_memory", new_callable=AsyncMock):
        result = await analyzer.analyze_text(
            "Mon concurrent fait des reels tous les jours",
            {"id": "test-uuid", "name": "Test Resto"},
            {"label": "Restaurant / Café"},
        )
    assert result["understanding"] == "test"
    assert result["key_insight"] == "insight"
    assert "action_plan" in result


@pytest.mark.asyncio
async def test_analyze_text_saves_to_memory():
    """analyze_text calls _save_to_memory."""
    analyzer = StrategicAnalyzer()
    analyzer._claude = _make_mock_claude(
        '{"ilyas_response": "OK", "key_insight": "test"}'
    )

    with patch.object(analyzer, "_save_to_memory", new_callable=AsyncMock) as mock_save:
        await analyzer.analyze_text(
            "Idée de menu saisonnier",
            {"id": "brand-1", "name": "Resto"},
            {"label": "Restaurant"},
        )
        mock_save.assert_called_once()


# ── Analyze URL (mocked) ──


@pytest.mark.asyncio
async def test_analyze_url_returns_structured():
    """analyze_url calls _fetch_url then Claude."""
    analyzer = StrategicAnalyzer()
    analyzer._claude = _make_mock_claude(
        '{"summary": "test", "action_plan": {"this_week": ["a"]}, "ilyas_response": "OK"}'
    )

    with patch.object(analyzer, "_fetch_url", new_callable=AsyncMock, return_value="contenu web"):
        result = await analyzer.analyze_url(
            "https://www.tiktok.com/@concurrent",
            {"id": "test", "name": "Resto"},
            {"label": "Restaurant"},
        )
    assert result["summary"] == "test"
    assert "action_plan" in result


# ── Analyze audio (mocked) ──


@pytest.mark.asyncio
async def test_analyze_audio_failure_returns_fallback():
    """analyze_audio returns fallback when Whisper fails."""
    analyzer = StrategicAnalyzer()

    with patch("app.services.strategic_analyzer.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        result = await analyzer.analyze_audio(
            b"fake audio bytes",
            {"id": "test", "name": "Resto"},
            {"label": "Restaurant"},
        )
        assert "ilyas_response" in result


# ── Image analyze fallback ──


@pytest.mark.asyncio
async def test_analyze_image_claude_fallback():
    """_analyze_image_claude returns fallback on failure."""
    analyzer = StrategicAnalyzer()
    mock_claude = MagicMock()
    mock_claude.messages = AsyncMock()
    mock_claude.messages.create = AsyncMock(side_effect=Exception("API error"))
    analyzer._claude = mock_claude

    result = await analyzer._analyze_image_claude(
        b"fake image",
        {"id": "test", "name": "Resto"},
        {"label": "Restaurant"},
        "note",
    )
    assert "ilyas_response" in result
    assert result["marketing_potential"] == "medium"


@pytest.mark.asyncio
async def test_analyze_image_gemini_fallback_to_claude():
    """analyze_image falls back to Claude when Gemini fails."""
    analyzer = StrategicAnalyzer()
    analyzer._claude = _make_mock_claude(
        '{"caption_instagram": "Test caption", "ilyas_response": "OK"}'
    )

    with patch("app.services.strategic_analyzer.settings") as mock_settings:
        mock_settings.google_api_key = ""
        mock_settings.gemini_api_key = ""

        result = await analyzer.analyze_image(
            b"fake image bytes",
            {"id": "test", "name": "Resto"},
            {"label": "Restaurant"},
            "test note",
        )
    assert "ilyas_response" in result


# ── Endpoint imports ──


def test_war_room_router_importable():
    from app.api.v2.endpoints.war_room import router
    assert router is not None


def test_v2_router_includes_war_room():
    from app.api.v2.router import api_v2_router
    route_paths = [r.path for r in api_v2_router.routes]
    war_room_routes = [p for p in route_paths if "war-room" in p]
    assert len(war_room_routes) > 0, "War Room routes not found in v2 router"


def test_war_room_has_all_endpoints():
    from app.api.v2.endpoints.war_room import router
    route_paths = [r.path for r in router.routes]
    assert any("analyze-text" in p for p in route_paths)
    assert any("analyze-url" in p for p in route_paths)
    assert any("analyze-image" in p for p in route_paths)
    assert any("analyze-audio" in p for p in route_paths)


# ── Save to memory (non-blocking) ──


@pytest.mark.asyncio
async def test_save_to_memory_handles_error_gracefully():
    """_save_to_memory should not raise even if Mem0 fails."""
    analyzer = StrategicAnalyzer()

    await analyzer._save_to_memory(
        "test input",
        {"key_insight": "test", "action_plan": {}},
        {"id": "brand-1"},
    )
    # Should not raise — Mem0 not configured in test env, logs warning
