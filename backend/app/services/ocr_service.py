"""
PresenceOS - OCR Service (Content Library)

Extracts menu items from paper menu photos using Claude Vision.
Returns structured dish data for user validation before import.
"""
import base64
import json
from typing import Any

import anthropic
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class OCRService:
    """Menu OCR using Claude Vision (Anthropic)."""

    HAIKU_MODEL = "claude-haiku-4-5-20251001"
    SONNET_MODEL = "claude-sonnet-4-6"

    def __init__(self) -> None:
        self._client: anthropic.AsyncAnthropic | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError(
                    "Anthropic API key is not configured. "
                    "Set ANTHROPIC_API_KEY in your environment."
                )
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def scan_menu_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> list[dict[str, Any]]:
        """Extract dishes from a menu photo using Claude Vision.

        Returns a list of structured dish data:
        [
            {
                "name": "Entrecôte grillée",
                "category": "plats",
                "price": 24.90,
                "description": "Servie avec frites maison et sauce béarnaise"
            },
            ...
        ]
        """
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """Analyse cette photo de carte/menu de restaurant.

Extrais TOUS les plats visibles avec leurs informations.

Réponds en JSON strict — un tableau de plats :
[
  {
    "name": "Nom du plat",
    "category": "entrees|plats|desserts|boissons|autres",
    "price": 12.90,
    "description": "Description courte si visible, sinon null"
  }
]

Règles :
- Catégories autorisées : "entrees", "plats", "desserts", "boissons", "autres"
- Le prix doit être un nombre décimal (12.90), pas une string. Si pas visible, mettre null.
- Si la description n'est pas lisible, mettre null.
- Inclure TOUS les items visibles, même partiellement.
- Si le texte est flou ou illisible, faire ton meilleur effort.
- Répondre UNIQUEMENT avec le tableau JSON, pas de texte autour."""

        client = self._get_client()

        try:
            # Use Sonnet for better OCR accuracy on menu photos
            response = await client.messages.create(
                model=self.SONNET_MODEL,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            raw = response.content[0].text
            dishes = self._parse_dishes_json(raw)

            logger.info("Menu OCR completed", dish_count=len(dishes))
            return dishes

        except Exception as exc:
            logger.error("Menu OCR failed", error=str(exc))
            raise

    def _parse_dishes_json(self, text: str) -> list[dict[str, Any]]:
        """Parse and validate the JSON array of dishes from LLM response."""
        # Find JSON array in response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in OCR response")

        raw_dishes = json.loads(text[start:end])

        valid_categories = {"entrees", "plats", "desserts", "boissons", "autres"}
        cleaned = []

        for item in raw_dishes:
            if not isinstance(item, dict) or not item.get("name"):
                continue

            category = str(item.get("category", "autres")).lower().strip()
            if category not in valid_categories:
                category = "autres"

            price = item.get("price")
            if price is not None:
                try:
                    price = round(float(price), 2)
                except (ValueError, TypeError):
                    price = None

            cleaned.append({
                "name": str(item["name"]).strip(),
                "category": category,
                "price": price,
                "description": str(item["description"]).strip() if item.get("description") else None,
            })

        return cleaned
