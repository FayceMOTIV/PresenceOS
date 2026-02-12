"""
PresenceOS - Tests du parcours ConversationEngine refonde (3 etats).

10 tests couvrant le flow: IDLE -> ENRICHING -> CONFIRMING -> IDLE.

Tests:
  1. Etat initial IDLE
  2. Photo -> passe a ENRICHING + message avec boutons
  3. ENRICHING + texte -> passe a CONFIRMING + preview caption
  4. ENRICHING + bouton "C'est bon" -> passe a CONFIRMING + preview caption
  5. ENRICHING + 2eme photo -> reste ENRICHING + message "Photo ajoutee"
  6. CONFIRMING + bouton "publish" -> reset IDLE
  7. CONFIRMING + bouton "cancel" -> reset IDLE
  8. CONFIRMING + texte modification -> reste CONFIRMING + nouveau preview
  9. IDLE + texte seul -> message "envoie une photo"
  10. IDLE + vocal -> message "envoie d'abord une photo"
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def _make_engine():
    """Create an engine with in-memory Redis."""
    from app.services.conversation_engine import ConversationEngine, _InMemoryRedis

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()
    return engine


def _make_mock_wa():
    """Create a mock messaging service."""
    wa = MagicMock()
    wa.send_text_message = AsyncMock(return_value="msg_1")
    wa.send_interactive_buttons = AsyncMock(return_value="msg_2")
    wa.send_media_message = AsyncMock(return_value="msg_3")
    wa.is_configured = True
    return wa


# ── Test 1: Etat initial IDLE ──────────────────────────────────────

def test_initial_state_is_idle():
    """Un nouveau contexte demarre en IDLE."""
    from app.services.conversation_engine import ConversationContext, ConversationState

    ctx = ConversationContext("33600000000", "brand-1", "config-1")
    assert ctx.state == ConversationState.IDLE
    assert ctx.media_urls == []
    assert ctx.media_analyses == []
    assert ctx.user_context == ""
    assert ctx.generated_caption == ""


# ── Test 2: Photo -> ENRICHING + boutons ─────────────────────────

@pytest.mark.asyncio
async def test_photo_moves_to_enriching():
    """Photo en IDLE -> passe a ENRICHING avec reaction + boutons."""
    from app.services.conversation_engine import ConversationState

    engine = _make_engine()
    wa = _make_mock_wa()

    # Mock _ingest_media to avoid real S3/Vision calls
    async def mock_ingest(ctx, msg_type, message):
        ctx.media_urls.append("https://s3.example.com/photo.jpg")
        ctx.media_keys.append("brands/1/photo.jpg")
        ctx.media_types.append("image")
        ctx.media_analyses.append({
            "description": "Un magnifique tajine aux legumes",
            "tags": ["food", "tajine"],
            "detected_objects": ["plate", "vegetables"],
            "mood": "warm",
        })

    # Mock _generate_photo_reaction
    async def mock_reaction(analysis, brand_name):
        return "Superbe tajine, ca a l'air delicieux ! 😍"

    # Mock _get_brand_name
    async def mock_brand_name(brand_id):
        return "Family's"

    with patch.object(engine, "_ingest_media", side_effect=mock_ingest), \
         patch.object(engine, "_generate_photo_reaction", side_effect=mock_reaction), \
         patch.object(engine, "_get_brand_name", side_effect=mock_brand_name):

        await engine.handle_message(
            sender_phone="33600000001",
            msg_type="image",
            message={"image": {"id": "photo_123", "caption": ""}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=wa,
        )

    # Should be ENRICHING now
    ctx = await engine.store.get("33600000001")
    assert ctx is not None
    assert ctx.state == ConversationState.ENRICHING
    assert len(ctx.media_urls) == 1

    # Should have sent interactive buttons
    wa.send_interactive_buttons.assert_called_once()
    call_kwargs = wa.send_interactive_buttons.call_args
    body = call_kwargs[1].get("body_text", "") if call_kwargs[1] else call_kwargs[0][1]
    assert "tajine" in body.lower() or "publie" in body.lower() or "ajouter" in body.lower()


# ── Test 3: ENRICHING + texte -> CONFIRMING + preview ────────────

@pytest.mark.asyncio
async def test_enriching_text_moves_to_confirming():
    """Texte en ENRICHING -> genere caption -> CONFIRMING + preview."""
    from app.services.conversation_engine import (
        ConversationContext, ConversationState,
    )

    engine = _make_engine()
    wa = _make_mock_wa()

    # Pre-populate ENRICHING state
    ctx = ConversationContext("33600000002", "brand-1", "config-1")
    ctx.state = ConversationState.ENRICHING
    ctx.media_urls = ["https://s3.example.com/photo.jpg"]
    ctx.media_analyses = [{"description": "Tajine", "detected_objects": [], "mood": "warm"}]
    await engine.store.save(ctx)

    # Mock _generate_and_preview
    async def mock_generate(ctx, wa):
        ctx.generated_caption = "Decouvrez notre tajine du jour a 12 euros ! 🍽️"
        ctx.state = ConversationState.CONFIRMING
        await engine.store.save(ctx)
        await wa.send_interactive_buttons(
            ctx.sender_phone,
            body_text=f"Voici ta publication :\n\"{ctx.generated_caption}\"",
            buttons=[
                {"id": "confirm_publish", "title": "Publier"},
                {"id": "confirm_edit", "title": "Modifier"},
                {"id": "confirm_cancel", "title": "Annuler"},
            ],
        )

    with patch.object(engine, "_generate_and_preview", side_effect=mock_generate):
        await engine.handle_message(
            sender_phone="33600000002",
            msg_type="text",
            message={"text": {"body": "plat du jour a 12 euros"}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=wa,
        )

    ctx = await engine.store.get("33600000002")
    assert ctx is not None
    assert ctx.state == ConversationState.CONFIRMING
    assert ctx.user_context == "plat du jour a 12 euros"
    wa.send_interactive_buttons.assert_called()


# ── Test 4: ENRICHING + bouton "C'est bon" -> CONFIRMING ─────────

@pytest.mark.asyncio
async def test_enriching_publish_button_to_confirming():
    """Bouton 'enrich_publish' en ENRICHING -> genere caption -> CONFIRMING."""
    from app.services.conversation_engine import (
        ConversationContext, ConversationState,
    )

    engine = _make_engine()
    wa = _make_mock_wa()

    # Pre-populate ENRICHING state
    ctx = ConversationContext("33600000003", "brand-1", "config-1")
    ctx.state = ConversationState.ENRICHING
    ctx.media_urls = ["https://s3.example.com/photo.jpg"]
    ctx.media_analyses = [{"description": "Tajine", "detected_objects": [], "mood": "warm"}]
    await engine.store.save(ctx)

    # Mock _generate_and_preview
    async def mock_generate(ctx, wa):
        ctx.generated_caption = "Notre tajine fait maison 🍽️"
        ctx.state = ConversationState.CONFIRMING
        await engine.store.save(ctx)
        await wa.send_interactive_buttons(
            ctx.sender_phone,
            body_text="preview",
            buttons=[{"id": "confirm_publish", "title": "Publier"}],
        )

    with patch.object(engine, "_generate_and_preview", side_effect=mock_generate):
        await engine.handle_message(
            sender_phone="33600000003",
            msg_type="interactive",
            message={"interactive": {"type": "button_reply", "button_reply": {"id": "enrich_publish"}}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=wa,
        )

    ctx = await engine.store.get("33600000003")
    assert ctx is not None
    assert ctx.state == ConversationState.CONFIRMING
    wa.send_interactive_buttons.assert_called()


# ── Test 5: ENRICHING + 2eme photo -> reste ENRICHING ────────────

@pytest.mark.asyncio
async def test_enriching_second_photo_stays_enriching():
    """2eme photo en ENRICHING -> reste ENRICHING + 'Photo ajoutee'."""
    from app.services.conversation_engine import (
        ConversationContext, ConversationState,
    )

    engine = _make_engine()
    wa = _make_mock_wa()

    # Pre-populate ENRICHING state with 1 photo
    ctx = ConversationContext("33600000004", "brand-1", "config-1")
    ctx.state = ConversationState.ENRICHING
    ctx.media_urls = ["https://s3.example.com/photo1.jpg"]
    ctx.media_analyses = [{"description": "Photo 1"}]
    await engine.store.save(ctx)

    # Mock _ingest_media
    async def mock_ingest(ctx, msg_type, message):
        ctx.media_urls.append("https://s3.example.com/photo2.jpg")
        ctx.media_keys.append("brands/1/photo2.jpg")
        ctx.media_types.append("image")
        ctx.media_analyses.append({"description": "Photo 2"})

    with patch.object(engine, "_ingest_media", side_effect=mock_ingest):
        await engine.handle_message(
            sender_phone="33600000004",
            msg_type="image",
            message={"image": {"id": "photo_456"}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=wa,
        )

    ctx = await engine.store.get("33600000004")
    assert ctx is not None
    assert ctx.state == ConversationState.ENRICHING
    assert len(ctx.media_urls) == 2

    # Should show "Photo ajoutee" with buttons
    wa.send_interactive_buttons.assert_called_once()
    body = wa.send_interactive_buttons.call_args[1].get("body_text", "") \
        if wa.send_interactive_buttons.call_args[1] \
        else wa.send_interactive_buttons.call_args[0][1]
    assert "ajoutee" in body.lower() or "2 photo" in body.lower()


# ── Test 6: CONFIRMING + bouton "publish" -> reset IDLE ──────────

@pytest.mark.asyncio
async def test_confirming_publish_resets_idle():
    """Bouton 'confirm_publish' en CONFIRMING -> publie -> IDLE (context deleted)."""
    from app.services.conversation_engine import (
        ConversationContext, ConversationState,
    )

    engine = _make_engine()
    wa = _make_mock_wa()

    # Pre-populate CONFIRMING state
    ctx = ConversationContext("33600000005", "brand-1", "config-1")
    ctx.state = ConversationState.CONFIRMING
    ctx.generated_caption = "Notre tajine fait maison"
    ctx.platforms = ["instagram"]
    ctx.media_urls = ["https://s3.example.com/photo.jpg"]
    await engine.store.save(ctx)

    # Mock DB session for _publish_posts
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.database.async_session_maker", return_value=mock_session):
        await engine.handle_message(
            sender_phone="33600000005",
            msg_type="interactive",
            message={"interactive": {"type": "button_reply", "button_reply": {"id": "confirm_publish"}}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=wa,
        )

    # Context should be deleted (back to IDLE)
    final_ctx = await engine.store.get("33600000005")
    assert final_ctx is None

    # Should have sent a success message
    wa.send_text_message.assert_called()
    call_text = wa.send_text_message.call_args[0][1]
    assert "publie" in call_text.lower() or "✅" in call_text


# ── Test 7: CONFIRMING + bouton "cancel" -> reset IDLE ───────────

@pytest.mark.asyncio
async def test_confirming_cancel_resets_idle():
    """Bouton 'confirm_cancel' en CONFIRMING -> annule -> IDLE."""
    from app.services.conversation_engine import (
        ConversationContext, ConversationState,
    )

    engine = _make_engine()
    wa = _make_mock_wa()

    # Pre-populate CONFIRMING state
    ctx = ConversationContext("33600000006", "brand-1", "config-1")
    ctx.state = ConversationState.CONFIRMING
    ctx.generated_caption = "Publication test"
    await engine.store.save(ctx)

    await engine.handle_message(
        sender_phone="33600000006",
        msg_type="interactive",
        message={"interactive": {"type": "button_reply", "button_reply": {"id": "confirm_cancel"}}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=wa,
    )

    # Context should be deleted
    final_ctx = await engine.store.get("33600000006")
    assert final_ctx is None

    # Should have sent cancellation message
    wa.send_text_message.assert_called()
    call_text = wa.send_text_message.call_args[0][1]
    assert "annule" in call_text.lower() or "photo" in call_text.lower()


# ── Test 8: CONFIRMING + texte modification -> reste CONFIRMING ──

@pytest.mark.asyncio
async def test_confirming_text_regenerates_caption():
    """Texte en CONFIRMING -> regenere caption -> reste CONFIRMING."""
    from app.services.conversation_engine import (
        ConversationContext, ConversationState,
    )

    engine = _make_engine()
    wa = _make_mock_wa()

    # Pre-populate CONFIRMING state
    ctx = ConversationContext("33600000007", "brand-1", "config-1")
    ctx.state = ConversationState.CONFIRMING
    ctx.generated_caption = "Version originale"
    ctx.platforms = ["instagram"]
    ctx.media_urls = ["https://s3.example.com/photo.jpg"]
    await engine.store.save(ctx)

    # Mock _regenerate_caption
    async def mock_regen(ctx, instruction, wa):
        ctx.generated_caption = "Version modifiee sans hashtags"
        await engine.store.save(ctx)
        await wa.send_interactive_buttons(
            ctx.sender_phone,
            body_text=f"Nouvelle version :\n\"{ctx.generated_caption}\"",
            buttons=[
                {"id": "confirm_publish", "title": "Publier"},
                {"id": "confirm_edit", "title": "Modifier"},
                {"id": "confirm_cancel", "title": "Annuler"},
            ],
        )

    with patch.object(engine, "_regenerate_caption", side_effect=mock_regen):
        await engine.handle_message(
            sender_phone="33600000007",
            msg_type="text",
            message={"text": {"body": "enleve les hashtags"}},
            brand_id="brand-1",
            config_id="config-1",
            messaging_service=wa,
        )

    ctx = await engine.store.get("33600000007")
    assert ctx is not None
    assert ctx.state == ConversationState.CONFIRMING
    assert ctx.generated_caption == "Version modifiee sans hashtags"
    wa.send_interactive_buttons.assert_called()


# ── Test 9: IDLE + texte seul -> message "envoie une photo" ──────

@pytest.mark.asyncio
async def test_idle_text_asks_for_photo():
    """Texte seul en IDLE -> demande une photo."""
    engine = _make_engine()
    wa = _make_mock_wa()

    await engine.handle_message(
        sender_phone="33600000008",
        msg_type="text",
        message={"text": {"body": "Je veux publier quelque chose"}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=wa,
    )

    wa.send_text_message.assert_called_once()
    call_text = wa.send_text_message.call_args[0][1]
    assert "photo" in call_text.lower()


# ── Test 10: IDLE + vocal -> message "envoie d'abord une photo" ──

@pytest.mark.asyncio
async def test_idle_audio_asks_for_photo():
    """Vocal en IDLE -> demande d'abord une photo."""
    engine = _make_engine()
    wa = _make_mock_wa()

    await engine.handle_message(
        sender_phone="33600000009",
        msg_type="audio",
        message={"audio": {"id": "voice_123"}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=wa,
    )

    wa.send_text_message.assert_called_once()
    call_text = wa.send_text_message.call_args[0][1]
    assert "photo" in call_text.lower()
