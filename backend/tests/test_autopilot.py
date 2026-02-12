"""Tests pour le mode autopilote (Sprint 9)."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, MagicMock


# ── Model Tests ─────────────────────────────────────────────────────


def test_autopilot_models_import():
    """Test importing autopilot models."""
    from app.models.autopilot import (
        AutopilotConfig,
        PendingPost,
        AutopilotFrequency,
        PendingPostStatus,
    )
    assert AutopilotConfig.__tablename__ == "autopilot_configs"
    assert PendingPost.__tablename__ == "pending_posts"
    assert AutopilotFrequency.DAILY.value == "daily"
    assert PendingPostStatus.PENDING.value == "pending"


def test_autopilot_frequency_enum():
    """Test all frequency values."""
    from app.models.autopilot import AutopilotFrequency
    assert AutopilotFrequency.DAILY.value == "daily"
    assert AutopilotFrequency.WEEKDAYS.value == "weekdays"
    assert AutopilotFrequency.THREE_PER_WEEK.value == "3_per_week"
    assert AutopilotFrequency.WEEKLY.value == "weekly"


def test_pending_post_status_enum():
    """Test all pending post status values."""
    from app.models.autopilot import PendingPostStatus
    assert PendingPostStatus.PENDING.value == "pending"
    assert PendingPostStatus.APPROVED.value == "approved"
    assert PendingPostStatus.REJECTED.value == "rejected"
    assert PendingPostStatus.AUTO_PUBLISHED.value == "auto_published"
    assert PendingPostStatus.EXPIRED.value == "expired"


def test_models_registered_in_init():
    """Test that autopilot models are registered in __init__."""
    from app.models import AutopilotConfig, PendingPost
    assert AutopilotConfig is not None
    assert PendingPost is not None


# ── WhatsApp Service Tests ──────────────────────────────────────────


def test_whatsapp_service_import():
    """Test importing WhatsApp service."""
    from app.services.whatsapp import WhatsAppService
    ws = WhatsAppService()
    assert hasattr(ws, "send_approval_message")
    assert hasattr(ws, "send_text_message")
    assert hasattr(ws, "is_configured")


def test_whatsapp_service_not_configured():
    """Test WhatsApp service reports not configured with empty settings."""
    from app.services.whatsapp import WhatsAppService
    with patch("app.services.whatsapp.settings") as mock_settings:
        mock_settings.whatsapp_token = ""
        mock_settings.whatsapp_phone_number_id = ""
        mock_settings.whatsapp_api_version = "v21.0"
        ws = WhatsAppService()
        assert ws.is_configured is False


@pytest.mark.asyncio
async def test_whatsapp_send_approval_not_configured():
    """Test send_approval_message returns None when not configured."""
    from app.services.whatsapp import WhatsAppService
    with patch("app.services.whatsapp.settings") as mock_settings:
        mock_settings.whatsapp_token = ""
        mock_settings.whatsapp_phone_number_id = ""
        mock_settings.whatsapp_api_version = "v21.0"
        ws = WhatsAppService()
        result = await ws.send_approval_message(
            to_phone="+33612345678",
            pending_post_id="test-id",
            platform="instagram",
            caption_preview="Test caption",
        )
        assert result is None


@pytest.mark.asyncio
async def test_whatsapp_send_text_not_configured():
    """Test send_text_message returns None when not configured."""
    from app.services.whatsapp import WhatsAppService
    with patch("app.services.whatsapp.settings") as mock_settings:
        mock_settings.whatsapp_token = ""
        mock_settings.whatsapp_phone_number_id = ""
        mock_settings.whatsapp_api_version = "v21.0"
        ws = WhatsAppService()
        result = await ws.send_text_message("+33612345678", "Hello")
        assert result is None


# ── Celery Tasks Tests ──────────────────────────────────────────────


def test_celery_tasks_import():
    """Test importing autopilot tasks."""
    from app.workers.tasks import autopilot_daily_generate, autopilot_check_auto_publish
    assert callable(autopilot_daily_generate)
    assert callable(autopilot_check_auto_publish)


def test_should_generate_today():
    """Test frequency-based generation logic."""
    from app.workers.tasks import _should_generate_today
    from app.models.autopilot import AutopilotFrequency

    # DAILY should always return True
    assert _should_generate_today(AutopilotFrequency.DAILY) is True


def test_build_autopilot_prompt():
    """Test autopilot prompt building."""
    from app.workers.tasks import _build_autopilot_prompt
    # Create a mock brand
    mock_brand = MagicMock()
    mock_brand.name = "Test Brand"
    mock_brand.description = "A test brand"
    mock_brand.brand_type.value = "restaurant"
    mock_brand.target_persona = None
    mock_brand.locations = ["Paris"]
    mock_brand.voice = None

    prompt = _build_autopilot_prompt(mock_brand, "instagram", "marketing")
    assert "Test Brand" in prompt
    assert "instagram" in prompt
    assert "marketing" in prompt


def test_build_autopilot_prompt_with_voice():
    """Test autopilot prompt building with brand voice."""
    from app.workers.tasks import _build_autopilot_prompt
    mock_brand = MagicMock()
    mock_brand.name = "Voice Brand"
    mock_brand.description = "Description"
    mock_brand.brand_type.value = "saas"
    mock_brand.target_persona = {"name": "Devs"}
    mock_brand.locations = None
    mock_brand.voice = MagicMock()
    mock_brand.voice.tone_formal = 80
    mock_brand.voice.tone_playful = 20
    mock_brand.voice.tone_bold = 60
    mock_brand.voice.words_to_avoid = ["spam", "free"]
    mock_brand.voice.words_to_prefer = ["innovant"]
    mock_brand.voice.custom_instructions = "Sois concis"

    prompt = _build_autopilot_prompt(mock_brand, "linkedin")
    assert "Voice Brand" in prompt
    assert "80" in prompt  # tone_formal
    assert "spam" in prompt
    assert "innovant" in prompt
    assert "Sois concis" in prompt


def test_str_to_platform_enum():
    """Test platform string to enum conversion."""
    from app.workers.tasks import _str_to_platform_enum
    from app.models.publishing import SocialPlatform

    assert _str_to_platform_enum("instagram") == SocialPlatform.INSTAGRAM
    assert _str_to_platform_enum("linkedin") == SocialPlatform.LINKEDIN
    assert _str_to_platform_enum("tiktok") == SocialPlatform.TIKTOK
    assert _str_to_platform_enum("facebook") == SocialPlatform.FACEBOOK
    # Unknown defaults to Instagram
    assert _str_to_platform_enum("unknown") == SocialPlatform.INSTAGRAM


# ── Schema Tests ────────────────────────────────────────────────────


def test_autopilot_schemas_import():
    """Test importing autopilot schemas."""
    from app.schemas.autopilot import (
        AutopilotConfigCreate,
        AutopilotConfigUpdate,
        AutopilotConfigResponse,
        PendingPostResponse,
        PendingPostAction,
    )
    assert AutopilotConfigCreate is not None
    assert PendingPostAction is not None


def test_autopilot_config_create_defaults():
    """Test AutopilotConfigCreate with defaults."""
    from app.schemas.autopilot import AutopilotConfigCreate
    config = AutopilotConfigCreate()
    assert config.platforms == ["instagram"]
    assert config.frequency == "daily"
    assert config.generation_hour == 7
    assert config.auto_publish is False
    assert config.approval_window_hours == 4


def test_pending_post_action_validation():
    """Test PendingPostAction validation."""
    from app.schemas.autopilot import PendingPostAction

    # Valid actions
    action = PendingPostAction(action="approve")
    assert action.action == "approve"

    action = PendingPostAction(action="reject")
    assert action.action == "reject"

    # Invalid action should raise
    with pytest.raises(Exception):
        PendingPostAction(action="invalid")


# ── API Endpoint Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_autopilot_config_endpoint_unauthorized():
    """Test autopilot config requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/autopilot/brands/00000000-0000-0000-0000-000000000001/autopilot"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_autopilot_create_endpoint_unauthorized():
    """Test autopilot create requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/autopilot/brands/00000000-0000-0000-0000-000000000001/autopilot",
            json={"platforms": ["instagram"]},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_autopilot_toggle_endpoint_unauthorized():
    """Test autopilot toggle requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/autopilot/brands/00000000-0000-0000-0000-000000000001/autopilot/toggle"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_autopilot_pending_endpoint_unauthorized():
    """Test pending posts list requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/autopilot/brands/00000000-0000-0000-0000-000000000001/autopilot/pending"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_autopilot_generate_endpoint_unauthorized():
    """Test manual generation requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/autopilot/brands/00000000-0000-0000-0000-000000000001/autopilot/generate"
        )
        assert response.status_code == 401


