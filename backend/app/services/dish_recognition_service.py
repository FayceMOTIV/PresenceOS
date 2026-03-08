"""
PresenceOS — Dish Recognition Service (Gemini 2.0 Flash Vision)

Analyzes food photos to identify dish name, category, and description.
Used in the upload flow to auto-tag photos with dish information.
"""

import base64
import json
from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Gemini model for vision tasks (fast + cheap)
GEMINI_MODEL = "gemini-2.0-flash"


class DishRecognitionResult:
    """Result of a dish recognition analysis."""

    def __init__(
        self,
        dish_name: str,
        category: str,
        description: str,
        confidence: float,
        tags: list[str] | None = None,
    ):
        self.dish_name = dish_name
        self.category = category
        self.description = description
        self.confidence = confidence
        self.tags = tags or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "dish_name": self.dish_name,
            "category": self.category,
            "description": self.description,
            "confidence": self.confidence,
            "tags": self.tags,
        }


class DishRecognitionService:
    """Identifies dishes from food photos using Gemini 2.0 Flash Vision."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not settings.gemini_api_key:
            raise RuntimeError(
                "Gemini API key not configured. Set GEMINI_API_KEY in environment."
            )

        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        self._client = genai.GenerativeModel(GEMINI_MODEL)
        return self._client

    async def recognize(self, image_bytes: bytes) -> DishRecognitionResult:
        """
        Analyze a food photo and return dish information.

        Args:
            image_bytes: Raw image bytes (JPEG or PNG).

        Returns:
            DishRecognitionResult with dish_name, category, description, confidence.
        """
        import asyncio

        model = self._get_client()

        prompt = """Analyse cette photo de nourriture/plat et réponds en JSON strict :
{
  "dish_name": "<nom du plat en français, ex: 'Tartare de saumon'>",
  "category": "<une parmi: entrée, plat, dessert, boisson, snack, brunch, apéritif>",
  "description": "<description courte en 1 phrase pour un post Instagram>",
  "confidence": <float 0.0-1.0>,
  "tags": ["<tag1>", "<tag2>", ...]
}

Si ce n'est pas de la nourriture, retourne :
{"dish_name": "inconnu", "category": "autre", "description": "Photo non alimentaire", "confidence": 0.0, "tags": []}

Réponds UNIQUEMENT en JSON, pas de texte autour."""

        def _sync_call() -> dict:
            response = model.generate_content(
                [
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_bytes},
                ],
                generation_config={"temperature": 0.2, "max_output_tokens": 512},
            )
            raw = response.text.strip()

            # Extract JSON from response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON in Gemini response")
            return json.loads(raw[start:end])

        result = await asyncio.to_thread(_sync_call)

        return DishRecognitionResult(
            dish_name=result.get("dish_name", "inconnu"),
            category=result.get("category", "plat"),
            description=result.get("description", ""),
            confidence=float(result.get("confidence", 0.0)),
            tags=result.get("tags", []),
        )
