"""
PresenceOS - Instruction Parser (Sprint 9B)

Parses natural language instructions from WhatsApp messages or voice transcriptions
to extract: platform targets, posting time, caption directives, hashtag preferences.
Uses AI to understand user intent.
"""
import json
import structlog
from typing import Any

from app.services.ai_service import AIService

logger = structlog.get_logger()

PARSE_PROMPT = """Tu es un assistant qui analyse les instructions de publication
sur les reseaux sociaux. L'utilisateur envoie un message (texte ou transcription vocale)
qui decrit ce qu'il veut publier.

Extrais les informations suivantes du message:

1. **platforms**: Sur quelles plateformes publier (instagram, linkedin, tiktok, facebook).
   Si non mentionne, utilise ["instagram"].
2. **caption_directive**: Ce que l'utilisateur veut comme legende/caption. Peut etre un theme,
   des mots-cles, ou une caption complete.
3. **posting_time**: Quand publier (ex: "maintenant", "demain 10h", "ce soir").
   null si non mentionne.
4. **hashtags**: Hashtags demandes ou preferences hashtags. null si non mentionne.
5. **tone**: Ton souhaite (ex: "professionnel", "fun", "inspirant"). null si non mentionne.
6. **is_ready_to_publish**: true si l'utilisateur veut publier immediatement,
   false s'il veut un brouillon/preview.
7. **additional_notes**: Toute autre instruction pertinente.

Message de l'utilisateur:
{message}

Reponds UNIQUEMENT en JSON valide:
{{
  "platforms": ["instagram"],
  "caption_directive": "...",
  "posting_time": null,
  "hashtags": null,
  "tone": null,
  "is_ready_to_publish": false,
  "additional_notes": null
}}"""


class InstructionParser:
    """Parse natural language instructions into structured post directives."""

    def __init__(self):
        self.ai = AIService()

    async def parse(self, message: str) -> dict[str, Any]:
        """
        Parse a natural language message into structured instructions.

        Args:
            message: Text from WhatsApp message or voice transcription

        Returns:
            Parsed instructions dict
        """
        if not message or not message.strip():
            return self._default_instructions()

        prompt = PARSE_PROMPT.format(message=message)

        try:
            raw = await self.ai._complete(
                prompt=prompt,
                system="Tu es un parseur d'instructions. Reponds uniquement en JSON valide.",
                max_tokens=500,
                temperature=0.2,
            )

            result = self.ai._parse_json_response(raw)

            # Normalize platforms
            if "platforms" in result:
                result["platforms"] = [
                    p.lower().strip() for p in result["platforms"]
                    if p.lower().strip() in ("instagram", "linkedin", "tiktok", "facebook")
                ]
                if not result["platforms"]:
                    result["platforms"] = ["instagram"]

            logger.info("Instructions parsed", platforms=result.get("platforms"))
            return result

        except Exception as e:
            logger.error("Instruction parsing failed", error=str(e))
            return self._default_instructions(caption_directive=message)

    def _default_instructions(self, caption_directive: str | None = None) -> dict:
        """Return default instructions when parsing fails."""
        return {
            "platforms": ["instagram"],
            "caption_directive": caption_directive,
            "posting_time": None,
            "hashtags": None,
            "tone": None,
            "is_ready_to_publish": False,
            "additional_notes": None,
        }
