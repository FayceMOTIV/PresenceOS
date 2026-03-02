# PresenceOS — Reply Generator (Sprint 5: Engager)
# Uses Claude Sonnet for quality reply generation with Brand DNA context

from __future__ import annotations

import logging

import anthropic

from app.core.config import settings
from app.models.comment import Comment
from app.models.business_dna import BusinessDNA
from app.services.firebase_firestore import FirestoreService

logger = logging.getLogger(__name__)

REPLY_SYSTEM_PROMPT = """Tu es Ilyas, le community manager IA de ce commerce.
Tu rediges des reponses aux commentaires sur les reseaux sociaux.

REGLES :
- Ton chaleureux et professionnel, adapte a la marque
- Reponse courte (1 a 3 phrases max)
- Tutoiement ou vouvoiement selon le ton de la marque
- Si commentaire negatif → empathie + solution concrete
- Si question → reponse directe et utile
- Si positif → remerciement sincere (pas generique)
- Jamais de hashtags dans les reponses
- Jamais d'emoji excessif (1-2 max)
- Signe avec le prenom du commerce si pertinent

{dna_context}"""

REPLY_USER_PROMPT = """Commentaire a traiter :
Plateforme: {platform}
Auteur: {author}
Sentiment: {sentiment} (urgence: {urgency}/10)
Texte: "{text}"

Redige une reponse naturelle et adaptee."""


class ReplyGenerator:
    """Generates brand-voice replies using Claude Sonnet + Brand DNA."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None
        self._firestore = FirestoreService()

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    async def _get_dna_context(self, brand_id: str) -> str:
        """Load Brand DNA from Firestore for system prompt injection."""
        try:
            data = await self._firestore.get_subcollection_doc(
                "businesses", brand_id, "dna", "profile"
            )
            if data:
                dna = BusinessDNA.from_dict(data)
                if dna.onboarding_complete:
                    return dna.to_system_prompt_section()
        except Exception as exc:
            logger.debug("DNA load failed for reply gen", extra={"error": str(exc)})
        return ""

    async def generate_reply(self, comment: Comment) -> Comment:
        """Generate a reply for a classified comment. Returns comment with suggested_reply."""
        if comment.reply_status == "skipped":
            return comment

        try:
            client = self._get_client()
            dna_context = await self._get_dna_context(comment.brand_id)

            system = REPLY_SYSTEM_PROMPT.format(dna_context=dna_context)
            user_msg = REPLY_USER_PROMPT.format(
                platform=comment.platform,
                author=comment.author_name,
                sentiment=comment.sentiment,
                urgency=comment.urgency_score,
                text=comment.text,
            )

            response = client.messages.create(
                model=settings.ilyas_model,
                max_tokens=300,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )

            reply = response.content[0].text.strip()
            # Strip quotes if Sonnet wraps the reply
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1]

            comment.suggested_reply = reply
            comment.reply_status = "classified"

            logger.info(
                "Reply generated",
                extra={
                    "comment_id": comment.id,
                    "reply_length": len(reply),
                },
            )

        except Exception as exc:
            logger.error(
                "Reply generation failed",
                extra={"error": str(exc), "comment_id": comment.id},
            )
            comment.suggested_reply = ""

        return comment

    async def generate_replies_batch(self, comments: list[Comment]) -> list[Comment]:
        """Generate replies for a batch of classified comments."""
        results: list[Comment] = []
        for comment in comments:
            result = await self.generate_reply(comment)
            results.append(result)
        return results
