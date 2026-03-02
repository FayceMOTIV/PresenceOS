"""
PresenceOS — Firecrawl Scraper Tests (Sprint 6)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.business_dna import BusinessDNA


class TestFirecrawlScraper:
    """Tests for FirecrawlScraper."""

    @pytest.fixture
    def scraper(self):
        with patch("app.services.firecrawl_scraper.anthropic"):
            from app.services.firecrawl_scraper import FirecrawlScraper
            return FirecrawlScraper()

    @pytest.mark.asyncio
    async def test_scrape_url_fallback_when_no_api_key(self, scraper):
        """Without Firecrawl key, uses httpx fallback."""
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Le Family's</h1><p>Cuisine marseillaise</p></body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.firecrawl_scraper.settings") as mock_s:
            mock_s.firecrawl_api_key = ""
            mock_s.anthropic_api_key = "sk-test"
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
                mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_client.return_value.get = AsyncMock(return_value=mock_response)

                content = await scraper.scrape_url("https://example.com")
                assert content is not None
                assert len(content) > 0

    @pytest.mark.asyncio
    async def test_scrape_url_returns_none_on_failure(self, scraper):
        """Returns None when both Firecrawl and fallback fail."""
        with patch("app.services.firecrawl_scraper.settings") as mock_s:
            mock_s.firecrawl_api_key = ""
            mock_s.anthropic_api_key = "sk-test"
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
                mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_client.return_value.get = AsyncMock(side_effect=Exception("Network error"))

                content = await scraper.scrape_url("https://unreachable.com")
                assert content is None

    @pytest.mark.asyncio
    async def test_extract_dna_from_content(self, scraper):
        """Extracts BusinessDNA from scraped text."""
        mock_resp = MagicMock()
        mock_resp.content = [
            MagicMock(
                text='{"business_name":"Le Familys","business_type":"restaurant","city":"Marseille","cuisine_style":"Cuisine marseillaise","tone_of_voice":"chaleureux","target_audience":null,"ambiance":null,"unique_selling_point":null}'
            )
        ]
        scraper._claude = MagicMock()
        scraper._claude.messages.create.return_value = mock_resp

        dna = await scraper.extract_dna_from_content(
            "Bienvenue au Family's, restaurant marseillais", "https://test.com"
        )
        assert dna.business_name == "Le Familys"
        assert dna.city == "Marseille"
        assert dna.business_type == "restaurant"

    @pytest.mark.asyncio
    async def test_extract_handles_malformed_json(self, scraper):
        """Returns empty BusinessDNA on malformed JSON."""
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text='{"broken json')]
        scraper._claude = MagicMock()
        scraper._claude.messages.create.return_value = mock_resp

        dna = await scraper.extract_dna_from_content("content", "url")
        assert isinstance(dna, BusinessDNA)
        assert dna.business_name == ""

    @pytest.mark.asyncio
    async def test_scrape_and_extract_success(self, scraper):
        """Full pipeline succeeds with mocked scrape + extract."""
        scraper.scrape_url = AsyncMock(return_value="Restaurant Le Family's a Marseille")
        scraper.extract_dna_from_content = AsyncMock(
            return_value=BusinessDNA(
                business_name="Le Family's",
                city="Marseille",
                business_type="restaurant",
                tone_of_voice="chaleureux",
                cuisine_style="Cuisine du terroir",
            )
        )

        result = await scraper.scrape_and_extract("https://test.com")
        assert result["success"] is True
        assert result["fields_found"] >= 2
        assert result["dna"]["business_name"] == "Le Family's"

    @pytest.mark.asyncio
    async def test_scrape_and_extract_handles_failure(self, scraper):
        """Returns failure when scrape returns None."""
        scraper.scrape_url = AsyncMock(return_value=None)

        result = await scraper.scrape_and_extract("https://unreachable.com")
        assert result["success"] is False
        assert result["fields_found"] == 0

    @pytest.mark.asyncio
    async def test_adds_https_if_missing(self, scraper):
        """URL without protocol gets https:// prepended."""
        scraper.scrape_url = AsyncMock(return_value=None)
        await scraper.scrape_and_extract("mon-resto.fr")
        call_url = scraper.scrape_url.call_args[0][0]
        assert call_url.startswith("https://")

    @pytest.mark.asyncio
    async def test_extract_strips_markdown_code_block(self, scraper):
        """Strips ```json blocks from Claude response."""
        mock_resp = MagicMock()
        mock_resp.content = [
            MagicMock(
                text='```json\n{"business_name":"Test","city":"Paris","business_type":"restaurant"}\n```'
            )
        ]
        scraper._claude = MagicMock()
        scraper._claude.messages.create.return_value = mock_resp

        dna = await scraper.extract_dna_from_content("content", "url")
        assert dna.business_name == "Test"
        assert dna.city == "Paris"


class TestScrapeEndpoint:
    """Tests for the /scrape onboarding endpoint."""

    def test_scrape_route_exists(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("scrape" in p for p in paths), f"No scrape route in: {paths}"
