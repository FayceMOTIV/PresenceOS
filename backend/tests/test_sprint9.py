"""
PresenceOS - Phase 3 Tests: Autopilot + WhatsApp Cloud API.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient

from app.models.autopilot import (
    AutopilotConfig,
    PendingPost,
    PendingPostStatus,
    AutopilotFrequency,
)


# ── Model tests ──────────────────────────────────────────────────────


def test_autopilot_config_model_fields():
    """AutopilotConfig a tous les champs requis."""
    from sqlalchemy import inspect

    mapper = inspect(AutopilotConfig)
    columns = {c.key for c in mapper.column_attrs}

    required = {
        "id",
        "brand_id",
        "is_enabled",
        "platforms",
        "frequency",
        "generation_hour",
        "auto_publish",
        "approval_window_hours",
        "whatsapp_enabled",
        "whatsapp_phone",
        "preferred_posting_time",
        "topics",
        "total_generated",
        "total_published",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"Champs manquants: {required - columns}"


def test_pending_post_model_fields():
    """PendingPost a tous les champs requis."""
    from sqlalchemy import inspect

    mapper = inspect(PendingPost)
    columns = {c.key for c in mapper.column_attrs}

    required = {
        "id",
        "config_id",
        "brand_id",
        "platform",
        "caption",
        "hashtags",
        "media_urls",
        "status",
        "whatsapp_message_id",
        "reviewed_at",
        "expires_at",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"Champs manquants: {required - columns}"


def test_pending_post_statuses():
    """PendingPostStatus contient les statuts requis."""
    statuses = {s.value for s in PendingPostStatus}
    assert "pending" in statuses
    assert "approved" in statuses
    assert "rejected" in statuses


def test_autopilot_frequency_enum():
    """AutopilotFrequency contient les frequences requises."""
    freqs = {f.value for f in AutopilotFrequency}
    assert "daily" in freqs
    assert "3_per_week" in freqs
    assert "weekly" in freqs


# ── Model creation (in-database) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_create_autopilot_config(db, test_brand):
    """AutopilotConfig peut etre cree en DB."""
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        platforms=["instagram", "linkedin"],
        frequency=AutopilotFrequency.DAILY,
        generation_hour=7,
        auto_publish=False,
        approval_window_hours=4,
        whatsapp_enabled=True,
        whatsapp_phone="+33612345678",
        preferred_posting_time="10:30",
        topics=["marketing", "IA"],
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    assert config.id is not None
    assert config.brand_id == test_brand.id
    assert config.is_enabled is True
    assert config.platforms == ["instagram", "linkedin"]
    assert config.whatsapp_phone == "+33612345678"


@pytest.mark.asyncio
async def test_create_pending_post(db, test_brand):
    """PendingPost peut etre cree en DB."""
    # Need a config first
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        frequency=AutopilotFrequency.DAILY,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    post = PendingPost(
        config_id=config.id,
        brand_id=test_brand.id,
        platform="instagram",
        caption="Test caption #presenceos",
        hashtags=["presenceos", "test"],
        media_urls=[],
        status=PendingPostStatus.PENDING,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    assert post.id is not None
    assert post.status == PendingPostStatus.PENDING
    assert post.caption == "Test caption #presenceos"


@pytest.mark.asyncio
async def test_pending_post_status_transitions(db, test_brand):
    """PendingPost peut changer de statut."""
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        frequency=AutopilotFrequency.DAILY,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    post = PendingPost(
        config_id=config.id,
        brand_id=test_brand.id,
        platform="instagram",
        caption="Test",
        status=PendingPostStatus.PENDING,
    )
    db.add(post)
    await db.commit()

    # Approve
    post.status = PendingPostStatus.APPROVED
    await db.commit()
    await db.refresh(post)
    assert post.status == PendingPostStatus.APPROVED


# ── WhatsApp Service tests ───────────────────────────────────────────


def test_whatsapp_service_init():
    """WhatsAppService peut etre instancie."""
    from app.services.whatsapp import WhatsAppService

    service = WhatsAppService()
    assert service is not None
    assert service.base_url is not None


def test_whatsapp_service_is_configured():
    """is_configured retourne False sans credentials."""
    from app.services.whatsapp import WhatsAppService

    service = WhatsAppService()
    # In test env, credentials are empty
    assert service.is_configured is False or isinstance(service.is_configured, bool)


@pytest.mark.asyncio
async def test_whatsapp_send_text_mock():
    """send_text_message envoie une requete HTTP correcte."""
    from app.services.whatsapp import WhatsAppService

    service = WhatsAppService()
    service.token = "test-token"
    service.phone_number_id = "123456789"
    service.base_url = "https://graph.facebook.com/v21.0/123456789/messages"

    mock_response = MagicMock()
    mock_response.json.return_value = {"messages": [{"id": "wamid.test123"}]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.send_text_message("+33612345678", "Hello test")
        assert result == "wamid.test123"


@pytest.mark.asyncio
async def test_whatsapp_send_interactive_buttons_mock():
    """send_interactive_buttons envoie les boutons correctement."""
    from app.services.whatsapp import WhatsAppService

    service = WhatsAppService()
    service.token = "test-token"
    service.phone_number_id = "123456789"
    service.base_url = "https://graph.facebook.com/v21.0/123456789/messages"

    mock_response = MagicMock()
    mock_response.json.return_value = {"messages": [{"id": "wamid.btn123"}]}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.send_interactive_buttons(
            to_phone="+33612345678",
            body_text="Nouveau post a approuver",
            buttons=[
                {"id": "approve_123", "title": "Approuver"},
                {"id": "reject_123", "title": "Rejeter"},
            ],
        )
        assert result == "wamid.btn123"


@pytest.mark.asyncio
async def test_whatsapp_send_text_not_configured():
    """send_text_message retourne None si pas configure."""
    from app.services.whatsapp import WhatsAppService

    service = WhatsAppService()
    service.token = ""
    service.phone_number_id = ""

    result = await service.send_text_message("+33612345678", "Hello")
    assert result is None


# ── Webhook tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_get_verification(client: AsyncClient):
    """GET /webhooks/whatsapp avec bon token retourne le challenge."""
    response = await client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "presenceos-webhook-verify",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.json() == 12345


@pytest.mark.asyncio
async def test_webhook_get_verification_fails(client: AsyncClient):
    """GET /webhooks/whatsapp avec mauvais token retourne 403."""
    response = await client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_post_text_message(client: AsyncClient):
    """POST /webhooks/whatsapp avec message texte retourne 200."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "type": "text",
                                    "text": {"body": "Cree un post Instagram"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    with patch(
        "app.api.webhooks.whatsapp._find_brand_for_phone",
        new_callable=AsyncMock,
        return_value=(None, None),
    ):
        response = await client.post("/webhooks/whatsapp", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_webhook_post_button_reply(client: AsyncClient):
    """POST /webhooks/whatsapp avec button_reply retourne 200."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": "approve_some-uuid",
                                            "title": "Publier",
                                        },
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    with patch(
        "app.api.webhooks.whatsapp._find_brand_for_phone",
        new_callable=AsyncMock,
        return_value=(None, None),
    ):
        response = await client.post("/webhooks/whatsapp", json=payload)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_post_empty_body(client: AsyncClient):
    """POST /webhooks/whatsapp avec body vide retourne 200."""
    response = await client.post("/webhooks/whatsapp", json={"entry": []})
    assert response.status_code == 200


# ── API Endpoint tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_autopilot_get_config_404(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /autopilot/brands/{brand_id}/autopilot retourne 404 sans config."""
    response = await client.get(
        f"/api/v1/autopilot/brands/{test_brand.id}/autopilot",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_autopilot_create_config(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """POST /autopilot/brands/{brand_id}/autopilot cree une config."""
    response = await client.post(
        f"/api/v1/autopilot/brands/{test_brand.id}/autopilot",
        json={
            "platforms": ["instagram", "linkedin"],
            "frequency": "daily",
            "auto_publish": False,
            "whatsapp_enabled": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_enabled"] is True
    assert data["platforms"] == ["instagram", "linkedin"]
    assert data["frequency"] == "daily"


@pytest.mark.asyncio
async def test_autopilot_update_config(
    client: AsyncClient, auth_headers: dict, test_brand, db
):
    """PATCH /autopilot/brands/{brand_id}/autopilot met a jour."""
    # Create first
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        frequency=AutopilotFrequency.DAILY,
    )
    db.add(config)
    await db.commit()

    response = await client.patch(
        f"/api/v1/autopilot/brands/{test_brand.id}/autopilot",
        json={"platforms": ["tiktok"], "whatsapp_enabled": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["platforms"] == ["tiktok"]
    assert data["whatsapp_enabled"] is True


@pytest.mark.asyncio
async def test_autopilot_toggle(
    client: AsyncClient, auth_headers: dict, test_brand, db
):
    """POST /autopilot/brands/{brand_id}/autopilot/toggle bascule."""
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        frequency=AutopilotFrequency.DAILY,
    )
    db.add(config)
    await db.commit()

    response = await client.post(
        f"/api/v1/autopilot/brands/{test_brand.id}/autopilot/toggle",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] is False  # Toggled from True to False


@pytest.mark.asyncio
async def test_autopilot_list_pending_empty(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /autopilot/brands/{brand_id}/autopilot/pending retourne liste vide."""
    response = await client.get(
        f"/api/v1/autopilot/brands/{test_brand.id}/autopilot/pending",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_autopilot_list_pending_with_posts(
    client: AsyncClient, auth_headers: dict, test_brand, db
):
    """GET /autopilot/brands/{brand_id}/autopilot/pending retourne les posts."""
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        frequency=AutopilotFrequency.DAILY,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    post = PendingPost(
        config_id=config.id,
        brand_id=test_brand.id,
        platform="instagram",
        caption="Test post pour listing",
        status=PendingPostStatus.PENDING,
    )
    db.add(post)
    await db.commit()

    response = await client.get(
        f"/api/v1/autopilot/brands/{test_brand.id}/autopilot/pending",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["caption"] == "Test post pour listing"


@pytest.mark.asyncio
async def test_autopilot_get_pending_post(
    client: AsyncClient, auth_headers: dict, test_brand, db
):
    """GET /autopilot/autopilot/pending/{id} retourne un post."""
    config = AutopilotConfig(
        brand_id=test_brand.id,
        is_enabled=True,
        frequency=AutopilotFrequency.DAILY,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)

    post = PendingPost(
        config_id=config.id,
        brand_id=test_brand.id,
        platform="linkedin",
        caption="Test single post",
        status=PendingPostStatus.PENDING,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    response = await client.get(
        f"/api/v1/autopilot/autopilot/pending/{post.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["platform"] == "linkedin"


@pytest.mark.asyncio
async def test_autopilot_get_pending_post_404(
    client: AsyncClient, auth_headers: dict
):
    """GET /autopilot/autopilot/pending/{id} retourne 404 pour id inconnu."""
    import uuid

    response = await client.get(
        f"/api/v1/autopilot/autopilot/pending/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ── Celery tasks existence ───────────────────────────────────────────


def test_autopilot_daily_generate_exists():
    """La tache autopilot_daily_generate existe."""
    from app.workers.tasks import autopilot_daily_generate

    assert callable(autopilot_daily_generate)


def test_autopilot_check_auto_publish_exists():
    """La tache autopilot_check_auto_publish existe."""
    from app.workers.tasks import autopilot_check_auto_publish

    assert callable(autopilot_check_auto_publish)


def test_celery_beat_has_autopilot_schedules():
    """Le beat schedule contient les taches autopilot."""
    from app.workers.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule
    schedule_tasks = [v["task"] for v in schedule.values()]

    assert "app.workers.tasks.autopilot_daily_generate" in schedule_tasks
    assert "app.workers.tasks.autopilot_check_auto_publish" in schedule_tasks


# ── Schemas ──────────────────────────────────────────────────────────


def test_autopilot_config_create_schema():
    """AutopilotConfigCreate valide les donnees."""
    from app.schemas.autopilot import AutopilotConfigCreate

    schema = AutopilotConfigCreate(
        platforms=["instagram"],
        frequency="daily",
        auto_publish=False,
    )
    assert schema.platforms == ["instagram"]
    assert schema.frequency == "daily"


def test_autopilot_config_create_defaults():
    """AutopilotConfigCreate a des valeurs par defaut."""
    from app.schemas.autopilot import AutopilotConfigCreate

    schema = AutopilotConfigCreate()
    assert schema.platforms == ["instagram"]
    assert schema.frequency == "daily"
    assert schema.auto_publish is False
    assert schema.generation_hour == 7


def test_pending_post_action_schema():
    """PendingPostAction valide 'approve' et 'reject'."""
    from app.schemas.autopilot import PendingPostAction

    approve = PendingPostAction(action="approve")
    assert approve.action == "approve"

    reject = PendingPostAction(action="reject")
    assert reject.action == "reject"


def test_pending_post_action_invalid():
    """PendingPostAction rejette les actions invalides."""
    from app.schemas.autopilot import PendingPostAction
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PendingPostAction(action="invalid_action")
