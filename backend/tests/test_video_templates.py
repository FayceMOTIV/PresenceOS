"""
Tests for Video Templates — Breakout V4 + Cinematic Food
"""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Breakout V4 Engine Tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_breakout_v4_prepare_returns_assets():
    """prepare() returns dict with original_url and cutout_url."""
    with patch(
        "app.services.breakout.breakout_v4_engine.BreakoutV4Engine._download_image",
        new_callable=AsyncMock,
        return_value=b"fake_image_bytes",
    ), patch(
        "app.services.breakout.breakout_v4_engine.BreakoutV4Engine._remove_background",
        return_value=b"fake_cutout_bytes",
    ), patch(
        "app.services.breakout.breakout_v4_engine.BreakoutV4Engine._upload_to_fal",
        side_effect=["https://fal.ai/original.jpg", "https://fal.ai/cutout.png"],
    ):
        from app.services.breakout.breakout_v4_engine import BreakoutV4Engine

        engine = BreakoutV4Engine()
        result = await engine.prepare(
            image_url="https://example.com/food.jpg",
            brand_id="test-brand",
        )

        assert "original_url" in result
        assert "cutout_url" in result
        assert result["original_url"] == "https://fal.ai/original.jpg"
        assert result["cutout_url"] == "https://fal.ai/cutout.png"


@pytest.mark.asyncio
async def test_breakout_v4_render_persists_to_s3():
    """render() calls Remotion and persists video to S3."""
    mock_video_bytes = b"fake_mp4_data"

    with patch(
        "app.services.breakout.breakout_v4_engine.BreakoutV4Engine._call_remotion_v4",
        new_callable=AsyncMock,
        return_value=mock_video_bytes,
    ), patch(
        "app.services.breakout.breakout_v4_engine.BreakoutV4Engine._persist_to_s3",
        new_callable=AsyncMock,
        return_value="https://s3.example.com/breakout-v4.mp4",
    ):
        from app.services.breakout.breakout_v4_engine import BreakoutV4Engine

        engine = BreakoutV4Engine()
        result = await engine.render(
            original_url="https://fal.ai/original.jpg",
            cutout_url="https://fal.ai/cutout.png",
            brand_id="test-brand",
        )

        assert result["video_url"] == "https://s3.example.com/breakout-v4.mp4"
        assert result["duration_seconds"] == 3


# ── Cinematic Food Service Tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_cinematic_food_generate():
    """generate() calls fal.ai and persists to S3."""
    mock_fal_result = {"video": {"url": "https://fal.ai/temp-video.mp4"}}

    with patch("app.services.cinematic_food_service.settings") as mock_settings, \
         patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_fal_result), \
         patch(
             "app.services.cinematic_food_service.CinematicFoodService._persist_video",
             new_callable=AsyncMock,
             return_value="https://s3.example.com/cinematic.mp4",
         ):
        mock_settings.fal_key = "test-key"

        from app.services.cinematic_food_service import CinematicFoodService

        svc = CinematicFoodService()
        result = await svc.generate(
            image_url="https://example.com/burger.jpg",
            brand_id="test-brand",
            food_type="burger",
            duration=5,
        )

        assert result["video_url"] == "https://s3.example.com/cinematic.mp4"
        assert result["food_type"] == "burger"
        assert result["duration"] == 5
        assert result["cost_usd"] == 0.35


@pytest.mark.asyncio
async def test_cinematic_food_10s_cost():
    """10s video costs $0.70."""
    mock_fal_result = {"video": {"url": "https://fal.ai/temp.mp4"}}

    with patch("app.services.cinematic_food_service.settings") as mock_settings, \
         patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_fal_result), \
         patch(
             "app.services.cinematic_food_service.CinematicFoodService._persist_video",
             new_callable=AsyncMock,
             return_value="https://s3.example.com/cinematic10.mp4",
         ):
        mock_settings.fal_key = "test-key"

        from app.services.cinematic_food_service import CinematicFoodService

        svc = CinematicFoodService()
        result = await svc.generate(
            image_url="https://example.com/pizza.jpg",
            brand_id="test-brand",
            food_type="pizza",
            duration=10,
        )

        assert result["cost_usd"] == 0.70
        assert result["duration"] == 10


def test_cinematic_food_prompts_exist():
    """All food types have prompts defined."""
    from app.services.cinematic_food_service import CINEMATIC_FOOD_PROMPTS, VALID_FOOD_TYPES

    for ft in VALID_FOOD_TYPES:
        assert ft in CINEMATIC_FOOD_PROMPTS
        assert len(CINEMATIC_FOOD_PROMPTS[ft]) > 20


# ── API Endpoint Tests (import check) ──────────────────────────────


def test_video_templates_router_importable():
    """video_templates router imports without error."""
    from app.api.v2.endpoints.video_templates import router

    assert router is not None
    routes = [r.path for r in router.routes]
    assert any("breakout-v4" in r for r in routes)
    assert any("cinematic" in r for r in routes)


def test_cinematic_pricing_response():
    """Pricing endpoint has correct structure."""
    from app.api.v2.endpoints.video_templates import CinematicPricingResponse

    resp = CinematicPricingResponse(
        pricing={
            "5s_no_audio": 0.35,
            "5s_with_audio": 0.70,
            "10s_no_audio": 0.70,
            "10s_with_audio": 1.40,
        },
    )
    assert resp.model == "kling-2.6-pro"
    assert resp.pricing["5s_no_audio"] == 0.35
