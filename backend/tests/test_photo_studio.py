"""
PresenceOS - Tests for PhotoStudio (AI Photo Generation)

Unit tests for the Gemini Image photo generation service with full mocking
of external dependencies (Gemini, S3/MinIO storage).

Migration: DALL-E 3 → Gemini Image (March 2026)
"""
import base64

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.photo_studio import (
    PhotoStudio,
    STYLE_DESCRIPTIONS,
    NICHE_CONTEXTS,
    DEFAULT_NICHE_CONTEXT,
    NEGATIVE_INSTRUCTIONS,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def studio():
    """Create a PhotoStudio instance."""
    return PhotoStudio()


@pytest.fixture
def mock_gemini_response():
    """Build a realistic Gemini Image response object."""
    fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 500
    fake_b64 = base64.b64encode(fake_image).decode()

    mock_part = MagicMock()
    mock_part.inline_data = MagicMock()
    mock_part.inline_data.data = fake_b64

    response = MagicMock()
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [mock_part]
    return response


@pytest.fixture
def mock_storage():
    """Build a mocked StorageService."""
    storage = MagicMock()
    storage.generate_key.return_value = "brands/ai-studio/media/2026/03/abc123_gemini_restaurant_natural.png"
    storage.upload_bytes = AsyncMock(return_value={
        "key": "brands/ai-studio/media/2026/03/abc123_gemini_restaurant_natural.png",
        "url": "http://minio:9000/presenceos-media/brands/ai-studio/media/abc.png",
        "size": 1024000,
    })
    return storage


# ── Prompt Enhancement Tests ─────────────────────────────────────────────────


class TestPromptEnhancement:
    """Tests for _enhance_prompt logic."""

    def test_enhance_prompt_contains_user_prompt(self, studio):
        result = studio._enhance_prompt("a delicious pizza", "restaurant", "natural")
        assert "a delicious pizza" in result

    def test_enhance_prompt_includes_style(self, studio):
        result = studio._enhance_prompt("a dish", "restaurant", "cinematic")
        assert "cinematic" in result.lower()

    def test_enhance_prompt_includes_niche_context(self, studio):
        result = studio._enhance_prompt("a dish", "restaurant", "natural")
        niche_ctx = NICHE_CONTEXTS["restaurant"]
        assert niche_ctx["setting"] in result

    def test_enhance_prompt_uses_default_for_unknown_niche(self, studio):
        result = studio._enhance_prompt("a photo", "unknown_niche", "natural")
        assert DEFAULT_NICHE_CONTEXT["setting"] in result

    def test_enhance_prompt_includes_negative_instructions(self, studio):
        result = studio._enhance_prompt("a photo", "cafe", "vibrant")
        assert "must NOT contain" in result

    def test_enhance_prompt_includes_brand_name(self, studio):
        result = studio._enhance_prompt("a photo", "cafe", "natural", brand_name="TestBrand")
        assert "TestBrand" in result
        assert "sophistication" in result

    def test_enhance_prompt_without_brand_name(self, studio):
        result = studio._enhance_prompt("a photo", "cafe", "natural", brand_name=None)
        assert "sophistication" not in result

    def test_all_styles_produce_different_prompts(self, studio):
        prompts = set()
        for style in STYLE_DESCRIPTIONS:
            prompt = studio._enhance_prompt("test", "restaurant", style)
            prompts.add(prompt)
        assert len(prompts) == len(STYLE_DESCRIPTIONS)

    def test_all_niches_produce_different_prompts(self, studio):
        prompts = set()
        for niche in NICHE_CONTEXTS:
            prompt = studio._enhance_prompt("test", niche, "natural")
            prompts.add(prompt)
        assert len(prompts) == len(NICHE_CONTEXTS)


# ── Supported Niches Tests ───────────────────────────────────────────────────


class TestSupportedNiches:
    """Tests for get_supported_niches."""

    def test_returns_list_of_dicts(self):
        niches = PhotoStudio.get_supported_niches()
        assert isinstance(niches, list)
        assert len(niches) > 0
        for niche in niches:
            assert "id" in niche
            assert "label" in niche

    def test_all_niche_contexts_have_labels(self):
        niches = PhotoStudio.get_supported_niches()
        niche_ids = {n["id"] for n in niches}
        for ctx_id in NICHE_CONTEXTS:
            assert ctx_id in niche_ids, f"Niche '{ctx_id}' in NICHE_CONTEXTS but missing from labels"

    def test_niche_count(self):
        niches = PhotoStudio.get_supported_niches()
        assert len(niches) >= 20


# ── Style/Niche Constants Tests ──────────────────────────────────────────────


class TestConstants:
    """Tests for style and niche configuration."""

    def test_all_styles_defined(self):
        expected = {"natural", "cinematic", "vibrant", "minimalist"}
        assert set(STYLE_DESCRIPTIONS.keys()) == expected

    def test_style_descriptions_are_non_empty(self):
        for style, desc in STYLE_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Style '{style}' description too short"

    def test_niche_contexts_have_required_keys(self):
        required_keys = {"setting", "subjects", "mood"}
        for niche_id, ctx in NICHE_CONTEXTS.items():
            assert set(ctx.keys()) == required_keys, (
                f"Niche '{niche_id}' missing keys: {required_keys - set(ctx.keys())}"
            )

    def test_default_niche_context_has_required_keys(self):
        assert "setting" in DEFAULT_NICHE_CONTEXT
        assert "subjects" in DEFAULT_NICHE_CONTEXT
        assert "mood" in DEFAULT_NICHE_CONTEXT

    def test_negative_instructions_block_text(self):
        assert "text" in NEGATIVE_INSTRUCTIONS.lower()
        assert "watermark" in NEGATIVE_INSTRUCTIONS.lower()
        assert "logo" in NEGATIVE_INSTRUCTIONS.lower()


# ── Photo Generation Tests (Gemini Image) ────────────────────────────────────


class TestGeneratePhoto:
    """Tests for generate_photo with mocked Gemini."""

    @pytest.mark.asyncio
    async def test_generate_photo_success(self, studio, mock_gemini_response, mock_storage):
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_gemini_response

        studio._storage = mock_storage

        with (
            patch.object(studio, "_get_model", return_value=mock_model),
            patch("app.ai.photo_studio.asyncio") as mock_asyncio,
        ):
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=mock_gemini_response)
            mock_asyncio.get_event_loop.return_value = mock_loop

            result = await studio.generate_photo(
                prompt="a beautiful pizza",
                niche="restaurant",
                style="natural",
                size="1024x1024",
            )

        assert "image_url" in result
        assert result["style"] == "natural"
        assert result["niche"] == "restaurant"
        assert result["size"] == "1024x1024"
        assert result["original_prompt"] == "a beautiful pizza"
        assert "enhanced_prompt" in result
        assert "generated_at" in result

    @pytest.mark.asyncio
    async def test_generate_photo_with_brand(self, studio, mock_gemini_response, mock_storage):
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_gemini_response

        studio._storage = mock_storage

        with (
            patch.object(studio, "_get_model", return_value=mock_model),
            patch("app.ai.photo_studio.asyncio") as mock_asyncio,
        ):
            mock_loop = MagicMock()
            mock_loop.run_in_executor = AsyncMock(return_value=mock_gemini_response)
            mock_asyncio.get_event_loop.return_value = mock_loop

            result = await studio.generate_photo(
                prompt="latte art",
                niche="cafe",
                style="minimalist",
                brand_name="CaféChic",
            )

        assert "CaféChic" in result["enhanced_prompt"]

    @pytest.mark.asyncio
    async def test_generate_photo_no_api_key_raises(self):
        studio = PhotoStudio()
        with patch("app.ai.photo_studio.settings") as mock_settings:
            mock_settings.google_api_key = ""
            mock_settings.gemini_api_key = ""
            with pytest.raises(RuntimeError, match="Google API key"):
                await studio.generate_photo(prompt="test")

    @pytest.mark.asyncio
    async def test_generate_photo_gemini_error_propagates(self, studio, mock_storage):
        studio._storage = mock_storage

        with (
            patch.object(studio, "_get_model", side_effect=RuntimeError("Google API key not configured")),
        ):
            with pytest.raises(RuntimeError, match="Google API key"):
                await studio.generate_photo(prompt="test")


