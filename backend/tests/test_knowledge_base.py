"""
PresenceOS - Knowledge Base Service Tests

Tests for KB rebuild, debounce, completeness scoring, and prompt building.
"""
import uuid
from datetime import datetime, timezone, date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.brand import Brand, BrandVoice, BrandType
from app.models.dish import Dish, DishCategory
from app.models.compiled_kb import CompiledKB
from app.models.daily_brief import DailyBrief, BriefStatus
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.prompt_builder import PromptBuilder


# ── Mock Builders ────────────────────────────────────────────────────────


def _make_brand(
    name="Le Bistrot",
    brand_type=BrandType.RESTAURANT,
    description="Restaurant français traditionnel",
    has_voice=True,
    has_logo=True,
    locations=None,
) -> Brand:
    brand = MagicMock(spec=Brand)
    brand.id = uuid.uuid4()
    brand.name = name
    brand.brand_type = brand_type
    brand.description = description
    brand.logo_url = "https://example.com/logo.png" if has_logo else None
    brand.locations = locations or ["Paris 15e"]
    brand.constraints = {"halal": False}
    brand.content_pillars = {"education": 20, "entertainment": 30}
    brand.target_persona = {"name": "Familles"}
    brand.is_active = True

    if has_voice:
        voice = MagicMock(spec=BrandVoice)
        voice.tone_formal = 40
        voice.tone_playful = 70
        voice.tone_bold = 30
        voice.emojis_allowed = ["🍕", "🔥"]
        voice.words_to_avoid = ["cheap", "discount"]
        voice.words_to_prefer = ["artisanal", "maison"]
        voice.custom_instructions = "Toujours mentionner le fait maison"
        voice.primary_language = "fr"
        brand.voice = voice
    else:
        brand.voice = None

    return brand


# ── Completeness Tests ───────────────────────────────────────────────────


class TestCalculateCompleteness:
    """Tests for completeness scoring."""

    def _score(self, brand, menu, media):
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        return service._calculate_completeness_from_sections(brand, identity, menu, media)

    def test_full_completeness_100(self):
        brand = _make_brand(has_voice=True, has_logo=True, locations=["Paris"])
        menu = {"total_dishes": 5, "categories": {}}
        media = {"total_assets": 3, "assets": []}
        assert self._score(brand, menu, media) == 100

    def test_no_data_0(self):
        brand = _make_brand(has_voice=False, has_logo=False, locations=None)
        brand.description = None
        brand.locations = None
        menu = {"total_dishes": 0}
        media = {"total_assets": 0}
        assert self._score(brand, menu, media) == 0

    def test_only_dishes_20(self):
        brand = _make_brand(has_voice=False, has_logo=False, locations=None)
        brand.description = None
        brand.locations = None
        menu = {"total_dishes": 3}
        media = {"total_assets": 0}
        assert self._score(brand, menu, media) == 20

    def test_dishes_and_photos_40(self):
        brand = _make_brand(has_voice=False, has_logo=False, locations=None)
        brand.description = None
        brand.locations = None
        menu = {"total_dishes": 3}
        media = {"total_assets": 2}
        assert self._score(brand, menu, media) == 40

    def test_logo_adds_15(self):
        brand = _make_brand(has_voice=False, has_logo=True, locations=None)
        brand.description = None
        brand.locations = None
        menu = {"total_dishes": 0}
        media = {"total_assets": 0}
        assert self._score(brand, menu, media) == 15

    def test_voice_adds_15(self):
        brand = _make_brand(has_voice=True, has_logo=False, locations=None)
        brand.description = None
        brand.locations = None
        menu = {"total_dishes": 0}
        media = {"total_assets": 0}
        assert self._score(brand, menu, media) == 15

    def test_description_adds_15(self):
        brand = _make_brand(has_voice=False, has_logo=False, locations=None)
        brand.locations = None
        menu = {"total_dishes": 0}
        media = {"total_assets": 0}
        assert self._score(brand, menu, media) == 15

    def test_locations_adds_15(self):
        brand = _make_brand(has_voice=False, has_logo=False, locations=["Paris"])
        brand.description = None
        menu = {"total_dishes": 0}
        media = {"total_assets": 0}
        assert self._score(brand, menu, media) == 15


