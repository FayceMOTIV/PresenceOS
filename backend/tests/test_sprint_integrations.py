"""
PresenceOS - Tests for Sprint Integrations

Tests for:
- normalize_image utility (HEIC/WebP → JPEG)
- WeatherService (Open-Meteo)
- TrendingService (pytrends + Redis cache)
- InstagramHashtagService (scoring)
- DishRecognitionService (Gemini Vision)
"""

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image


# ── normalize_image ──────────────────────────────────────────────────────


class TestNormalizeImage:
    """Tests for app.utils.normalize_image.normalize_image"""

    def _make_test_image(self, mode: str = "RGB", size: tuple = (100, 100), fmt: str = "JPEG") -> bytes:
        img = Image.new(mode, size, color=(255, 128, 0))
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    def test_jpeg_passthrough(self):
        from app.utils.normalize_image import normalize_image

        raw = self._make_test_image("RGB", (200, 200), "JPEG")
        result = normalize_image(raw)
        # Should return JPEG bytes
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"
        assert img.mode == "RGB"

    def test_png_to_jpeg(self):
        from app.utils.normalize_image import normalize_image

        raw = self._make_test_image("RGBA", (200, 200), "PNG")
        result = normalize_image(raw)
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"
        assert img.mode == "RGB"

    def test_resize_large_image(self):
        from app.utils.normalize_image import normalize_image

        raw = self._make_test_image("RGB", (4000, 3000), "JPEG")
        result = normalize_image(raw, max_size=1024)
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 1024

    def test_small_image_not_resized(self):
        from app.utils.normalize_image import normalize_image

        raw = self._make_test_image("RGB", (500, 400), "JPEG")
        result = normalize_image(raw, max_size=2048)
        img = Image.open(io.BytesIO(result))
        assert img.size == (500, 400)

    def test_webp_to_jpeg(self):
        from app.utils.normalize_image import normalize_image

        raw = self._make_test_image("RGB", (200, 200), "WebP")
        result = normalize_image(raw)
        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"


# ── WeatherService ───────────────────────────────────────────────────────


class TestWeatherService:
    """Tests for app.services.weather_service.WeatherService"""

    @pytest.mark.asyncio
    async def test_get_weather_with_valid_location(self):
        from app.services.weather_service import WeatherService

        mock_geocode_response = MagicMock()
        mock_geocode_response.status_code = 200
        mock_geocode_response.raise_for_status = MagicMock()
        mock_geocode_response.json.return_value = {
            "results": [{"latitude": 48.8566, "longitude": 2.3522}]
        }

        mock_weather_response = MagicMock()
        mock_weather_response.status_code = 200
        mock_weather_response.raise_for_status = MagicMock()
        mock_weather_response.json.return_value = {
            "current": {
                "temperature_2m": 18.5,
                "weather_code": 1,
                "wind_speed_10m": 12.3,
            }
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(
                side_effect=[mock_geocode_response, mock_weather_response]
            )
            mock_client_cls.return_value = mock_client

            svc = WeatherService()
            result = await svc.get_current_weather(["Paris 11e"])

        assert result is not None
        assert "18°C" in result
        assert "Paris 11e" in result

    @pytest.mark.asyncio
    async def test_returns_none_without_locations(self):
        from app.services.weather_service import WeatherService

        svc = WeatherService()
        result = await svc.get_current_weather(None)
        assert result is None

        result = await svc.get_current_weather([])
        assert result is None

    @pytest.mark.asyncio
    async def test_geocode_failure_returns_none(self):
        from app.services.weather_service import WeatherService

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=Exception("Network error"))
            mock_client_cls.return_value = mock_client

            svc = WeatherService()
            result = await svc.get_current_weather(["Unknown Place"])

        assert result is None


# ── TrendingService ──────────────────────────────────────────────────────


