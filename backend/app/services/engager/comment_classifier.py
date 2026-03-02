# PresenceOS — Comment Classifier (Sprint 5: Engager)
# Uses Claude Haiku for fast, cheap sentiment classification + urgency scoring

from __future__ import annotations

import json
import logging

import anthropic

from app.core.config import settings
from app.models.comment import Comment

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """Tu es un classificateur de commentaires pour un commerce local.

Analyse ce commentaire et retourne un JSON strict :
{{
  "sentiment": "positive|negative|question|spam|neutral|urgent",
  "urgency_score": <float 0-10>,
  "topics": [<liste de mots-cles>],
  "needs_reply": <bool>
}}

Regles :
- "urgent" = plainte grave, probleme sanitaire, reservation non confirmee
- "spam" = pub, bots, liens suspects
- "question" = demande d'info (horaires, menu, livraison, reservation)
- urgency_score >= 8 → urgent (humain doit valider)
- urgency_score 5-7 → important (reponse rapide)
- urgency_score < 5 → normal
- needs_reply = false pour spam, emoji-only, tags sans texte

Commentaire a analyser :
Plateforme: {platform}
Auteur: {author}
Texte: {text}"""


class CommentClassifier:
    """Classifies comments using Claude Haiku for speed and cost efficiency."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=api_key)
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

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text.strip()
            # Strip markdown code block if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            result = json.loads(raw)

            comment.sentiment = result.get("sentiment", "neutral")
            comment.urgency_score = float(result.get("urgency_score", 0))
            comment.topics = result.get("topics", [])

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