# ── Webhook Tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_whatsapp_webhook_verify():
    """Test WhatsApp webhook verification."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "presenceos-webhook-verify",
            },
        )
        assert response.status_code == 200
        assert response.json() == 12345


@pytest.mark.asyncio
async def test_whatsapp_webhook_verify_invalid_token():
    """Test WhatsApp webhook with wrong verify token."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "wrong-token",
            },
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_whatsapp_webhook_post_empty():
    """Test WhatsApp webhook with empty payload returns 200."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhooks/whatsapp",
            json={"entry": []},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ── Beat Schedule Tests ─────────────────────────────────────────────


def test_celery_beat_schedule_has_autopilot():
    """Test celery beat schedule includes autopilot tasks."""
    from app.workers.celery_app import celery_app
    schedule = celery_app.conf.beat_schedule
    assert "autopilot-daily-generate" in schedule
    assert "autopilot-check-auto-publish" in schedule
    assert schedule["autopilot-daily-generate"]["task"] == "app.workers.tasks.autopilot_daily_generate"
    assert schedule["autopilot-check-auto-publish"]["task"] == "app.workers.tasks.autopilot_check_auto_publish"


# ── Config Tests ────────────────────────────────────────────────────


def test_config_has_whatsapp_settings():
    """Test that config includes WhatsApp settings."""
    from app.core.config import Settings
    fields = Settings.model_fields
    assert "whatsapp_token" in fields
    assert "whatsapp_phone_number_id" in fields
    assert "whatsapp_verify_token" in fields
    assert "whatsapp_api_version" in fields
    assert "whatsapp_webhook_secret" in fields


# ── Router Registration Tests ───────────────────────────────────────


def test_autopilot_router_registered():
    """Test that autopilot router is registered in API."""
    from app.api.v1.router import api_router
    route_paths = [route.path for route in api_router.routes]
    # Check that autopilot prefix is registered (routes contain /autopilot)
    autopilot_routes = [p for p in route_paths if "autopilot" in p]
    assert len(autopilot_routes) > 0


def test_whatsapp_webhook_router_registered():
    """Test that webhook router is registered in main app."""
    from app.main import app
    route_paths = [route.path for route in app.routes]
    webhook_routes = [p for p in route_paths if "webhook" in p.lower()]
    assert len(webhook_routes) > 0
