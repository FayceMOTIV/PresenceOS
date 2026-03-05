# PresenceOS — Comment Classifier (Sprint 5: Engager)
# Uses GPT-4o-mini for fast, cheap sentiment classification + urgency scoring

from __future__ import annotations

import json
import logging

from openai import OpenAI

from app.core.config import settings
from app.models.comment import Comment

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """Tu es un classificateur de commentaires pour un commerce local (restaurant, café, boulangerie).

Analyse ce commentaire et retourne un JSON strict :
{{
  "sentiment": "<positive|negative|question|spam|neutral>",
  "urgency_score": <float 0.0-10.0>,
  "topics": [<liste parmi: service, nourriture, prix, hygiene, horaires, livraison, reservation, ambiance, personnel, menu, autre>],
  "needs_reply": <bool>,
  "language": "<fr|en|ar|es|autre>"
}}

REGLES DE CLASSIFICATION :
- "positive" = compliment, recommandation, satisfaction
- "negative" = plainte, déception, critique
- "question" = demande d'information (horaires, menu, livraison, réservation)
- "spam" = publicité, bots, liens suspects, promotions tierces
- "neutral" = emoji seul, tag sans texte, commentaire factuel sans émotion

REGLES D'URGENCE (urgency_score) :
- 9-10 : crise sanitaire (intoxication, allergène, corps étranger), menace légale
- 7-8 : plainte grave (attente excessive, commande incorrecte, hygiène), réservation urgente non confirmée
- 5-6 : question pressante, retour négatif modéré
- 3-4 : question standard, retour mitigé
- 1-2 : commentaire positif, remarque neutre
- 0 : spam, emoji seul, tag sans contexte

REGLES needs_reply :
- false : spam, emoji seul (🔥❤️👍 sans texte), tags sans message, commentaire de bot
- true : tout le reste

EXEMPLES :
Commentaire: "J'ai attendu 1h pour ma pizza, c'est inadmissible"
→ {{"sentiment": "negative", "urgency_score": 7.5, "topics": ["service"], "needs_reply": true, "language": "fr"}}

Commentaire: "🔥🔥🔥"
→ {{"sentiment": "neutral", "urgency_score": 0.0, "topics": [], "needs_reply": false, "language": "fr"}}

Commentaire: "Vous êtes ouverts le dimanche ?"
→ {{"sentiment": "question", "urgency_score": 3.0, "topics": ["horaires"], "needs_reply": true, "language": "fr"}}

Commentaire: "ALERTE : cheveu trouvé dans la salade, j'ai des photos"
→ {{"sentiment": "negative", "urgency_score": 9.0, "topics": ["hygiene", "nourriture"], "needs_reply": true, "language": "fr"}}

---
Commentaire a analyser :
Plateforme: {platform}
Auteur: {author}
Texte: \"{text}\""""


class CommentClassifier:
    """Classifies comments using GPT-4o-mini for speed and cost efficiency."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            api_key = settings.openai_api_key
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not configured")
            self._client = OpenAI(api_key=api_key)
        return self._client

    async def classify(self, comment: Comment) -> Comment:
        """Classify a single comment. Returns the comment with updated fields."""
        try:
            client = self._get_client()
            prompt = CLASSIFIER_PROMPT.format(
                platform=comment.platform,
                author=comment.author_name,
                text=comment.text,
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=256,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Tu retournes uniquement du JSON valide."},
                    {"role": "user", "content": prompt},
                ],
            )

            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)

            comment.sentiment = result.get("sentiment", "neutral")
            comment.urgency_score = float(result.get("urgency_score", 0))
            comment.topics = result.get("topics", [])
            comment.language = result.get("language", "fr")

            needs_reply = result.get("needs_reply", True)
            if not needs_reply:
                comment.reply_status = "skipped"
            else:
                comment.reply_status = "classified"

            logger.info(
                "Comment classified",
                extra={
                    "comment_id": comment.id,
                    "sentiment": comment.sentiment,
                    "urgency": comment.urgency_score,
                },
            )

        except json.JSONDecodeError as exc:
            logger.warning(
                "Classifier JSON parse failed, defaulting to neutral",
                extra={"error": str(exc), "comment_id": comment.id},
            )
            comment.sentiment = "neutral"
            comment.urgency_score = 5.0
            comment.reply_status = "classified"

        except Exception as exc:
            logger.error(
                "Classification failed",
                extra={"error": str(exc), "comment_id": comment.id},
            )
            comment.sentiment = "neutral"
            comment.urgency_score = 5.0
            comment.reply_status = "classified"

        return comment

    async def classify_batch(self, comments: list[Comment]) -> list[Comment]:
        """Classify multiple comments sequentially."""
        classified: list[Comment] = []
        for comment in comments:
            result = await self.classify(comment)
            classified.append(result)
        return classified
