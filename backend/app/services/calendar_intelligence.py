"""
PresenceOS - Calendar Intelligence Service (F1: Conscience Temporelle)

Provides temporal awareness for the CM Chat: French holidays, Islamic events,
weather context via Open-Meteo API, and seasonal opportunity detection.

Zero additional cost: Open-Meteo is free, Nominatim is free (OpenStreetMap).
"""
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── French Fixed Holidays ─────────────────────────────────────────────────────

FRENCH_HOLIDAYS: dict[tuple[int, int], str] = {
    (1, 1): "Jour de l'An",
    (5, 1): "Fête du Travail",
    (5, 8): "Victoire 1945",
    (6, 21): "Fête de la Musique",
    (7, 14): "Fête Nationale",
    (8, 15): "Assomption",
    (11, 1): "Toussaint",
    (11, 11): "Armistice",
    (12, 25): "Noël",
    (12, 31): "Saint-Sylvestre / Réveillon",
    (2, 14): "Saint-Valentin",
    (10, 31): "Halloween",
}

# ── Mobile French Holidays (computed) ─────────────────────────────────────────

def _easter_date(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _get_mobile_french_holidays(year: int) -> dict[date, str]:
    """Return mobile French holidays for a given year."""
    easter = _easter_date(year)
    holidays: dict[date, str] = {
        easter: "Pâques",
        easter + timedelta(days=1): "Lundi de Pâques",
        easter + timedelta(days=39): "Ascension",
        easter + timedelta(days=49): "Pentecôte",
        easter + timedelta(days=50): "Lundi de Pentecôte",
    }

    # Fête des Mères: last Sunday of May, unless it collides with Pentecôte
    # then first Sunday of June
    last_may = date(year, 5, 31)
    while last_may.weekday() != 6:  # 6 = Sunday
        last_may -= timedelta(days=1)
    pentecote = easter + timedelta(days=49)
    if last_may == pentecote:
        fete_meres = last_may + timedelta(days=7)
    else:
        fete_meres = last_may
    holidays[fete_meres] = "Fête des Mères"

    # Fête des Pères: 3rd Sunday of June
    june_1 = date(year, 6, 1)
    first_sunday = june_1 + timedelta(days=(6 - june_1.weekday()) % 7)
    fete_peres = first_sunday + timedelta(weeks=2)
    holidays[fete_peres] = "Fête des Pères"

    return holidays


# ── Islamic Calendar Events (year-specific approximations) ────────────────────
# These are approximate Gregorian dates for Islamic events.
# Updated yearly based on astronomical observations.

ISLAMIC_EVENTS: dict[int, list[tuple[date, date, str]]] = {
    2025: [
        (date(2025, 2, 28), date(2025, 3, 30), "Ramadan"),
        (date(2025, 3, 30), date(2025, 4, 1), "Aïd el-Fitr"),
        (date(2025, 6, 6), date(2025, 6, 8), "Aïd el-Adha"),
    ],
    2026: [
        (date(2026, 2, 17), date(2026, 3, 19), "Ramadan"),
        (date(2026, 3, 19), date(2026, 3, 21), "Aïd el-Fitr"),
        (date(2026, 5, 26), date(2026, 5, 28), "Aïd el-Adha"),
    ],
    2027: [
        (date(2027, 2, 7), date(2027, 3, 9), "Ramadan"),
        (date(2027, 3, 9), date(2027, 3, 11), "Aïd el-Fitr"),
        (date(2027, 5, 16), date(2027, 5, 18), "Aïd el-Adha"),
    ],
}

# ── Commercial Seasons ────────────────────────────────────────────────────────

COMMERCIAL_SEASONS: list[dict[str, Any]] = [
    {"name": "Soldes d'hiver", "start_month": 1, "start_day": 8, "end_month": 2, "end_day": 4},
    {"name": "Soldes d'été", "start_month": 6, "start_day": 26, "end_month": 7, "end_day": 23},
    {"name": "Black Friday", "start_month": 11, "start_day": 25, "end_month": 11, "end_day": 30},
    {"name": "Rentrée scolaire", "start_month": 9, "start_day": 1, "end_month": 9, "end_day": 15},
    {"name": "Terrasses d'été", "start_month": 5, "start_day": 15, "end_month": 9, "end_day": 30},
]


# ── Weather via Open-Meteo (free, no API key) ────────────────────────────────

async def _geocode_city(city: str) -> tuple[float, float] | None:
    """Geocode a city name to (lat, lon) using Nominatim (free, OSM)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": city, "format": "json", "limit": 1},
                headers={"User-Agent": "PresenceOS/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as exc:
        logger.warning("Geocoding failed for %s: %s", city, exc)
    return None


async def _fetch_weather(lat: float, lon: float) -> dict[str, Any] | None:
    """Fetch current weather from Open-Meteo (free, no key)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": "true",
                    "timezone": "Europe/Paris",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("current_weather")
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
    return None


# Weather code mapping (WMO codes to French descriptions)
_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "ciel dégagé ☀️",
    1: "principalement dégagé 🌤",
    2: "partiellement nuageux ⛅",
    3: "couvert ☁️",
    45: "brouillard 🌫",
    48: "brouillard givrant 🌫",
    51: "bruine légère 🌦",
    53: "bruine modérée 🌦",
    55: "bruine forte 🌧",
    61: "pluie légère 🌧",
    63: "pluie modérée 🌧",
    65: "pluie forte 🌧",
    71: "neige légère 🌨",
    73: "neige modérée 🌨",
    75: "neige forte 🌨",
    80: "averses légères 🌦",
    81: "averses modérées 🌧",
    82: "averses violentes ⛈",
    95: "orage ⛈",
    96: "orage avec grêle ⛈",
    99: "orage violent avec grêle ⛈",
}


