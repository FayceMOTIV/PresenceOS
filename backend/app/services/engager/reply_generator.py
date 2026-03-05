# PresenceOS — Reply Generator (Sprint 5: Engager)
# Uses GPT-4o for quality reply generation with Brand DNA context

from __future__ import annotations

import logging

from openai import OpenAI

from app.core.config import settings
from app.models.comment import Comment
from app.models.business_dna import BusinessDNA
from app.services.firebase_firestore import FirestoreService

logger = logging.getLogger(__name__)

REPLY_SYSTEM_PROMPT = """Tu es le community manager IA de ce commerce local.
Tu rédiges des réponses aux commentaires sur les réseaux sociaux.

REGLES :
- Ton chaleureux et professionnel, adapté à la marque
- Réponse courte : 1 à 3 phrases maximum
- Tutoiement ou vouvoiement selon le ton de la marque (défaut: vouvoiement)
- Mentionne le prénom de l'auteur quand il est disponible
- Référence un détail spécifique du commentaire (ne pas faire de réponse générique)
- Réponds dans la même langue que le commentaire
- Maximum 1-2 emojis, jamais de hashtags

PAR TYPE DE COMMENTAIRE :
- Positif → remerciement sincère et personnalisé, invitation à revenir
- Négatif → empathie + proposition concrète (ex: "contactez-nous en DM pour qu'on arrange ça")
- Question → réponse directe et utile, avec une info supplémentaire si pertinent
- Urgent (score >= 7) → empathie forte + redirection vers DM ou téléphone pour suivi rapide

INTERDICTIONS ABSOLUES :
- Ne JAMAIS promettre de remise, geste commercial ou compensation
- Ne JAMAIS confirmer un fait non vérifié (horaires précis, disponibilité plat)
- Ne JAMAIS minimiser un problème d'hygiène ou de santé
- Ne JAMAIS utiliser un ton sarcastique ou défensif face à une critique
- Ne JAMAIS signer avec un prénom fictif — signer "L'équipe [nom du commerce]" si DNA disponible

EXEMPLES DE BONNES REPONSES :
Commentaire: "Le burger était incroyable, bravo !" (positif)
→ "Merci beaucoup Marie, ça nous fait super plaisir ! On espère vous revoir bientôt 😊"

Commentaire: "45 min d'attente pour un café, c'est abusé" (négatif, urgence 7)
→ "On comprend votre frustration Thomas, ce n'est pas notre standard. Envoyez-nous un DM pour qu'on en discute et qu'on se rattrape."

Commentaire: "Vous faites des plats végé ?" (question)
→ "Oui bien sûr ! On a plusieurs options végétariennes sur notre carte. N'hésitez pas à demander au serveur 😊"

{dna_context}"""

REPLY_USER_PROMPT = """Commentaire à traiter :
Plateforme: {platform}
Auteur: {author}
Langue détectée: {language}
Sentiment: {sentiment} (urgence: {urgency}/10)
Texte: "{text}"

Rédige une réponse naturelle et adaptée."""


class ReplyGenerator:
    """Generates brand-voice replies using GPT-4o + Brand DNA."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None
        self._firestore = FirestoreService()

    def _get_client(self) -> OpenAI:
        if self._client is None:
            api_key = settings.openai_api_key
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not configured")
            self._client = OpenAI(api_key=api_key)
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
                language=getattr(comment, "language", "fr"),
                sentiment=comment.sentiment,
                urgency=comment.urgency_score,
                text=comment.text,
            )

            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
            )

            reply = response.choices[0].message.content.strip()
            # Strip quotes if GPT wraps the reply
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
