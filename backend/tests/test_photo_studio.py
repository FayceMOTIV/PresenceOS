"""
PresenceOS - Tests for PhotoStudio (AI Photo Generation)

Unit tests for the DALL-E 3 photo generation service with full mocking
of external dependencies (OpenAI, S3/MinIO storage).
"""
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
    """Create a PhotoStudio instance with mocked OpenAI client."""
    s = PhotoStudio()
    return s


@pytest.fixture
def mock_openai_response():
    """Build a realistic DALL-E 3 response object."""
    image_data = MagicMock()
    image_data.url = "https://oaidalleapiprodscus.blob.core.windows.net/fake-image.png"
    image_data.revised_prompt = "A professional marketing photograph of a dish..."

    response = MagicMock()
    response.data = [image_data]
    return response


@pytest.fixture
def mock_storage():
    """Build a mocked StorageService."""
    storage = MagicMock()
    storage.generate_key.return_value = "brands/ai-studio/media/2026/02/abc123_dalle_restaurant_natural.png"
    storage.upload_bytes = AsyncMock(return_value={
        "key": "brands/ai-studio/media/2026/02/abc123_dalle_restaurant_natural.png",
        "url": "http://minio:9000/presenceos-media/brands/ai-studio/media/2026/02/abc123_dalle_restaurant_natural.png",
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


# ── Photo Generation Tests ───────────────────────────────────────────────────


class TestGeneratePhoto:
    """Tests for generate_photo with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_generate_photo_success(self, studio, mock_openai_response, mock_storage):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_openai_response)
        studio._client = mock_client
        studio._storage = mock_storage

        # Mock httpx for image download
        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1000
            mock_resp.raise_for_status = MagicMock()

            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

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
        mock_client.images.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_photo_with_brand(self, studio, mock_openai_response, mock_storage):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_openai_response)
        studio._client = mock_client
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG" + b"\x00" * 100
            mock_resp.raise_for_status = MagicMock()
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            result = await studio.generate_photo(
                prompt="latte art",
                niche="cafe",
                style="minimalist",
                brand_name="CaféChic",
            )

        assert "CaféChic" in result["enhanced_prompt"]

    @pytest.mark.asyncio
    async def test_generate_photo_uses_hd_quality(self, studio, mock_openai_response, mock_storage):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_openai_response)
        studio._client = mock_client
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG" + b"\x00" * 100
            mock_resp.raise_for_status = MagicMock()
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            await studio.generate_photo(prompt="test", niche="restaurant")

        call_kwargs = mock_client.images.generate.call_args
        assert call_kwargs.kwargs["quality"] == "hd"
        assert call_kwargs.kwargs["model"] == "dall-e-3"

    @pytest.mark.asyncio
    async def test_generate_photo_no_api_key_raises(self):
        studio = PhotoStudio()
        with patch("app.ai.photo_studio.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            with pytest.raises(RuntimeError, match="OpenAI API key"):
                await studio.generate_photo(prompt="test")

    @pytest.mark.asyncio
    async def test_generate_photo_openai_error_propagates(self, studio):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(side_effect=Exception("API overloaded"))
        studio._client = mock_client

        with pytest.raises(Exception, match="API overloaded"):
            await studio.generate_photo(prompt="test")


# ── Image Persistence Tests ──────────────────────────────────────────────────


class TestImagePersistence:
    """Tests for _persist_image S3 upload."""

    @pytest.mark.asyncio
    async def test_persist_image_success(self, studio, mock_storage):
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG\r\n" + b"\x00" * 500
            mock_resp.raise_for_status = MagicMock()

            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            url = await studio._persist_image("https://dalle.example.com/img.png", "restaurant", "natural")

        assert "minio" in url or "s3" in url or "presenceos" in url
        mock_storage.upload_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_image_no_storage_returns_original(self, studio):
        studio._storage = None
        with patch.object(studio, "_get_storage", return_value=None):
            url = await studio._persist_image("https://dalle.example.com/img.png", "restaurant", "natural")
        assert url == "https://dalle.example.com/img.png"

    @pytest.mark.asyncio
    async def test_persist_image_download_failure_returns_original(self, studio, mock_storage):
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(side_effect=Exception("Network error"))
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            url = await studio._persist_image("https://dalle.example.com/img.png", "cafe", "vibrant")

        assert url == "https://dalle.example.com/img.png"


# ── Variations Tests ─────────────────────────────────────────────────────────


class TestGenerateVariations:
    """Tests for generate_variations parallel generation."""

    @pytest.mark.asyncio
    async def test_generate_variations_returns_4_styles(self, studio, mock_openai_response, mock_storage):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_openai_response)
        studio._client = mock_client
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG" + b"\x00" * 100
            mock_resp.raise_for_status = MagicMock()
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            variations = await studio.generate_variations(base_prompt="a dish", niche="restaurant")

        assert len(variations) == 4
        styles_returned = {v["style"] for v in variations}
        assert styles_returned == {"natural", "cinematic", "vibrant", "minimalist"}

    @pytest.mark.asyncio
    async def test_generate_variations_with_count_limit(self, studio, mock_openai_response, mock_storage):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_openai_response)
        studio._client = mock_client
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG" + b"\x00" * 100
            mock_resp.raise_for_status = MagicMock()
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            variations = await studio.generate_variations(base_prompt="a dish", niche="cafe", count=2)

        assert len(variations) == 2

    @pytest.mark.asyncio
    async def test_generate_variations_propagates_brand_name(self, studio, mock_openai_response, mock_storage):
        mock_client = MagicMock()
        mock_client.images.generate = AsyncMock(return_value=mock_openai_response)
        studio._client = mock_client
        studio._storage = mock_storage

        with patch("app.ai.photo_studio.httpx.AsyncClient") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.content = b"\x89PNG" + b"\x00" * 100
            mock_resp.raise_for_status = MagicMock()
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
            mock_httpx_instance.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
            mock_httpx_instance.__aexit__ = AsyncMock(return_value=False)
            mock_httpx.return_value = mock_httpx_instance

            variations = await studio.generate_variations(
                base_prompt="a dish",
                niche="restaurant",
                brand_name="Chez Marcel",
            )

        for v in variations:
            assert "Chez Marcel" in v["enhanced_prompt"]
