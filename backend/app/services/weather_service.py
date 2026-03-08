"""
PresenceOS — Weather Service (Open-Meteo)

Free API, no key required.
Geocodes brand location text → lat/lon → current weather.
Injects weather context into Ilyas system prompt.
"""

import json
from datetime import datetime, timezone

import httpx
import structlog

logger = structlog.get_logger()

# Open-Meteo endpoints (free, no API key)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather code → French description
WMO_CODES: dict[int, str] = {
    0: "ciel dégagé",
    1: "principalement dégagé",
    2: "partiellement nuageux",
    3: "couvert",
    45: "brouillard",
    48: "brouillard givrant",
    51: "bruine légère",
    53: "bruine modérée",
    55: "bruine forte",
    61: "pluie légère",
    63: "pluie modérée",
    65: "pluie forte",
    66: "pluie verglaçante légère",
    67: "pluie verglaçante forte",
    71: "neige légère",
    73: "neige modérée",
    75: "neige forte",
    80: "averses légères",
    81: "averses modérées",
    82: "averses violentes",
    85: "averses de neige légères",
    86: "averses de neige fortes",
    95: "orage",
    96: "orage avec grêle légère",
    99: "orage avec grêle forte",
}


class WeatherService:
    """Fetches current weather from Open-Meteo for a brand location."""

    def __init__(self) -> None:
        self._geocode_cache: dict[str, tuple[float, float] | None] = {}

    async def _geocode(self, location_text: str) -> tuple[float, float] | None:
        """Geocode a location string to (latitude, longitude) via Open-Meteo."""
        if location_text in self._geocode_cache:
            return self._geocode_cache[location_text]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    GEOCODE_URL,
                    params={"name": location_text, "count": 1, "language": "fr"},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    self._geocode_cache[location_text] = None
                    return None

                lat = results[0]["latitude"]
                lon = results[0]["longitude"]
                self._geocode_cache[location_text] = (lat, lon)
                return (lat, lon)
        except Exception as exc:
            logger.warning("Geocoding failed", location=location_text, error=str(exc))
            self._geocode_cache[location_text] = None
            return None

    async def get_current_weather(
        self, locations: list[str] | None
    ) -> str | None:
        """
        Fetch current weather for the first brand location.

        Returns a formatted string for the Ilyas system prompt, or None.
        """
        if not locations:
            return None

        # Try the first location
        coords = await self._geocode(locations[0])
        if not coords:
            return None

        lat, lon = coords

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    WEATHER_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "temperature_2m,weather_code,wind_speed_10m",
                        "timezone": "Europe/Paris",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("Weather fetch failed", error=str(exc))
            return None

        current = data.get("current", {})
        temp = current.get("temperature_2m")
        code = current.get("weather_code")
        wind = current.get("wind_speed_10m")

        if temp is None:
            return None

        description = WMO_CODES.get(code, "conditions inconnues")
        wind_str = f", vent {wind:.0f} km/h" if wind else ""

        now = datetime.now(timezone.utc)
        hour = now.hour + 1  # rough CET offset

        return (
            f"MÉTÉO ACTUELLE ({locations[0]}) : "
            f"{temp:.0f}°C, {description}{wind_str}. "
            f"Adapte tes suggestions de contenu à la météo "
            f"(terrasse si beau, plats réconfortants si froid/pluie)."
        )
