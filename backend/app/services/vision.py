"""
PresenceOS - Vision AI Service (Sprint 9B)

Analyzes images using OpenAI GPT-4 Vision or Anthropic Claude Vision
to generate descriptions, tags, and suggest captions.
"""
import base64
import json
import structlog
from typing import Any

import openai
import anthropic

from app.core.config import settings

logger = structlog.get_logger()


class VisionService:
    """Analyze images using AI vision models."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.ai_provider

        if self.provider == "openai":
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            self.model_name = "gpt-4o"
        else:
            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model_name = settings.anthropic_model

    async def analyze_image(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        brand_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze an image and return description, tags, and caption suggestions.

        Returns:
            {
                "description": str,
                "tags": list[str],
                "suggested_caption": str,
                "detected_objects": list[str],
                "mood": str,
                "suitable_platforms": list[str],
            }
        """
        b64_image = base64.b64encode(image_data).decode("utf-8")

        system_prompt = "Tu es un expert en marketing visuel et creation de contenu pour les reseaux sociaux."

        brand_hint = ""
        if brand_context:
            brand_hint = f"\n\nContexte de la marque: {brand_context}"

        user_prompt = f"""Analyse cette image pour une utilisation marketing sur les reseaux sociaux.{brand_hint}

Reponds en JSON:
{{
  "description": "Description detaillee de l'image (2-3 phrases)",
  "tags": ["tag1", "tag2", "tag3", ...],
  "suggested_caption": "Caption Instagram engageante basee sur l'image",
  "detected_objects": ["objet1", "objet2", ...],
  "mood": "mood general (ex: chaleureux, professionnel, fun, appetissant)",
  "suitable_platforms": ["instagram", "linkedin", ...]
}}"""

        try:
            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{b64_image}",
                                        "detail": "high",
                                    },
                                },
                            ],
                        },
                    ],
                    max_tokens=1000,
                    temperature=0.5,
                )
                raw = response.choices[0].message.content

            else:  # anthropic
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": b64_image,
                                    },
                                },
                                {"type": "text", "text": user_prompt},
                            ],
                        }
                    ],
                )
                raw = response.content[0].text

            return self._parse_json(raw)

        except Exception as e:
            logger.error("Vision analysis failed", error=str(e))
            return {
                "description": "Analyse non disponible",
                "tags": [],
                "suggested_caption": "",
                "detected_objects": [],
                "mood": "unknown",
                "suitable_platforms": ["instagram"],
            }

    async def analyze_image_from_url(
        self,
        image_url: str,
        brand_context: str | None = None,
    ) -> dict[str, Any]:
        """Analyze an image from a URL (OpenAI only)."""
        if self.provider != "openai":
            # For Anthropic, download the image first
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url, timeout=30.0)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "image/jpeg")
                return await self.analyze_image(resp.content, content_type, brand_context)

        system_prompt = "Tu es un expert en marketing visuel et creation de contenu pour les reseaux sociaux."

        brand_hint = ""
        if brand_context:
            brand_hint = f"\n\nContexte de la marque: {brand_context}"

        user_prompt = f"""Analyse cette image pour une utilisation marketing sur les reseaux sociaux.{brand_hint}

Reponds en JSON:
{{
  "description": "Description detaillee de l'image (2-3 phrases)",
  "tags": ["tag1", "tag2", "tag3", ...],
  "suggested_caption": "Caption Instagram engageante basee sur l'image",
  "detected_objects": ["objet1", "objet2", ...],
  "mood": "mood general",
  "suitable_platforms": ["instagram", "linkedin", ...]
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url, "detail": "high"},
                            },
                        ],
                    },
                ],
                max_tokens=1000,
                temperature=0.5,
            )
            raw = response.choices[0].message.content
            return self._parse_json(raw)

        except Exception as e:
            logger.error("Vision URL analysis failed", error=str(e))
            return {
                "description": "Analyse non disponible",
                "tags": [],
                "suggested_caption": "",
                "detected_objects": [],
                "mood": "unknown",
                "suitable_platforms": ["instagram"],
            }

    def _parse_json(self, text: str) -> dict:
        """Extract JSON from response text."""
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")
        return json.loads(text[start:end])