def _describe_weather(weather: dict[str, Any]) -> str:
    """Convert Open-Meteo current_weather to French text."""
    temp = weather.get("temperature", "?")
    code = weather.get("weathercode", -1)
    desc = _WMO_DESCRIPTIONS.get(code, "conditions inconnues")
    wind = weather.get("windspeed", 0)
    parts = [f"{temp}°C, {desc}"]
    if wind and wind > 30:
        parts.append(f"vent fort ({wind} km/h)")
    return " — ".join(parts)


# ── Main Service ──────────────────────────────────────────────────────────────

class CalendarIntelligence:
    """Builds temporal context for the CM Chat system prompt."""

    def __init__(self, default_timezone: str = "Europe/Paris"):
        self.tz_name = default_timezone

    def _get_today(self) -> date:
        """Get today's date (mockable for tests)."""
        return date.today()

    def get_upcoming_events(self, days_ahead: int = 14) -> list[dict[str, Any]]:
        """Return holidays and events within the next N days."""
        today = self._get_today()
        end = today + timedelta(days=days_ahead)
        events: list[dict[str, Any]] = []

        year = today.year

        # Fixed French holidays
        for (m, d), name in FRENCH_HOLIDAYS.items():
            try:
                dt = date(year, m, d)
            except ValueError:
                continue
            if today <= dt <= end:
                delta = (dt - today).days
                events.append({
                    "name": name,
                    "date": dt.isoformat(),
                    "days_until": delta,
                    "type": "holiday",
                })

        # Mobile French holidays (Easter-based)
        for dt, name in _get_mobile_french_holidays(year).items():
            if today <= dt <= end:
                delta = (dt - today).days
                events.append({
                    "name": name,
                    "date": dt.isoformat(),
                    "days_until": delta,
                    "type": "holiday",
                })

        # Islamic events
        for yr in (year, year + 1):
            for start, end_dt, name in ISLAMIC_EVENTS.get(yr, []):
                if today <= start <= end or today <= end_dt <= end:
                    delta = max(0, (start - today).days)
                    events.append({
                        "name": name,
                        "date": start.isoformat(),
                        "days_until": delta,
                        "type": "islamic",
                    })

        # Commercial seasons
        for season in COMMERCIAL_SEASONS:
            try:
                s_start = date(year, season["start_month"], season["start_day"])
                s_end = date(year, season["end_month"], season["end_day"])
            except ValueError:
                continue
            if s_start <= today <= s_end:
                events.append({
                    "name": f"{season['name']} (en cours)",
                    "date": s_start.isoformat(),
                    "days_until": 0,
                    "type": "commercial",
                })
            elif today <= s_start <= end:
                delta = (s_start - today).days
                events.append({
                    "name": season["name"],
                    "date": s_start.isoformat(),
                    "days_until": delta,
                    "type": "commercial",
                })

        events.sort(key=lambda e: e["days_until"])
        return events

    async def get_weather_context(self, locations: list[str] | None) -> str | None:
        """Fetch weather for the first city in locations."""
        if not locations:
            return None

        # Extract city name (e.g., "Paris 15e" -> "Paris")
        city = locations[0].split()[0] if locations else None
        if not city:
            return None

        coords = await _geocode_city(city)
        if not coords:
            return None

        weather = await _fetch_weather(coords[0], coords[1])
        if not weather:
            return None

        return f"Météo actuelle à {city} : {_describe_weather(weather)}"

    async def get_temporal_context(
        self,
        brand_locations: list[str] | None = None,
        brand_niche: str | None = None,
        brand_constraints: dict | None = None,
    ) -> str:
        """
        Build the full temporal context block for injection into the CM Chat
        system prompt. Returns a formatted string ready for concatenation.

        Args:
            brand_locations: Brand.locations (e.g., ["Paris 15e"])
            brand_niche: Brand.niche (e.g., "restaurant")
            brand_constraints: Brand.constraints (e.g., {"halal": true})
        """
        today = self._get_today()
        now = datetime.now(timezone.utc)

        lines: list[str] = []
        lines.append("CONTEXTE TEMPOREL :")
        lines.append(f"Date : {today.strftime('%A %d %B %Y').capitalize()} (semaine {today.isocalendar()[1]})")
        lines.append(f"Heure (Paris) : ~{(now.hour + 1) % 24}h")  # UTC+1 approx

        # Day part for content timing hints
        hour_paris = (now.hour + 1) % 24
        if 6 <= hour_paris < 12:
            lines.append("Moment : Matin — idéal pour un post petit-déjeuner / motivation")
        elif 12 <= hour_paris < 14:
            lines.append("Moment : Déjeuner — idéal pour un post menu du jour / offre midi")
        elif 14 <= hour_paris < 18:
            lines.append("Moment : Après-midi — idéal pour un post teasing soirée / conseil")
        elif 18 <= hour_paris < 22:
            lines.append("Moment : Soirée — idéal pour un post ambiance / événement")
        else:
            lines.append("Moment : Nuit — préparer les contenus de demain")

        # Upcoming events
        events = self.get_upcoming_events(days_ahead=14)
        if events:
            lines.append("")
            lines.append("ÉVÉNEMENTS À VENIR :")
            is_halal = (brand_constraints or {}).get("halal", False)
            for ev in events[:8]:  # Max 8 events
                # Skip Islamic events for non-halal brands (relevance filter)
                if ev["type"] == "islamic" and not is_halal:
                    continue
                if ev["days_until"] == 0:
                    lines.append(f"  🔴 AUJOURD'HUI : {ev['name']}")
                elif ev["days_until"] <= 3:
                    lines.append(f"  🟡 Dans {ev['days_until']}j : {ev['name']} ({ev['date']})")
                else:
                    lines.append(f"  📅 Dans {ev['days_until']}j : {ev['name']} ({ev['date']})")

        # Weather
        try:
            weather = await self.get_weather_context(brand_locations)
            if weather:
                lines.append("")
                lines.append(weather)
                # Content opportunity based on weather
                lines.append("→ Adapte tes propositions à la météo (terrasse si beau temps, plats réconfortants si froid/pluie)")
        except Exception:
            pass  # Weather is optional — never block on it

        # Seasonal hints based on niche
        niche = (brand_niche or "").lower()
        month = today.month
        if niche in ("restaurant", "food", "boulangerie", "pâtisserie", "traiteur"):
            if month in (1, 2):
                lines.append("🍽 Saison : plats d'hiver, galette des rois (janvier), chandeleur (février)")
            elif month in (3, 4, 5):
                lines.append("🍽 Saison : produits de printemps, asperges, fraises, terrasses qui ouvrent")
            elif month in (6, 7, 8):
                lines.append("🍽 Saison : été, salades, glaces, cocktails, terrasse")
            elif month in (9, 10):
                lines.append("🍽 Saison : rentrée, plats réconfortants, champignons, courges")
            elif month in (11, 12):
                lines.append("🍽 Saison : fêtes de fin d'année, menu de Noël, réveillon")

        return "\n".join(lines)
