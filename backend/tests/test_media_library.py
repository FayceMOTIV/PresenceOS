"""Tests pour la media library et le pipeline WhatsApp-first (Sprint 9B)."""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock


# ── Model Tests ─────────────────────────────────────────────────────


def test_media_models_import():
    """Test importing media models."""
    from app.models.media import (
        MediaAsset,
        VoiceNote,
        MediaSource,
        MediaType,
    )
    assert MediaAsset.__tablename__ == "media_assets"
    assert VoiceNote.__tablename__ == "voice_notes"
    assert MediaSource.WHATSAPP.value == "whatsapp"
    assert MediaType.IMAGE.value == "image"


def test_media_source_enum():
    """Test all MediaSource values."""
    from app.models.media import MediaSource
    assert MediaSource.WHATSAPP.value == "whatsapp"
    assert MediaSource.UPLOAD.value == "upload"
    assert MediaSource.AI_GENERATED.value == "ai_generated"


def test_media_type_enum():
    """Test all MediaType values."""
    from app.models.media import MediaType
    assert MediaType.IMAGE.value == "image"
    assert MediaType.VIDEO.value == "video"


def test_models_registered_in_init():
    """Test that media models are registered in __init__."""
    from app.models import MediaAsset, VoiceNote
    assert MediaAsset is not None
    assert VoiceNote is not None


# ── Schema Tests ────────────────────────────────────────────────────


def test_media_schemas_import():
    """Test importing media schemas."""
    from app.schemas.media import (
        MediaAssetResponse,
        MediaAssetUpdate,
        VoiceNoteResponse,
        MediaLibraryStats,
    )
    assert MediaAssetResponse is not None
    assert MediaAssetUpdate is not None
    assert VoiceNoteResponse is not None
    assert MediaLibraryStats is not None


def test_media_library_stats_defaults():
    """Test MediaLibraryStats default values."""
    from app.schemas.media import MediaLibraryStats
    stats = MediaLibraryStats()
    assert stats.total_images == 0
    assert stats.total_videos == 0
    assert stats.total_voice_notes == 0
    assert stats.total_size_bytes == 0
    assert stats.from_whatsapp == 0
    assert stats.from_upload == 0
    assert stats.ai_analyzed_count == 0


def test_media_asset_update_partial():
    """Test MediaAssetUpdate with partial data."""
    from app.schemas.media import MediaAssetUpdate
    update = MediaAssetUpdate(is_archived=True)
    data = update.model_dump(exclude_unset=True)
    assert data == {"is_archived": True}
    assert "ai_description" not in data
    assert "ai_tags" not in data


# ── Vision Service Tests ────────────────────────────────────────────


def test_vision_service_import():
    """Test importing VisionService."""
    from app.services.vision import VisionService
    vs = VisionService()
    assert hasattr(vs, "analyze_image")
    assert hasattr(vs, "analyze_image_from_url")
    assert hasattr(vs, "_parse_json")


def test_vision_service_parse_json():
    """Test VisionService JSON parsing."""
    from app.services.vision import VisionService
    vs = VisionService()

    result = vs._parse_json('Some text {"key": "value"} more text')
    assert result == {"key": "value"}


def test_vision_service_parse_json_error():
    """Test VisionService JSON parsing with invalid input."""
    from app.services.vision import VisionService
    vs = VisionService()

    with pytest.raises(ValueError, match="No JSON found"):
        vs._parse_json("no json here")


# ── Transcription Service Tests ─────────────────────────────────────


def test_transcription_service_import():
    """Test importing TranscriptionService."""
    from app.services.transcription import TranscriptionService
    ts = TranscriptionService()
    assert hasattr(ts, "transcribe")
    assert hasattr(ts, "transcribe_with_timestamps")


# ── Instruction Parser Tests ────────────────────────────────────────


def test_instruction_parser_import():
    """Test importing InstructionParser."""
    from app.services.instruction_parser import InstructionParser
    parser = InstructionParser()
    assert hasattr(parser, "parse")
    assert hasattr(parser, "_default_instructions")


def test_instruction_parser_default_instructions():
    """Test default instructions fallback."""
    from app.services.instruction_parser import InstructionParser
    parser = InstructionParser()
    result = parser._default_instructions()
    assert result["platforms"] == ["instagram"]
    assert result["caption_directive"] is None
    assert result["posting_time"] is None
    assert result["is_ready_to_publish"] is False