class TestCompileIdentity:
    """Tests for identity section compilation."""

    def test_identity_includes_brand_name(self):
        brand = _make_brand(name="Chez Marcel")
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        assert identity["name"] == "Chez Marcel"

    def test_identity_includes_type(self):
        brand = _make_brand(brand_type=BrandType.RESTAURANT)
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        assert identity["type"] == "restaurant"

    def test_identity_voice_tone(self):
        brand = _make_brand(has_voice=True)
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        assert identity["voice"]["tone_formal"] == 40
        assert identity["voice"]["tone_playful"] == 70

    def test_identity_no_voice(self):
        brand = _make_brand(has_voice=False)
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        assert identity["voice"]["tone_formal"] == 50  # default

    def test_identity_words_to_avoid(self):
        brand = _make_brand(has_voice=True)
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        assert "cheap" in identity["voice"]["words_to_avoid"]

    def test_identity_locations(self):
        brand = _make_brand(locations=["Paris 15e", "Boulogne"])
        service = KnowledgeBaseService.__new__(KnowledgeBaseService)
        identity = service._compile_identity(brand)
        assert "Paris 15e" in identity["locations"]


# ── Prompt Builder Tests ─────────────────────────────────────────────────


class TestPromptBuilder:
    """Tests for the PromptBuilder service."""

    def _kb(self, **overrides) -> dict:
        base = {
            "identity": {
                "name": "Le Bistrot",
                "type": "restaurant",
                "description": "Restaurant français",
                "voice": {
                    "tone_formal": 40,
                    "tone_playful": 70,
                    "tone_bold": 30,
                    "emojis_allowed": True,
                    "words_to_avoid": ["cheap"],
                    "words_to_prefer": ["artisanal"],
                    "custom_instructions": None,
                    "language": "fr",
                },
            },
            "menu": {
                "total_dishes": 2,
                "categories": {
                    "plats": [
                        {"name": "Entrecôte", "price": 24.90, "is_featured": True, "has_photo": True, "last_posted_at": None},
                        {"name": "Risotto", "price": 18.50, "is_featured": False, "has_photo": False, "last_posted_at": "2024-01-15"},
                    ],
                },
            },
            "media": {"total_assets": 5, "assets": []},
            "today": {"has_brief": False},
            "posting_history": {"last_7_days_count": 3},
            "performance": {},
        }
        base.update(overrides)
        return base

    def test_system_prompt_includes_brand_name(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "Le Bistrot" in prompt

    def test_system_prompt_includes_language(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "français" in prompt

    def test_system_prompt_includes_menu(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "Entrecôte" in prompt
        assert "PLATS" in prompt

    def test_system_prompt_featured_star(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "⭐" in prompt  # Entrecôte is featured

    def test_system_prompt_photo_emoji(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "📸" in prompt  # Entrecôte has photo

    def test_system_prompt_includes_posting_history(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "3" in prompt  # last_7_days_count

    def test_system_prompt_avoids_words(self):
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(self._kb())
        assert "INTERDITS" in prompt
        assert "cheap" in prompt

    def test_system_prompt_brief_included(self):
        kb = self._kb(today={"has_brief": True, "response": "Aujourd'hui plat du jour boeuf bourguignon"})
        pb = PromptBuilder()
        prompt = pb.build_system_prompt(kb)
        assert "boeuf bourguignon" in prompt

    def test_generation_prompt_brief(self):
        pb = PromptBuilder()
        prompt = pb.build_generation_prompt(
            self._kb(),
            source_type="brief",
            source_data={"response": "Plat du jour: magret"},
        )
        assert "magret" in prompt
        assert "JSON" in prompt

    def test_generation_prompt_request(self):
        pb = PromptBuilder()
        prompt = pb.build_generation_prompt(
            self._kb(),
            source_type="request",
            source_data={"text": "Post pour nos desserts"},
        )
        assert "desserts" in prompt

    def test_generation_prompt_asset(self):
        pb = PromptBuilder()
        prompt = pb.build_generation_prompt(
            self._kb(),
            source_type="asset",
            source_data={"description": "Photo de pizza", "label": "pizza", "dish_name": "Pizza Margherita"},
        )
        assert "pizza" in prompt.lower()
        assert "Pizza Margherita" in prompt

    def test_format_guide_reel(self):
        pb = PromptBuilder()
        prompt = pb.build_generation_prompt(
            self._kb(),
            source_type="request",
            source_data={"text": "Un reel tendance"},
            content_type="reel",
        )
        assert "REEL" in prompt

    def test_format_guide_story(self):
        pb = PromptBuilder()
        prompt = pb.build_generation_prompt(
            self._kb(),
            source_type="request",
            source_data={"text": "Story du jour"},
            content_type="story",
        )
        assert "STORY" in prompt


class TestRecentlyPostedDishes:
    """Tests for avoiding recently posted dishes."""

    def test_no_recently_posted(self):
        pb = PromptBuilder()
        menu = {"categories": {"plats": [{"name": "Steak", "last_posted_at": None}]}}
        result = pb._get_recently_posted_dishes(menu)
        assert result == []

    def test_recently_posted_detected(self):
        pb = PromptBuilder()
        menu = {"categories": {"plats": [{"name": "Steak", "last_posted_at": "2024-01-15"}]}}
        result = pb._get_recently_posted_dishes(menu)
        assert "Steak" in result
