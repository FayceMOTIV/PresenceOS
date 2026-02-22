"""
PresenceOS - Tests for Community Manager AI Agent

30+ tests covering classification, response generation, system prompt building,
auto-publish thresholds, crisis detection, and niche-specific behavior.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

from app.services.cm_agent import (
    CMAgent,
    CRISIS_KEYWORDS,
    NICHE_TONE_GUIDE,
    DEFAULT_NICHE_TONE,
)
from app.models.cm_interaction import CMInteraction


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_brand(
    name="Le Family's",
    brand_type="restaurant",
    description="Bistrot familial parisien",
    locations=None,
    voice=None,
    knowledge_items=None,
    constraints=None,
):
    """Build a mock Brand object matching the real SQLAlchemy model."""
    brand = MagicMock()
    brand.name = name
    brand.brand_type = MagicMock()
    brand.brand_type.value = brand_type
    brand.description = description
    brand.locations = locations or ["Paris 11e"]
    brand.constraints = constraints
    brand.content_pillars = None
    brand.voice = voice
    brand.knowledge_items = knowledge_items or []
    return brand


def _make_voice(
    tone_formal=30,
    tone_playful=75,
    tone_bold=40,
    primary_language="fr",
    words_to_avoid=None,
    words_to_prefer=None,
    example_phrases=None,
    emojis_allowed=True,
    max_emojis_per_post=2,
    custom_instructions=None,
):
    voice = MagicMock()
    voice.tone_formal = tone_formal
    voice.tone_playful = tone_playful
    voice.tone_bold = tone_bold
    voice.tone_technical = 20
    voice.tone_emotional = 70
    voice.primary_language = primary_language
    voice.words_to_avoid = words_to_avoid or ["cheap", "discount"]
    voice.words_to_prefer = words_to_prefer or ["maison", "artisanal"]
    voice.example_phrases = example_phrases or ["Bienvenue chez nous !"]
    voice.emojis_allowed = emojis_allowed
    voice.max_emojis_per_post = max_emojis_per_post
    voice.hashtag_style = "mixed"
    voice.allow_english_terms = True
    voice.custom_instructions = custom_instructions
    return voice


def _make_interaction(
    content="Super restaurant, on a adoré !",
    rating=5,
    classification="positive",
    platform="google",
    interaction_type="review",
    commenter_name="Jean Dupont",
):
    interaction = MagicMock(spec=CMInteraction)
    interaction.id = uuid4()
    interaction.brand_id = uuid4()
    interaction.platform = platform
    interaction.interaction_type = interaction_type
    interaction.external_id = f"google_{uuid4().hex[:8]}"
    interaction.commenter_name = commenter_name
    interaction.content = content
    interaction.rating = rating
    interaction.classification = classification
    interaction.sentiment_score = 0.9 if rating and rating >= 4 else 0.2
    interaction.confidence_score = 0.85
    return interaction


def _mock_claude_response(content_dict):
    """Build a mock Anthropic message response."""
    block = MagicMock()
    block.text = json.dumps(content_dict, ensure_ascii=False)
    msg = MagicMock()
    msg.content = [block]
    return msg


# ── System Prompt Tests ──────────────────────────────────────────────────────


class TestBuildSystemPrompt:
    """Tests for dynamic system prompt generation."""

    def test_system_prompt_contains_business_name(self):
        brand = _make_brand(name="Le Family's")
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "Le Family's" in prompt

    def test_system_prompt_contains_niche(self):
        brand = _make_brand(brand_type="restaurant")
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "restaurant" in prompt

    def test_system_prompt_contains_description(self):
        brand = _make_brand(description="Meilleur couscous de Paris")
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "Meilleur couscous de Paris" in prompt

    def test_system_prompt_contains_locations(self):
        brand = _make_brand(locations=["Paris 11e", "Lyon 6e"])
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "Paris 11e" in prompt
        assert "Lyon 6e" in prompt

    def test_system_prompt_language_french(self):
        voice = _make_voice(primary_language="fr")
        brand = _make_brand(voice=voice)
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "français" in prompt

    def test_system_prompt_language_english(self):
        voice = _make_voice(primary_language="en")
        brand = _make_brand(voice=voice)
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "anglais" in prompt

    def test_system_prompt_contains_voice_words_to_avoid(self):
        voice = _make_voice(words_to_avoid=["cheap", "boring"])
        brand = _make_brand(voice=voice)
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "cheap" in prompt
        assert "boring" in prompt

    def test_system_prompt_contains_voice_words_to_prefer(self):
        voice = _make_voice(words_to_prefer=["artisanal", "maison"])
        brand = _make_brand(voice=voice)
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "artisanal" in prompt

    def test_system_prompt_contains_rules(self):
        brand = _make_brand()
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "JAMAIS mentionner" in prompt
        assert "Maximum 3 phrases" in prompt
        assert "JSON" in prompt

    def test_system_prompt_contains_auto_publish_threshold(self):
        brand = _make_brand()
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "0.85" in prompt

    def test_system_prompt_no_voice_still_works(self):
        brand = _make_brand(voice=None)
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "Le Family's" in prompt
        # Should not crash without voice

    def test_system_prompt_contains_knowledge_items(self):
        ki = MagicMock()
        ki.is_active = True
        ki.knowledge_type = MagicMock()
        ki.knowledge_type.value = "faq"
        ki.title = "Horaires"
        ki.content = "Ouvert du mardi au dimanche, 12h-14h30 et 19h-23h"

        brand = _make_brand(knowledge_items=[ki])
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "Horaires" in prompt
        assert "mardi" in prompt

    def test_system_prompt_restaurant_tone(self):
        brand = _make_brand(brand_type="restaurant")
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "chaleureux" in prompt or "gourmand" in prompt

    def test_system_prompt_custom_instructions(self):
        voice = _make_voice(custom_instructions="Toujours mentionner le brunch du dimanche")
        brand = _make_brand(voice=voice)
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "brunch du dimanche" in prompt


# ── Classification Tests ─────────────────────────────────────────────────────


class TestClassifyInteraction:
    """Tests for interaction classification."""

    @pytest.mark.asyncio
    async def test_classify_positive_review_restaurant(self):
        brand = _make_brand(brand_type="restaurant")
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "classification": "positive",
            "sentiment_score": 0.95,
            "confidence": 0.92,
            "reasoning": "Avis très positif, client satisfait",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.classify_interaction(
            "Excellent repas ! Le couscous royal était divin, service impeccable.",
            rating=5,
        )

        assert result["classification"] == "positive"
        assert result["sentiment_score"] >= 0.8
        assert result["confidence"] >= 0.8
        assert result["should_escalate"] is False

    @pytest.mark.asyncio
    async def test_classify_negative_review_salon(self):
        brand = _make_brand(name="Salon Élégance", brand_type="service")
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "classification": "negative",
            "sentiment_score": 0.15,
            "confidence": 0.88,
            "reasoning": "Client très mécontent du service",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.classify_interaction(
            "Service horrible, 2h d'attente et résultat raté. Jamais plus !",
            rating=1,
        )

        assert result["classification"] == "negative"
        assert result["sentiment_score"] < 0.3

    @pytest.mark.asyncio
    async def test_classify_crisis_keywords_intoxication(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "classification": "crisis",
            "sentiment_score": 0.05,
            "confidence": 0.95,
            "reasoning": "Mention d'intoxication alimentaire",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.classify_interaction(
            "Mon fils a eu une intoxication alimentaire après avoir mangé chez vous !",
            rating=1,
        )

        assert result["classification"] == "crisis"
        assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_classify_crisis_keywords_avocat(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        # Even if LLM says "negative", crisis keyword should override
        mock_response = _mock_claude_response({
            "classification": "negative",
            "sentiment_score": 0.1,
            "confidence": 0.8,
            "reasoning": "Menace juridique",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.classify_interaction(
            "Je vais appeler mon avocat, c'est une arnaque votre restaurant !",
        )

        assert result["classification"] == "crisis"
        assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_classify_question(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "classification": "question",
            "sentiment_score": 0.5,
            "confidence": 0.9,
            "reasoning": "Question sur les horaires",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.classify_interaction(
            "Bonjour, êtes-vous ouvert le dimanche midi ?",
        )

        assert result["classification"] == "question"

    @pytest.mark.asyncio
    async def test_classify_neutral(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "classification": "neutral",
            "sentiment_score": 0.5,
            "confidence": 0.75,
            "reasoning": "Avis mitigé",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        result = await agent.classify_interaction(
            "C'était correct, sans plus. Rien de spécial.",
            rating=3,
        )

        assert result["classification"] == "neutral"

    @pytest.mark.asyncio
    async def test_classify_fallback_on_llm_failure(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(side_effect=Exception("API down"))

        result = await agent.classify_interaction(
            "Super endroit !",
            rating=5,
        )

        # Should use fallback (rating-based)
        assert result["classification"] == "positive"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_classify_fallback_crisis_keyword(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(side_effect=Exception("API down"))

        result = await agent.classify_interaction(
            "Intoxication alimentaire grave !",
        )

        assert result["classification"] == "crisis"
        assert result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_classify_fallback_question_mark(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(side_effect=Exception("API down"))

        result = await agent.classify_interaction("Ouvert le dimanche ?")

        assert result["classification"] == "question"


# ── Response Generation Tests ────────────────────────────────────────────────


class TestGenerateResponse:
    """Tests for AI response generation."""

    @pytest.mark.asyncio
    async def test_generate_response_restaurant_5stars(self):
        brand = _make_brand(brand_type="restaurant")
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Merci infiniment Jean ! Nous sommes ravis que le couscous royal vous ait plu. Au plaisir de vous revoir bientôt !",
            "confidence": 0.92,
            "reasoning": "Avis très positif, réponse chaleureuse et personnalisée",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(
            content="Excellent repas, couscous royal divin !",
            rating=5,
            classification="positive",
        )

        result = await agent.generate_response(interaction)

        assert len(result["response"]) > 0
        assert result["confidence"] > 0.85
        assert result["should_auto_publish"] is True
        # Haiku should be used for positive reviews
        call_args = agent._client.messages.create.call_args
        assert call_args.kwargs["model"] == CMAgent.HAIKU_MODEL

    @pytest.mark.asyncio
    async def test_generate_response_hotel_complaint(self):
        brand = _make_brand(name="Hôtel Lumière", brand_type="service")
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Nous sommes sincèrement désolés de cette expérience. Votre confort est notre priorité et nous aimerions en discuter directement avec vous.",
            "confidence": 0.78,
            "reasoning": "Avis négatif hôtel, réponse empathique avec invitation au contact",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(
            content="Chambre sale, bruit toute la nuit. Très déçu.",
            rating=2,
            classification="negative",
        )

        result = await agent.generate_response(interaction)

        assert result["confidence"] < 0.85
        assert result["should_auto_publish"] is False
        # Sonnet should be used for negative reviews
        call_args = agent._client.messages.create.call_args
        assert call_args.kwargs["model"] == CMAgent.SONNET_MODEL

    @pytest.mark.asyncio
    async def test_generate_response_gym_question(self):
        brand = _make_brand(name="FitZone", brand_type="service")
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Bonjour ! Oui nous proposons un essai gratuit d'une semaine. Passez nous voir, l'équipe vous accueillera avec plaisir !",
            "confidence": 0.88,
            "reasoning": "Question sur l'essai gratuit, réponse informative et motivante",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(
            content="Faites-vous des essais gratuits ?",
            rating=None,
            classification="question",
        )

        result = await agent.generate_response(interaction)

        assert len(result["response"]) > 0
        assert result["should_auto_publish"] is True  # Question with high confidence

    @pytest.mark.asyncio
    async def test_generate_response_crisis_never_auto_publish(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Nous prenons votre retour très au sérieux. Veuillez nous contacter directement pour que nous puissions comprendre et résoudre cette situation.",
            "confidence": 0.95,
            "reasoning": "Crise, réponse empathique sans justification",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(
            content="Intoxication alimentaire ! Mon fils est à l'hôpital !",
            rating=1,
            classification="crisis",
        )

        result = await agent.generate_response(interaction)

        # Even with high confidence, crisis must NEVER auto-publish
        assert result["should_auto_publish"] is False


# ── Auto-publish Threshold Tests ─────────────────────────────────────────────


class TestAutoPublishThreshold:
    """Tests for auto-publish decision logic."""

    @pytest.mark.asyncio
    async def test_auto_publish_high_confidence_positive(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Merci beaucoup !",
            "confidence": 0.92,
            "reasoning": "Simple merci",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=5, classification="positive")
        result = await agent.generate_response(interaction)

        assert result["should_auto_publish"] is True

    @pytest.mark.asyncio
    async def test_no_auto_publish_low_confidence(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Merci pour votre retour.",
            "confidence": 0.60,
            "reasoning": "Confiance basse",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=4, classification="positive")
        result = await agent.generate_response(interaction)

        assert result["should_auto_publish"] is False

    @pytest.mark.asyncio
    async def test_escalate_1star_review(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Nous sommes désolés.",
            "confidence": 0.90,
            "reasoning": "Avis négatif",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=1, classification="negative")
        result = await agent.generate_response(interaction)

        # 1-star: NEVER auto-publish regardless of confidence
        assert result["should_auto_publish"] is False

    @pytest.mark.asyncio
    async def test_escalate_2star_review(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Merci pour votre retour.",
            "confidence": 0.90,
            "reasoning": "Avis mitigé",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=2, classification="negative")
        result = await agent.generate_response(interaction)

        assert result["should_auto_publish"] is False

    @pytest.mark.asyncio
    async def test_auto_publish_3star_high_confidence(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Merci pour votre retour honnête.",
            "confidence": 0.88,
            "reasoning": "Avis neutre",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=3, classification="neutral")
        result = await agent.generate_response(interaction)

        assert result["should_auto_publish"] is True


# ── Crisis Keyword Detection Tests ───────────────────────────────────────────


class TestCrisisKeywords:
    """Tests for crisis keyword detection."""

    def test_crisis_keywords_list_not_empty(self):
        assert len(CRISIS_KEYWORDS) > 20

    def test_french_keywords_present(self):
        assert "intoxication" in CRISIS_KEYWORDS
        assert "allergie" in CRISIS_KEYWORDS
        assert "avocat" in CRISIS_KEYWORDS
        assert "plainte" in CRISIS_KEYWORDS
        assert "signalement" in CRISIS_KEYWORDS

    def test_english_keywords_present(self):
        assert "food poisoning" in CRISIS_KEYWORDS
        assert "lawyer" in CRISIS_KEYWORDS
        assert "lawsuit" in CRISIS_KEYWORDS


# ── Niche Tone Tests ─────────────────────────────────────────────────────────


class TestNicheTones:
    """Tests for niche-specific tone configurations."""

    def test_restaurant_tone_exists(self):
        assert "restaurant" in NICHE_TONE_GUIDE
        tone = NICHE_TONE_GUIDE["restaurant"]
        assert "personality" in tone
        assert "chaleureux" in tone["personality"]

    def test_service_tone_exists(self):
        assert "service" in NICHE_TONE_GUIDE
        tone = NICHE_TONE_GUIDE["service"]
        assert "professionnel" in tone["personality"]

    def test_default_tone_fallback(self):
        assert "personality" in DEFAULT_NICHE_TONE
        assert "greeting" in DEFAULT_NICHE_TONE
        assert "negative_empathy" in DEFAULT_NICHE_TONE

    def test_system_prompt_adapts_to_niche_restaurant(self):
        brand = _make_brand(brand_type="restaurant")
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "chaleureux" in prompt or "gourmand" in prompt

    def test_system_prompt_adapts_to_niche_saas(self):
        brand = _make_brand(name="AppyCorp", brand_type="saas")
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "professionnel" in prompt or "réactif" in prompt

    def test_unknown_niche_uses_default(self):
        brand = _make_brand(brand_type="other")
        # "other" is not in NICHE_TONE_GUIDE so defaults should be used
        agent = CMAgent(brand)
        prompt = agent.build_system_prompt()
        assert "Le Family's" in prompt  # should not crash


# ── Client Initialization Tests ──────────────────────────────────────────────


class TestClientInit:
    """Tests for Anthropic client initialization."""

    def test_no_api_key_raises(self):
        brand = _make_brand()
        agent = CMAgent(brand)
        with patch("app.services.cm_agent.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            mock_settings.cm_auto_publish_threshold = 0.85
            with pytest.raises(RuntimeError, match="Anthropic API key"):
                agent._get_client()

    def test_client_reuses_existing(self):
        brand = _make_brand()
        agent = CMAgent(brand)
        mock_client = MagicMock()
        agent._client = mock_client
        assert agent._get_client() is mock_client


# ── Model Selection Tests ────────────────────────────────────────────────────


class TestModelSelection:
    """Tests verifying correct model selection based on complexity."""

    @pytest.mark.asyncio
    async def test_uses_haiku_for_positive(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Merci !", "confidence": 0.9, "reasoning": "ok",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=5, classification="positive")
        await agent.generate_response(interaction)

        call_kwargs = agent._client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == CMAgent.HAIKU_MODEL

    @pytest.mark.asyncio
    async def test_uses_sonnet_for_negative(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Désolé.", "confidence": 0.7, "reasoning": "ok",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=2, classification="negative")
        await agent.generate_response(interaction)

        call_kwargs = agent._client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == CMAgent.SONNET_MODEL

    @pytest.mark.asyncio
    async def test_uses_sonnet_for_crisis(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Nous prenons cela au sérieux.",
            "confidence": 0.8, "reasoning": "crise",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=1, classification="crisis")
        await agent.generate_response(interaction)

        call_kwargs = agent._client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == CMAgent.SONNET_MODEL

    @pytest.mark.asyncio
    async def test_uses_haiku_for_question(self):
        brand = _make_brand()
        agent = CMAgent(brand)

        mock_response = _mock_claude_response({
            "response": "Oui nous sommes ouverts !",
            "confidence": 0.88, "reasoning": "question simple",
        })
        agent._client = MagicMock()
        agent._client.messages.create = AsyncMock(return_value=mock_response)

        interaction = _make_interaction(rating=None, classification="question")
        await agent.generate_response(interaction)

        call_kwargs = agent._client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == CMAgent.HAIKU_MODEL
