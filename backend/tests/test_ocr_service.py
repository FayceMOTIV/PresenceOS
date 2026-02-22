"""
PresenceOS - OCR Service Tests

Tests for menu OCR scanning, category detection, price extraction, error handling.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ocr_service import OCRService


# ── Mock Builders ────────────────────────────────────────────────────────


def _mock_claude_response(content: str) -> MagicMock:
    """Build a mock Anthropic messages.create response."""
    response = MagicMock()
    response.content = [MagicMock(text=content)]
    return response


# ── OCR Parsing Tests ────────────────────────────────────────────────────


class TestParseDishesJson:
    """Tests for JSON parsing of OCR results."""

    def test_parse_valid_json(self):
        ocr = OCRService()
        text = """[
            {"name": "Entrecôte", "category": "plats", "price": 24.90, "description": "Grillée"},
            {"name": "Salade César", "category": "entrees", "price": 12.50, "description": null}
        ]"""
        result = ocr._parse_dishes_json(text)
        assert len(result) == 2
        assert result[0]["name"] == "Entrecôte"
        assert result[0]["price"] == 24.90
        assert result[1]["description"] is None

    def test_parse_json_with_surrounding_text(self):
        ocr = OCRService()
        text = """Here are the dishes I found:
        [{"name": "Pizza", "category": "plats", "price": 14.00, "description": "Margherita"}]
        That's all I could extract."""
        result = ocr._parse_dishes_json(text)
        assert len(result) == 1
        assert result[0]["name"] == "Pizza"

    def test_parse_invalid_category_defaults_to_autres(self):
        ocr = OCRService()
        text = '[{"name": "Mystère", "category": "invalid_category", "price": 10.00, "description": null}]'
        result = ocr._parse_dishes_json(text)
        assert result[0]["category"] == "autres"

    def test_parse_valid_categories(self):
        ocr = OCRService()
        valid_cats = ["entrees", "plats", "desserts", "boissons", "autres"]
        for cat in valid_cats:
            text = f'[{{"name": "Dish", "category": "{cat}", "price": 10, "description": null}}]'
            result = ocr._parse_dishes_json(text)
            assert result[0]["category"] == cat

    def test_parse_price_as_string_converts(self):
        ocr = OCRService()
        text = '[{"name": "Soupe", "category": "entrees", "price": "8.50", "description": null}]'
        result = ocr._parse_dishes_json(text)
        assert result[0]["price"] == 8.50
        assert isinstance(result[0]["price"], float)

    def test_parse_null_price(self):
        ocr = OCRService()
        text = '[{"name": "Plat du jour", "category": "plats", "price": null, "description": "Variable"}]'
        result = ocr._parse_dishes_json(text)
        assert result[0]["price"] is None

    def test_parse_invalid_price_becomes_none(self):
        ocr = OCRService()
        text = '[{"name": "Plat", "category": "plats", "price": "gratuit", "description": null}]'
        result = ocr._parse_dishes_json(text)
        assert result[0]["price"] is None

    def test_parse_skips_items_without_name(self):
        ocr = OCRService()
        text = '[{"name": "", "category": "plats", "price": 10, "description": null}, {"name": "Valid", "category": "plats", "price": 15, "description": null}]'
        result = ocr._parse_dishes_json(text)
        assert len(result) == 1
        assert result[0]["name"] == "Valid"

    def test_parse_no_json_raises(self):
        ocr = OCRService()
        with pytest.raises(ValueError, match="No JSON array"):
            ocr._parse_dishes_json("I couldn't read the menu.")

    def test_parse_empty_array(self):
        ocr = OCRService()
        result = ocr._parse_dishes_json("[]")
        assert result == []


# ── OCR Scan Tests ───────────────────────────────────────────────────────


class TestScanMenuImage:
    """Tests for the full scan_menu_image pipeline."""

    @pytest.mark.asyncio
    async def test_scan_returns_dishes(self):
        ocr = OCRService()
        response_json = json.dumps([
            {"name": "Magret de canard", "category": "plats", "price": 22.00, "description": "Sauce miel"},
            {"name": "Crème brûlée", "category": "desserts", "price": 9.50, "description": None},
        ])

        with patch.object(ocr, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response(response_json)
            )
            result = await ocr.scan_menu_image(b"fake_image_bytes", "image/jpeg")

        assert len(result) == 2
        assert result[0]["name"] == "Magret de canard"
        assert result[0]["category"] == "plats"
        assert result[1]["price"] == 9.50

    @pytest.mark.asyncio
    async def test_scan_empty_menu(self):
        ocr = OCRService()
        with patch.object(ocr, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("[]")
            )
            result = await ocr.scan_menu_image(b"fake_image_bytes")

        assert result == []

    @pytest.mark.asyncio
    async def test_scan_api_failure_raises(self):
        ocr = OCRService()
        with patch.object(ocr, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                side_effect=Exception("API error")
            )
            with pytest.raises(Exception, match="API error"):
                await ocr.scan_menu_image(b"fake_image_bytes")

    @pytest.mark.asyncio
    async def test_scan_handles_messy_response(self):
        ocr = OCRService()
        messy_response = """Based on the menu image, I extracted:
        [{"name": "Tartare", "category": "plats", "price": 19.00, "description": "De boeuf"}]
        Hope this helps!"""

        with patch.object(ocr, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response(messy_response)
            )
            result = await ocr.scan_menu_image(b"fake_image_bytes")

        assert len(result) == 1
        assert result[0]["name"] == "Tartare"