def test_instruction_parser_default_with_caption():
    """Test default instructions with caption."""
    from app.services.instruction_parser import InstructionParser
    parser = InstructionParser()
    result = parser._default_instructions(caption_directive="Mon post du jour")
    assert result["caption_directive"] == "Mon post du jour"
    assert result["platforms"] == ["instagram"]


@pytest.mark.asyncio
async def test_instruction_parser_empty_message():
    """Test parser with empty message returns defaults."""
    from app.services.instruction_parser import InstructionParser
    parser = InstructionParser()
    result = await parser.parse("")
    assert result["platforms"] == ["instagram"]
    assert result["is_ready_to_publish"] is False


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


@pytest.mark.asyncio
async def test_whatsapp_webhook_text_message():
    """Test webhook handles text message type without crashing."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

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
                                    "text": {"body": "Publie ca sur Instagram"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhooks/whatsapp",
            json=payload,
        )
        # Should return 200 even if no brand is found (graceful handling)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_whatsapp_webhook_image_message():
    """Test webhook handles image message type without crashing."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "type": "image",
                                    "image": {
                                        "id": "test_media_id",
                                        "caption": "Mon plat du jour",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhooks/whatsapp",
            json=payload,
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_whatsapp_webhook_audio_message():
    """Test webhook handles audio message type without crashing."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "type": "audio",
                                    "audio": {"id": "test_audio_id"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/webhooks/whatsapp",
            json=payload,
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ── API Endpoint Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_media_library_assets_endpoint_unauthorized():
    """Test media library assets requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/media-library/brands/00000000-0000-0000-0000-000000000001/assets"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_media_library_voice_notes_endpoint_unauthorized():
    """Test voice notes list requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/media-library/brands/00000000-0000-0000-0000-000000000001/voice-notes"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_media_library_stats_endpoint_unauthorized():
    """Test media stats requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/media-library/brands/00000000-0000-0000-0000-000000000001/stats"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_media_library_asset_detail_unauthorized():
    """Test asset detail requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/media-library/assets/00000000-0000-0000-0000-000000000001"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_media_library_delete_asset_unauthorized():
    """Test asset deletion requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            "/api/v1/media-library/assets/00000000-0000-0000-0000-000000000001"
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_media_library_delete_voice_note_unauthorized():
    """Test voice note deletion requires auth."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            "/api/v1/media-library/voice-notes/00000000-0000-0000-0000-000000000001"
        )
        assert response.status_code == 401


# ── Router Registration Tests ──────────────────────────────────────


def test_media_library_router_registered():
    """Test that media library router is registered in API."""
    from app.api.v1.router import api_router
    route_paths = [route.path for route in api_router.routes]
    media_routes = [p for p in route_paths if "media-library" in p]
    assert len(media_routes) > 0


def test_schemas_registered_in_init():
    """Test that media schemas are registered in __init__."""
    from app.schemas import (
        MediaAssetResponse,
        MediaAssetUpdate,
        VoiceNoteResponse,
        MediaLibraryStats,
    )
    assert MediaAssetResponse is not None
    assert MediaAssetUpdate is not None
    assert VoiceNoteResponse is not None
    assert MediaLibraryStats is not None


# ── Webhook Handler Helper Tests ───────────────────────────────────


def test_webhook_image_mimes():
    """Test image MIME types are defined."""
    from app.api.webhooks.whatsapp import IMAGE_MIMES
    assert "image/jpeg" in IMAGE_MIMES
    assert "image/png" in IMAGE_MIMES
    assert "image/webp" in IMAGE_MIMES


def test_webhook_video_mimes():
    """Test video MIME types are defined."""
    from app.api.webhooks.whatsapp import VIDEO_MIMES
    assert "video/mp4" in VIDEO_MIMES
    assert "video/quicktime" in VIDEO_MIMES


def test_webhook_audio_mimes():
    """Test audio MIME types are defined."""
    from app.api.webhooks.whatsapp import AUDIO_MIMES
    assert "audio/ogg" in AUDIO_MIMES
    assert "audio/mpeg" in AUDIO_MIMES
    assert "audio/opus" in AUDIO_MIMES


# ── Storage Service Tests ──────────────────────────────────────────


def test_storage_service_has_upload_bytes():
    """Test storage service has upload_bytes method."""
    from app.services.storage import StorageService
    assert hasattr(StorageService, "upload_bytes")