class TestTrendingService:
    """Tests for app.services.trending_service.TrendingService"""

    @pytest.mark.asyncio
    async def test_fallback_hashtags_when_pytrends_fails(self):
        from app.services.trending_service import TrendingService

        svc = TrendingService()

        with patch.object(svc, "_fetch_from_pytrends", side_effect=Exception("API error")):
            result = await svc.get_trending_hashtags(niche="restaurant")

        assert len(result) > 0
        assert result[0]["tag"].startswith("#")
        assert "score" in result[0]

    @pytest.mark.asyncio
    async def test_fallback_includes_niche_specific_tags(self):
        from app.services.trending_service import TrendingService

        svc = TrendingService()
        result = svc._fallback_hashtags("pizzeria pizza")
        tags = [h["tag"] for h in result]
        assert "#pizza" in tags

    def test_format_for_prompt(self):
        from app.services.trending_service import TrendingService

        svc = TrendingService()
        hashtags = [
            {"tag": "#foodie", "score": 95},
            {"tag": "#restaurant", "score": 90},
        ]
        result = svc.format_for_prompt(hashtags)
        assert "HASHTAGS TENDANCE" in result
        assert "#foodie" in result

    def test_format_empty_list(self):
        from app.services.trending_service import TrendingService

        svc = TrendingService()
        assert svc.format_for_prompt([]) == ""

    @pytest.mark.asyncio
    async def test_redis_cache_hit(self):
        from app.services.trending_service import TrendingService

        cached_data = json.dumps([{"tag": "#cached", "score": 100}])

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_data)

        svc = TrendingService()
        svc._redis = mock_redis

        result = await svc.get_trending_hashtags()
        assert result[0]["tag"] == "#cached"
        mock_redis.get.assert_called_once()


# ── InstagramHashtagService ──────────────────────────────────────────────


class TestInstagramHashtagService:
    """Tests for app.services.instagram_hashtag_service.InstagramHashtagService"""

    def test_compute_score_sweet_spot(self):
        from app.services.instagram_hashtag_service import InstagramHashtagService

        # 100K-1M is ideal (90)
        assert InstagramHashtagService._compute_score(500_000) == 90
        # < 10K is too niche (35)
        assert InstagramHashtagService._compute_score(5_000) == 35
        # > 50M is oversaturated (35)
        assert InstagramHashtagService._compute_score(100_000_000) == 35

    def test_heuristic_score_food_keywords(self):
        from app.services.instagram_hashtag_service import InstagramHashtagService

        score_food = InstagramHashtagService._heuristic_score("foodparis")
        score_generic = InstagramHashtagService._heuristic_score("xyz")
        assert score_food > score_generic

    @pytest.mark.asyncio
    async def test_score_without_api_keys(self):
        from app.services.instagram_hashtag_service import InstagramHashtagService

        svc = InstagramHashtagService(ig_business_id=None, access_token=None)
        results = await svc.score_hashtags(["#foodie", "#restaurant"])
        assert len(results) == 2
        assert all(r["tag"].startswith("#") for r in results)
        assert all("score" in r for r in results)

    @pytest.mark.asyncio
    async def test_dedup_and_sort(self):
        from app.services.instagram_hashtag_service import InstagramHashtagService

        svc = InstagramHashtagService()
        results = await svc.score_hashtags(["#foodie", "#foodie", "#test"])
        tags = [r["tag"] for r in results]
        assert len(tags) == len(set(tags))  # No duplicates


# ── DishRecognitionService ───────────────────────────────────────────────


class TestDishRecognitionService:
    """Tests for app.services.dish_recognition_service.DishRecognitionService"""

    @pytest.mark.asyncio
    async def test_recognize_returns_result(self):
        from app.services.dish_recognition_service import DishRecognitionService

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "dish_name": "Tartare de saumon",
            "category": "entrée",
            "description": "Un tartare frais et coloré",
            "confidence": 0.92,
            "tags": ["saumon", "frais", "tartare"],
        })

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)

        svc = DishRecognitionService()
        svc._client = mock_model

        # Create a small test JPEG
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        test_bytes = buf.getvalue()

        result = await svc.recognize(test_bytes)
        assert result.dish_name == "Tartare de saumon"
        assert result.category == "entrée"
        assert result.confidence == 0.92
        assert "saumon" in result.tags

    def test_result_to_dict(self):
        from app.services.dish_recognition_service import DishRecognitionResult

        result = DishRecognitionResult(
            dish_name="Pizza Margherita",
            category="plat",
            description="Pizza classique italienne",
            confidence=0.88,
            tags=["pizza", "italien"],
        )
        d = result.to_dict()
        assert d["dish_name"] == "Pizza Margherita"
        assert d["category"] == "plat"
        assert d["confidence"] == 0.88
        assert "pizza" in d["tags"]
