"""Tests pour Sprint 9C: Moteur conversationnel WhatsApp + Pipeline video."""
import pytest
import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock


# ══════════════════════════════════════════════════════════════════════
# Section A: ConversationEngine Tests
# ══════════════════════════════════════════════════════════════════════


def test_conversation_state_enum():
    """Test all ConversationState values (3 states: IDLE, ENRICHING, CONFIRMING)."""
    from app.services.conversation_engine import ConversationState
    assert ConversationState.IDLE.value == "idle"
    assert ConversationState.ENRICHING.value == "enriching"
    assert ConversationState.CONFIRMING.value == "confirming"
    assert len(ConversationState) == 3


def test_conversation_context_creation():
    """Test creating a ConversationContext."""
    from app.services.conversation_engine import ConversationContext, ConversationState
    ctx = ConversationContext(
        sender_phone="33612345678",
        brand_id="test-brand-id",
        config_id="test-config-id",
    )
    assert ctx.sender_phone == "33612345678"
    assert ctx.brand_id == "test-brand-id"
    assert ctx.config_id == "test-config-id"
    assert ctx.state == ConversationState.IDLE
    assert ctx.media_urls == []
    assert ctx.media_analyses == []
    assert ctx.user_context == ""
    assert ctx.generated_caption == ""
    assert ctx.platforms == ["instagram"]


def test_conversation_context_serialization():
    """Test ConversationContext round-trip serialization."""
    from app.services.conversation_engine import ConversationContext, ConversationState
    ctx = ConversationContext(
        sender_phone="33612345678",
        brand_id="brand-123",
        config_id="config-456",
    )
    ctx.state = ConversationState.ENRICHING
    ctx.media_urls = ["https://example.com/img.jpg"]
    ctx.media_keys = ["brands/123/media/img.jpg"]
    ctx.media_types = ["image"]
    ctx.media_analyses = [{"description": "Un plat", "tags": ["food"]}]
    ctx.user_context = "Plat du jour a 12 euros"
    ctx.generated_caption = "Mon plat du jour"
    ctx.platforms = ["instagram", "tiktok"]

    # Serialize
    data = ctx.to_dict()
    assert data["state"] == "enriching"
    assert data["sender_phone"] == "33612345678"
    assert data["generated_caption"] == "Mon plat du jour"
    assert data["user_context"] == "Plat du jour a 12 euros"
    assert data["media_analyses"] == [{"description": "Un plat", "tags": ["food"]}]

    # Deserialize
    ctx2 = ConversationContext.from_dict(data)
    assert ctx2.state == ConversationState.ENRICHING
    assert ctx2.media_urls == ["https://example.com/img.jpg"]
    assert ctx2.platforms == ["instagram", "tiktok"]
    assert ctx2.generated_caption == "Mon plat du jour"
    assert ctx2.user_context == "Plat du jour a 12 euros"
    assert ctx2.media_analyses == [{"description": "Un plat", "tags": ["food"]}]


def test_conversation_context_touch():
    """Test touch updates timestamp and message count."""
    from app.services.conversation_engine import ConversationContext
    ctx = ConversationContext("phone", "brand", "config")
    assert ctx.message_count == 0
    ctx.touch()
    assert ctx.message_count == 1
    ctx.touch()
    assert ctx.message_count == 2


@pytest.mark.asyncio
async def test_conversation_store_in_memory():
    """Test ConversationStore with in-memory fallback."""
    from app.services.conversation_engine import ConversationStore, ConversationContext, ConversationState

    store = ConversationStore()
    # Force in-memory backend
    from app.services.conversation_engine import _InMemoryRedis
    store._redis = _InMemoryRedis()

    # Initially empty
    ctx = await store.get("33612345678")
    assert ctx is None

    # Save
    new_ctx = ConversationContext("33612345678", "brand-1", "config-1")
    new_ctx.state = ConversationState.ENRICHING
    await store.save(new_ctx)

    # Retrieve
    loaded = await store.get("33612345678")
    assert loaded is not None
    assert loaded.state == ConversationState.ENRICHING
    assert loaded.brand_id == "brand-1"

    # Delete
    await store.delete("33612345678")
    assert await store.get("33612345678") is None


def test_conversation_engine_import():
    """Test importing ConversationEngine."""
    from app.services.conversation_engine import ConversationEngine
    engine = ConversationEngine()
    assert hasattr(engine, "handle_message")
    assert hasattr(engine, "store")


