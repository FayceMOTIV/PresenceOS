"""
Tests for CalendarIntelligence (F1: Conscience Temporelle)
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.calendar_intelligence import (
    CalendarIntelligence,
    _easter_date,
    _get_mobile_french_holidays,
    FRENCH_HOLIDAYS,
    ISLAMIC_EVENTS,
)


class TestEasterDate:
    """Test the Easter computation algorithm."""

    def test_easter_2025(self):
        assert _easter_date(2025) == date(2025, 4, 20)

    def test_easter_2026(self):
        assert _easter_date(2026) == date(2026, 4, 5)

    def test_easter_2027(self):
        assert _easter_date(2027) == date(2027, 3, 28)

    def test_easter_2024(self):
        assert _easter_date(2024) == date(2024, 3, 31)


class TestMobileFrenchHolidays:
    """Test mobile French holidays computation."""

    def test_fete_des_meres_2025(self):
        holidays = _get_mobile_french_holidays(2025)
        fete_meres = [d for d, name in holidays.items() if "Mères" in name]
        assert len(fete_meres) == 1
        assert fete_meres[0].month in (5, 6)  # Always May or June
        assert fete_meres[0].weekday() == 6  # Always a Sunday

    def test_fete_des_peres_2025(self):
        holidays = _get_mobile_french_holidays(2025)
        fete_peres = [d for d, name in holidays.items() if "Pères" in name]
        assert len(fete_peres) == 1
        assert fete_peres[0].month == 6  # Always June
        assert fete_peres[0].weekday() == 6  # Always a Sunday

    def test_lundi_paques_2025(self):
        holidays = _get_mobile_french_holidays(2025)
        lundi_paques = [d for d, name in holidays.items() if "Lundi de Pâques" in name]
        assert len(lundi_paques) == 1
        easter = _easter_date(2025)
        assert lundi_paques[0] == date(easter.year, easter.month, easter.day + 1) or \
               (lundi_paques[0] - easter).days == 1

    def test_ascension_2025(self):
        holidays = _get_mobile_french_holidays(2025)
        ascension = [d for d, name in holidays.items() if "Ascension" in name]
        assert len(ascension) == 1
        easter = _easter_date(2025)
        assert (ascension[0] - easter).days == 39


class TestCalendarIntelligence:
    """Test the main CalendarIntelligence service."""

    def _make_ci(self, fixed_today: date) -> CalendarIntelligence:
        """Create a CalendarIntelligence with a fixed date for deterministic tests."""
        ci = CalendarIntelligence()
        ci._get_today = lambda: fixed_today  # type: ignore[method-assign]
        return ci

    def test_detects_christmas(self):
        ci = self._make_ci(date(2025, 12, 20))
        events = ci.get_upcoming_events(days_ahead=14)
        names = [e["name"] for e in events]
        assert "Noël" in names

    def test_detects_bastille_day(self):
        ci = self._make_ci(date(2025, 7, 10))
        events = ci.get_upcoming_events(days_ahead=14)
        names = [e["name"] for e in events]
        assert "Fête Nationale" in names

    def test_detects_new_year(self):
        ci = self._make_ci(date(2025, 12, 28))
        events = ci.get_upcoming_events(days_ahead=14)
        names = [e["name"] for e in events]
        assert "Saint-Sylvestre / Réveillon" in names

    def test_empty_when_no_events_nearby(self):
        # Mid-March 2025 — no fixed holidays within 7 days
        ci = self._make_ci(date(2025, 3, 10))
        events = ci.get_upcoming_events(days_ahead=7)
        # Filter only holidays (commercial seasons may show)
        holidays = [e for e in events if e["type"] == "holiday"]
        assert len(holidays) == 0

    def test_days_until_correct(self):
        ci = self._make_ci(date(2025, 12, 22))
        events = ci.get_upcoming_events(days_ahead=14)
        noel = next((e for e in events if e["name"] == "Noël"), None)
        assert noel is not None
        assert noel["days_until"] == 3

    def test_ramadan_detected_for_halal(self):
        """Ramadan 2025 starts Feb 28."""
        ci = self._make_ci(date(2025, 2, 25))
        events = ci.get_upcoming_events(days_ahead=14)
        ramadan = [e for e in events if "Ramadan" in e["name"]]
        assert len(ramadan) > 0

    def test_commercial_season_in_progress(self):
        """Test that a commercial season is detected when inside it."""
        ci = self._make_ci(date(2025, 7, 1))
        events = ci.get_upcoming_events(days_ahead=14)
        soldes = [e for e in events if "Soldes" in e["name"] and "en cours" in e["name"]]
        assert len(soldes) > 0

    @pytest.mark.asyncio
    async def test_temporal_context_format(self):
        """Test the full temporal context output format."""
        ci = self._make_ci(date(2025, 12, 22))

        # Mock weather to avoid real HTTP calls
        with patch.object(ci, "get_weather_context", new_callable=AsyncMock, return_value=None):
            ctx = await ci.get_temporal_context(
                brand_locations=["Paris 15e"],
                brand_niche="restaurant",
                brand_constraints=None,
            )

        assert "CONTEXTE TEMPOREL" in ctx
        assert "Date :" in ctx
        assert "Noël" in ctx
        assert "semaine" in ctx

    @pytest.mark.asyncio
    async def test_temporal_context_with_weather(self):
        """Test temporal context includes weather when available."""
        ci = self._make_ci(date(2025, 7, 14))

        weather_text = "Météo actuelle à Paris : 28°C, ciel dégagé ☀️"
        with patch.object(ci, "get_weather_context", new_callable=AsyncMock, return_value=weather_text):
            ctx = await ci.get_temporal_context(
                brand_locations=["Paris 15e"],
                brand_niche="restaurant",
            )

        assert "28°C" in ctx
        assert "Adapte tes propositions" in ctx

    @pytest.mark.asyncio
    async def test_temporal_context_halal_includes_islamic(self):
        """Halal brands should see Islamic events."""
        ci = self._make_ci(date(2025, 2, 25))

        with patch.object(ci, "get_weather_context", new_callable=AsyncMock, return_value=None):
            ctx = await ci.get_temporal_context(
                brand_locations=["Paris"],
                brand_niche="restaurant",
                brand_constraints={"halal": True},
            )

        assert "Ramadan" in ctx

    @pytest.mark.asyncio
    async def test_temporal_context_non_halal_skips_islamic(self):
        """Non-halal brands should not see Islamic events."""
        ci = self._make_ci(date(2025, 2, 25))

        with patch.object(ci, "get_weather_context", new_callable=AsyncMock, return_value=None):
            ctx = await ci.get_temporal_context(
                brand_locations=["Paris"],
                brand_niche="restaurant",
                brand_constraints={"halal": False},
            )

        assert "Ramadan" not in ctx

    @pytest.mark.asyncio
    async def test_seasonal_hint_restaurant_winter(self):
        """Restaurant in winter should get seasonal food hints."""
        ci = self._make_ci(date(2025, 1, 15))

        with patch.object(ci, "get_weather_context", new_callable=AsyncMock, return_value=None):
            ctx = await ci.get_temporal_context(
                brand_niche="restaurant",
            )

        assert "galette des rois" in ctx or "chandeleur" in ctx

    @pytest.mark.asyncio
    async def test_no_crash_on_weather_failure(self):
        """Weather failure should not crash the context builder."""
        ci = self._make_ci(date(2025, 6, 15))

        with patch.object(
            ci, "get_weather_context", new_callable=AsyncMock, side_effect=Exception("network error")
        ):
            ctx = await ci.get_temporal_context(
                brand_locations=["Paris"],
                brand_niche="restaurant",
            )

        # Should still return context without weather
        assert "CONTEXTE TEMPOREL" in ctx