# ── Image Persistence Tests ──────────────────────────────────────────────────


class TestImagePersistence:
    """Tests for _persist_image S3 upload (now takes bytes directly)."""

    @pytest.mark.asyncio
    async def test_persist_image_success(self, studio, mock_storage):
        studio._storage = mock_storage

        fake_image = b"\x89PNG\r\n" + b"\x00" * 500
        url = await studio._persist_image(fake_image, "restaurant", "natural")

        assert "minio" in url or "s3" in url or "presenceos" in url
        mock_storage.upload_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_image_no_storage_raises(self, studio):
        studio._storage = None
        with patch.object(studio, "_get_storage", return_value=None):
            with pytest.raises(RuntimeError, match="Storage service not available"):
                await studio._persist_image(b"\x89PNG", "restaurant", "natural")


# ── Variations Tests ─────────────────────────────────────────────────────────


class TestGenerateVariations:
    """Tests for generate_variations parallel generation."""

    @pytest.mark.asyncio
    async def test_generate_variations_returns_4_styles(self, studio, mock_gemini_response, mock_storage):
        studio._storage = mock_storage

        results = []
        for style in ["natural", "cinematic", "vibrant", "minimalist"]:
            results.append({
                "image_url": f"http://example.com/{style}.png",
                "original_prompt": "a dish",
                "enhanced_prompt": f"test prompt for {style}",
                "style": style,
                "niche": "restaurant",
                "size": "1024x1024",
                "generated_at": "2026-03-08T12:00:00Z",
            })

        with patch.object(studio, "generate_photo", new_callable=AsyncMock, side_effect=results):
            variations = await studio.generate_variations(base_prompt="a dish", niche="restaurant")

        assert len(variations) == 4
        styles_returned = {v["style"] for v in variations}
        assert styles_returned == {"natural", "cinematic", "vibrant", "minimalist"}

    @pytest.mark.asyncio
    async def test_generate_variations_with_count_limit(self, studio, mock_gemini_response, mock_storage):
        studio._storage = mock_storage

        results = [
            {"image_url": "http://ex.com/1.png", "style": "natural", "niche": "cafe",
             "original_prompt": "a dish", "enhanced_prompt": "p1", "size": "1024x1024", "generated_at": "2026"},
            {"image_url": "http://ex.com/2.png", "style": "cinematic", "niche": "cafe",
             "original_prompt": "a dish", "enhanced_prompt": "p2", "size": "1024x1024", "generated_at": "2026"},
        ]

        with patch.object(studio, "generate_photo", new_callable=AsyncMock, side_effect=results):
            variations = await studio.generate_variations(base_prompt="a dish", niche="cafe", count=2)

        assert len(variations) == 2

    @pytest.mark.asyncio
    async def test_generate_variations_propagates_brand_name(self, studio, mock_gemini_response, mock_storage):
        studio._storage = mock_storage

        results = []
        for style in ["natural", "cinematic", "vibrant", "minimalist"]:
            results.append({
                "image_url": f"http://ex.com/{style}.png",
                "original_prompt": "a dish",
                "enhanced_prompt": f"test for Chez Marcel in {style}",
                "style": style,
                "niche": "restaurant",
                "size": "1024x1024",
                "generated_at": "2026",
            })

        with patch.object(studio, "generate_photo", new_callable=AsyncMock, side_effect=results):
            variations = await studio.generate_variations(
                base_prompt="a dish",
                niche="restaurant",
                brand_name="Chez Marcel",
            )

        for v in variations:
            assert "Chez Marcel" in v["enhanced_prompt"]