def test_conversation_engine_parse_platforms():
    """Test platform parsing from text."""
    from app.services.conversation_engine import ConversationEngine
    engine = ConversationEngine()

    assert engine._parse_platforms("instagram") == ["instagram"]
    assert engine._parse_platforms("insta") == ["instagram"]
    assert "tiktok" in engine._parse_platforms("tiktok et instagram")
    assert "instagram" in engine._parse_platforms("tiktok et instagram")
    assert engine._parse_platforms("toutes les plateformes") == ["instagram", "tiktok", "linkedin"]
    assert engine._parse_platforms("all") == ["instagram", "tiktok", "linkedin"]
    assert engine._parse_platforms("random text") == ["instagram"]  # default


@pytest.mark.asyncio
async def test_conversation_engine_cancel_command():
    """Test that 'annuler' resets conversation."""
    from app.services.conversation_engine import ConversationEngine, _InMemoryRedis

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()

    mock_wa = MagicMock()
    mock_wa.send_text_message = AsyncMock(return_value="wamid_123")

    await engine.handle_message(
        sender_phone="33612345678",
        msg_type="text",
        message={"text": {"body": "annuler"}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=mock_wa,
    )

    mock_wa.send_text_message.assert_called_once()
    call_args = mock_wa.send_text_message.call_args
    assert "annule" in call_args[0][1].lower() or "photo" in call_args[0][1].lower()


@pytest.mark.asyncio
async def test_conversation_engine_help_command():
    """Test that 'aide' sends help message."""
    from app.services.conversation_engine import ConversationEngine, _InMemoryRedis

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()

    mock_wa = MagicMock()
    mock_wa.send_text_message = AsyncMock(return_value="wamid_123")

    await engine.handle_message(
        sender_phone="33612345678",
        msg_type="text",
        message={"text": {"body": "aide"}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=mock_wa,
    )

    mock_wa.send_text_message.assert_called_once()
    call_args = mock_wa.send_text_message.call_args
    assert "PresenceOS" in str(call_args) or "photo" in call_args[0][1].lower()


@pytest.mark.asyncio
async def test_conversation_engine_text_in_idle_asks_photo():
    """Test that text message in IDLE state asks for a photo."""
    from app.services.conversation_engine import ConversationEngine, _InMemoryRedis

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()

    mock_wa = MagicMock()
    mock_wa.send_text_message = AsyncMock(return_value="wamid_1")
    mock_wa.send_interactive_buttons = AsyncMock(return_value="wamid_2")

    await engine.handle_message(
        sender_phone="33612345678",
        msg_type="text",
        message={"text": {"body": "Publie mon plat du jour"}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=mock_wa,
    )

    # Text in IDLE should ask for a photo, not start platform selection
    mock_wa.send_text_message.assert_called_once()
    call_args = mock_wa.send_text_message.call_args[0][1]
    assert "photo" in call_args.lower()


@pytest.mark.asyncio
async def test_conversation_engine_confirm_publish_button():
    """Test confirming publish via button creates posts."""
    from app.services.conversation_engine import (
        ConversationEngine, ConversationContext, ConversationState, _InMemoryRedis,
    )

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()

    # Pre-populate context in CONFIRMING state
    ctx = ConversationContext("33612345678", "brand-1", "config-1")
    ctx.state = ConversationState.CONFIRMING
    ctx.generated_caption = "Mon plat du jour est magnifique"
    ctx.platforms = ["instagram"]
    ctx.media_urls = ["https://example.com/img.jpg"]
    await engine.store.save(ctx)

    mock_wa = MagicMock()
    mock_wa.send_text_message = AsyncMock(return_value="wamid_1")

    # Mock DB session
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.database.async_session_maker", return_value=mock_session):

        await engine.handle_message(
            sender_phone="33612345678",
            msg_type="interactive",
            message={"interactive": {"type": "button_reply", "button_reply": {"id": "confirm_publish"}}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=mock_wa,
        )

        # Should send confirmation and clear context
        mock_wa.send_text_message.assert_called()
        call_text = mock_wa.send_text_message.call_args[0][1]
        assert "publie" in call_text.lower() or "✅" in call_text
        # Context should be deleted after publish
        final_ctx = await engine.store.get("33612345678")
        assert final_ctx is None


# ══════════════════════════════════════════════════════════════════════
# Section B: Video Pipeline Tests
# ══════════════════════════════════════════════════════════════════════


def test_pexels_service_import():
    """Test importing PexelsService."""
    from app.services.pexels import PexelsService
    ps = PexelsService()
    assert hasattr(ps, "search_videos")
    assert hasattr(ps, "search_photos")
    assert hasattr(ps, "download_video")


def test_pexels_pick_best_file():
    """Test picking the best video file."""
    from app.services.pexels import PexelsService
    ps = PexelsService()

    files = [
        {"file_type": "video/mp4", "width": 640, "height": 360, "link": "low.mp4"},
        {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "hd.mp4"},
        {"file_type": "video/mp4", "width": 3840, "height": 2160, "link": "4k.mp4"},
    ]
    best = ps._pick_best_file(files)
    assert best["link"] == "hd.mp4"  # Closest to 1920 height


def test_pexels_pick_best_file_empty():
    """Test picking file from empty list."""
    from app.services.pexels import PexelsService
    ps = PexelsService()
    assert ps._pick_best_file([]) is None


def test_tts_service_import():
    """Test importing TTSService."""
    from app.services.tts import TTSService
    tts = TTSService()
    assert hasattr(tts, "generate_speech")
    assert hasattr(tts, "generate_speech_for_caption")


def test_tts_clean_for_speech():
    """Test cleaning text for speech synthesis."""
    from app.services.tts import TTSService
    tts = TTSService()

    text = "Check out #food #restaurant @chefmike https://example.com"
    clean = tts._clean_for_speech(text)
    assert "#" not in clean
    assert "@" not in clean
    assert "https://" not in clean
    assert "Check out" in clean


def test_tts_clean_for_speech_empty():
    """Test cleaning empty text."""
    from app.services.tts import TTSService
    tts = TTSService()
    assert tts._clean_for_speech("") == ""


def test_music_library_import():
    """Test importing MusicLibrary."""
    from app.services.music_library import MusicLibrary
    ml = MusicLibrary()
    assert hasattr(ml, "get_track")
    assert hasattr(ml, "suggest_mood")
    assert hasattr(ml, "list_moods")


def test_music_library_suggest_mood():
    """Test mood suggestion from tags."""
    from app.services.music_library import MusicLibrary
    ml = MusicLibrary()

    assert ml.suggest_mood(["fitness", "gym", "sport"]) == "energetic"
    assert ml.suggest_mood(["relax", "calm", "coffee"]) == "chill"
    assert ml.suggest_mood(["business", "corporate"]) == "corporate"
    assert ml.suggest_mood(["trend", "viral", "tiktok"]) == "trendy"
    assert ml.suggest_mood(["random", "nothing"]) == "chill"  # default


def test_music_library_list_moods():
    """Test listing moods."""
    from app.services.music_library import MusicLibrary
    ml = MusicLibrary()
    moods = ml.list_moods()
    assert len(moods) == 8
    mood_names = [m["mood"] for m in moods]
    assert "energetic" in mood_names
    assert "chill" in mood_names
    assert "trendy" in mood_names


def test_music_library_get_track_no_files():
    """Test getting track when no files exist."""
    from app.services.music_library import MusicLibrary
    ml = MusicLibrary()
    ml._tracks_cache = {"energetic": [], "chill": [], "inspiring": [], "dramatic": [],
                        "happy": [], "corporate": [], "ambient": [], "trendy": []}
    assert ml.get_track("chill") is None


def test_ffmpeg_processor_import():
    """Test importing FFmpegProcessor."""
    from app.services.ffmpeg_processor import FFmpegProcessor
    fp = FFmpegProcessor()
    assert hasattr(fp, "image_to_video")
    assert hasattr(fp, "concatenate_clips")
    assert hasattr(fp, "add_audio")
    assert hasattr(fp, "mix_audio_tracks")
    assert hasattr(fp, "add_text_overlay")
    assert hasattr(fp, "format_for_reel")


def test_ffmpeg_processor_temp_path():
    """Test temp path generation."""
    from app.services.ffmpeg_processor import FFmpegProcessor
    fp = FFmpegProcessor()
    path = fp._temp_path("mp4")
    assert path.endswith(".mp4")


def test_video_producer_import():
    """Test importing VideoProducer."""
    from app.services.video_producer import VideoProducer
    vp = VideoProducer()
    assert hasattr(vp, "produce")
    assert hasattr(vp, "pexels")
    assert hasattr(vp, "tts")
    assert hasattr(vp, "music")
    assert hasattr(vp, "ffmpeg")


# ══════════════════════════════════════════════════════════════════════
# Section C: Celery Task Tests
# ══════════════════════════════════════════════════════════════════════


def test_generate_whatsapp_content_task_exists():
    """Test that the generate_whatsapp_content task is registered."""
    from app.workers.tasks import generate_whatsapp_content
    assert callable(generate_whatsapp_content)


# ══════════════════════════════════════════════════════════════════════
# Section D: WhatsApp Service Extensions Tests
# ══════════════════════════════════════════════════════════════════════


def test_whatsapp_service_has_interactive_buttons():
    """Test WhatsAppService has send_interactive_buttons method."""
    from app.services.whatsapp import WhatsAppService
    wa = WhatsAppService()
    assert hasattr(wa, "send_interactive_buttons")


def test_whatsapp_service_has_media_message():
    """Test WhatsAppService has send_media_message method."""
    from app.services.whatsapp import WhatsAppService
    wa = WhatsAppService()
    assert hasattr(wa, "send_media_message")


def test_whatsapp_service_has_reaction():
    """Test WhatsAppService has send_reaction method."""
    from app.services.whatsapp import WhatsAppService
    wa = WhatsAppService()
    assert hasattr(wa, "send_reaction")


# ══════════════════════════════════════════════════════════════════════
# Section E: Webhook + ConversationEngine Integration Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_webhook_still_verifies():
    """Test WhatsApp webhook verification still works after 9C refactor."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "99999",
                "hub.verify_token": "presenceos-webhook-verify",
            },
        )
        assert response.status_code == 200
        assert response.json() == 99999


@pytest.mark.asyncio
async def test_webhook_post_empty_still_works():
    """Test empty webhook payload returns 200 after 9C refactor."""
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
async def test_webhook_routes_through_engine():
    """Test that webhook POST routes messages through ConversationEngine."""
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
                                    "text": {"body": "test message"},
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
        # Should return 200 even without brand configured
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_image_through_engine():
    """Test image message flows through engine."""
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
                                        "caption": "Mon plat",
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


# ══════════════════════════════════════════════════════════════════════
# Section F: Config Tests
# ══════════════════════════════════════════════════════════════════════


def test_config_has_video_pipeline_settings():
    """Test that config has Sprint 9C video pipeline settings."""
    from app.core.config import Settings
    # Check the field exists on the class
    fields = Settings.model_fields
    assert "pexels_api_key" in fields
    assert "openai_tts_voice" in fields
    assert "openai_tts_model" in fields
    assert "music_library_path" in fields
    assert "ffmpeg_path" in fields
    assert "video_output_path" in fields
    assert "video_max_duration" in fields


def test_config_has_conversation_settings():
    """Test that config has Sprint 9C conversation settings."""
    from app.core.config import Settings
    fields = Settings.model_fields
    assert "conversation_ttl_seconds" in fields


def test_config_default_values():
    """Test Sprint 9C config defaults."""
    from app.core.config import settings
    assert settings.openai_tts_voice == "nova"
    assert settings.openai_tts_model == "tts-1"
    assert settings.video_max_duration == 60
    assert settings.conversation_ttl_seconds == 1800


# ══════════════════════════════════════════════════════════════════════
# Section G: Music Library Setup Script Tests
# ══════════════════════════════════════════════════════════════════════


def test_music_setup_script_exists():
    """Test that the music library setup script exists."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "scripts",
        "setup_music_library.sh",
    )
    assert os.path.exists(script_path)


def test_music_setup_script_executable():
    """Test that the script is executable."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "scripts",
        "setup_music_library.sh",
    )
    assert os.access(script_path, os.X_OK)


# ══════════════════════════════════════════════════════════════════════
# Webhook MIME Constants Tests (still valid after 9C)
# ══════════════════════════════════════════════════════════════════════


def test_webhook_mimes_still_defined():
    """Test MIME types still defined after 9C refactor."""
    from app.api.webhooks.whatsapp import IMAGE_MIMES, VIDEO_MIMES, AUDIO_MIMES
    assert "image/jpeg" in IMAGE_MIMES
    assert "video/mp4" in VIDEO_MIMES
    assert "audio/ogg" in AUDIO_MIMES
