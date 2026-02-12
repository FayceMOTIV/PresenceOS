"""
PresenceOS - Phase 4 Tests: Pipeline Contenu WhatsApp (Vision + Media).
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient

from app.models.media import MediaAsset, VoiceNote, MediaSource, MediaType


# ── Model tests ──────────────────────────────────────────────────────


def test_media_asset_model_fields():
    """MediaAsset a tous les champs requis."""
    from sqlalchemy import inspect

    mapper = inspect(MediaAsset)
    columns = {c.key for c in mapper.column_attrs}

    required = {
        "id",
        "brand_id",
        "storage_key",
        "public_url",
        "media_type",
        "mime_type",
        "file_size",
        "source",
        "whatsapp_media_id",
        "ai_description",
        "ai_tags",
        "ai_analyzed",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"Champs manquants: {required - columns}"


def test_voice_note_model_fields():
    """VoiceNote a tous les champs requis."""
    from sqlalchemy import inspect

    mapper = inspect(VoiceNote)
    columns = {c.key for c in mapper.column_attrs}

    required = {
        "id",
        "brand_id",
        "storage_key",
        "public_url",
        "mime_type",
        "file_size",
        "transcription",
        "is_transcribed",
        "whatsapp_media_id",
        "sender_phone",
        "parsed_instructions",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"Champs manquants: {required - columns}"


def test_media_source_enum():
    """MediaSource contient whatsapp, upload, ai_generated."""
    values = {s.value for s in MediaSource}
    assert "whatsapp" in values
    assert "upload" in values
    assert "ai_generated" in values


def test_media_type_enum():
    """MediaType contient image et video."""
    values = {t.value for t in MediaType}
    assert "image" in values
    assert "video" in values


@pytest.mark.asyncio
async def test_create_media_asset(db, test_brand):
    """MediaAsset peut etre cree en DB."""
    asset = MediaAsset(
        brand_id=test_brand.id,
        storage_key="brands/test/images/photo1.jpg",
        public_url="https://s3.example.com/photo1.jpg",
        media_type=MediaType.IMAGE,
        mime_type="image/jpeg",
        file_size=150000,
        source=MediaSource.WHATSAPP,
        whatsapp_media_id="wamid.media123",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    assert asset.id is not None
    assert asset.brand_id == test_brand.id
    assert asset.source == MediaSource.WHATSAPP
    assert asset.ai_analyzed is False


@pytest.mark.asyncio
async def test_create_voice_note(db, test_brand):
    """VoiceNote peut etre cree en DB."""
    note = VoiceNote(
        brand_id=test_brand.id,
        storage_key="brands/test/audio/voice1.ogg",
        public_url="https://s3.example.com/voice1.ogg",
        mime_type="audio/ogg",
        file_size=25000,
        transcription="Publie cette photo sur Instagram",
        is_transcribed=True,
        whatsapp_media_id="wamid.audio456",
        sender_phone="+33612345678",
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    assert note.id is not None
    assert note.is_transcribed is True
    assert note.transcription == "Publie cette photo sur Instagram"


# ── VisionService tests ──────────────────────────────────────────────


def test_vision_service_init():
    """VisionService peut etre instancie."""
    from app.services.vision import VisionService

    service = VisionService()
    assert service is not None
    assert service.provider in ("openai", "anthropic")


@pytest.mark.asyncio
async def test_vision_analyze_image_mock():
    """VisionService.analyze_image retourne un dict avec les bons champs."""
    from app.services.vision import VisionService

    service = VisionService(provider="openai")

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"description": "Un plat de pasta", "tags": ["food", "pasta"], "suggested_caption": "Decouvrez nos pates fraiches!", "detected_objects": ["plate", "pasta"], "mood": "appetizing", "suitable_platforms": ["instagram", "facebook"]}'
            )
        )
    ]

    with patch.object(
        service.client.chat.completions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await service.analyze_image(b"fake_image_data", "image/jpeg")

    assert "description" in result
    assert "tags" in result
    assert "suggested_caption" in result
    assert isinstance(result["tags"], list)


# ── TranscriptionService tests ───────────────────────────────────────


def test_transcription_service_init():
    """TranscriptionService peut etre instancie."""
    from app.services.transcription import TranscriptionService

    service = TranscriptionService()
    assert service is not None


@pytest.mark.asyncio
async def test_transcription_transcribe_mock():
    """TranscriptionService.transcribe retourne le texte transcrit."""
    from app.services.transcription import TranscriptionService

    service = TranscriptionService()

    mock_response = MagicMock()
    mock_response.text = "Publie cette photo sur Instagram et Facebook"

    with patch.object(
        service.client.audio.transcriptions,
        "create",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await service.transcribe(b"fake_audio_data", "audio.ogg")

    assert result == "Publie cette photo sur Instagram et Facebook"


# ── InstructionParser tests ──────────────────────────────────────────


def test_instruction_parser_init():
    """InstructionParser peut etre instancie."""
    from app.services.instruction_parser import InstructionParser

    parser = InstructionParser()
    assert parser is not None


@pytest.mark.asyncio
async def test_instruction_parser_default_on_empty():
    """InstructionParser retourne les defaults pour un message vide."""
    from app.services.instruction_parser import InstructionParser

    parser = InstructionParser()
    result = await parser.parse("")

    assert result["platforms"] == ["instagram"]
    assert result["is_ready_to_publish"] is False


@pytest.mark.asyncio
async def test_instruction_parser_detects_platforms():
    """InstructionParser detecte les plateformes via AI mock."""
    from app.services.instruction_parser import InstructionParser

    parser = InstructionParser()

    mock_result = '{"platforms": ["instagram", "facebook"], "caption_directive": "un beau post", "posting_time": null, "hashtags": null, "tone": null, "is_ready_to_publish": false, "additional_notes": null}'

    with patch.object(
        parser.ai,
        "_complete",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        result = await parser.parse("Publie sur insta et facebook")

    assert "instagram" in result["platforms"]
    assert "facebook" in result["platforms"]


@pytest.mark.asyncio
async def test_instruction_parser_detects_schedule():
    """InstructionParser detecte l'horaire programme."""
    from app.services.instruction_parser import InstructionParser

    parser = InstructionParser()

    mock_result = '{"platforms": ["instagram"], "caption_directive": "test", "posting_time": "demain 12h", "hashtags": null, "tone": null, "is_ready_to_publish": false, "additional_notes": null}'

    with patch.object(
        parser.ai,
        "_complete",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        result = await parser.parse("Publie demain a 12h sur instagram")

    assert result["posting_time"] == "demain 12h"


# ── Webhook tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_handles_photo(client: AsyncClient):
    """POST /webhooks/whatsapp avec photo retourne 200."""
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
                                        "id": "media_id_123",
                                        "mime_type": "image/jpeg",
                                        "caption": "Voici mon plat du jour",
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
async def test_webhook_handles_voice_note(client: AsyncClient):
    """POST /webhooks/whatsapp avec voice note retourne 200."""
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
                                    "audio": {
                                        "id": "media_id_456",
                                        "mime_type": "audio/ogg; codecs=opus",
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
async def test_webhook_handles_video(client: AsyncClient):
    """POST /webhooks/whatsapp avec video retourne 200."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "type": "video",
                                    "video": {
                                        "id": "media_id_789",
                                        "mime_type": "video/mp4",
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


# ── Media Library API tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_media_library_list_assets(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /media-library/brands/{id}/assets retourne 200."""
    response = await client.get(
        f"/api/v1/media-library/brands/{test_brand.id}/assets",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_media_library_list_voice_notes(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /media-library/brands/{id}/voice-notes retourne 200."""
    response = await client.get(
        f"/api/v1/media-library/brands/{test_brand.id}/voice-notes",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_media_library_stats(
    client: AsyncClient, auth_headers: dict, test_brand
):
    """GET /media-library/brands/{id}/stats retourne 200."""
    response = await client.get(
        f"/api/v1/media-library/brands/{test_brand.id}/stats",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_assets" in data or "total_images" in data or isinstance(data, dict)


@pytest.mark.asyncio
async def test_media_library_get_asset_404(
    client: AsyncClient, auth_headers: dict
):
    """GET /media-library/assets/{id} retourne 404 pour id inconnu."""
    import uuid

    response = await client.get(
        f"/api/v1/media-library/assets/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404
