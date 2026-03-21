# PresenceOS — A/B Testing Service (Sprint 8)
# Generates 2 caption variants, tracks engagement, learns from results
# Cost: $0 (pure internal logic + Claude Haiku for variant generation)

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ABTest:
    """An A/B test on a social media post."""

    id: str = ""
    business_id: str = ""
    platform: str = ""

    # Variant A
    caption_a: str = ""
    post_id_a: str = ""
    published_at_a: Optional[str] = None

    # Variant B
    caption_b: str = ""
    post_id_b: str = ""
    published_at_b: Optional[str] = None

    # Metrics (collected 48h after publication)
    likes_a: int = 0
    comments_a: int = 0
    reach_a: int = 0
    likes_b: int = 0
    comments_b: int = 0
    reach_b: int = 0

    # Result
    winner: Optional[str] = None
    winner_insight: str = ""

    # Status
    status: str = "pending"  # pending|a_published|b_published|analyzing|complete
    created_at: str = ""
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def engagement_a(self) -> float:
        if self.reach_a == 0:
            return float(self.likes_a + self.comments_a)
        return (self.likes_a + self.comments_a) / self.reach_a

    @property
    def engagement_b(self) -> float:
        if self.reach_b == 0:
            return float(self.likes_b + self.comments_b)
        return (self.likes_b + self.comments_b) / self.reach_b


class ABTestingService:
    """Generates caption variants and analyzes A/B test results."""

    def __init__(self) -> None:
        self._claude: anthropic.Anthropic | None = None

    def _get_claude(self) -> anthropic.Anthropic:
        if self._claude is None:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self._claude = anthropic.Anthropic(api_key=api_key)
        return self._claude

    async def generate_variants(
        self,
        original_caption: str,
        business_dna: dict | None = None,
        post_topic: str = "",
    ) -> dict:
        """
        Generate 2 caption variants for A/B testing.
        Returns {"caption_a": str, "caption_b": str, "strategy": str, "hypothesis": str}
        """
        dna_context = ""
        if business_dna:
            name = business_dna.get("business_name", "")
            tone = business_dna.get("editorial_tone", "")
            if name or tone:
                dna_context = f"\nCommerce : {name}, ton : {tone}"

        prompt = f"""Tu dois creer 2 variantes d'une caption Instagram pour un test A/B.
{dna_context}

Caption originale :
"{original_caption}"

Sujet du post : {post_topic or 'general'}

Genere 2 variantes distinctes qui testent une hypothese specifique.
Strategies possibles : longueur (court vs long), CTA (question vs invitation), ton (emotionnel vs factuel).

Reponds en JSON strict :
{{
  "caption_a": "<variante A complete avec hashtags>",
  "caption_b": "<variante B complete avec hashtags>",
  "strategy": "<ce qui est teste en 1 phrase courte>",
  "hypothesis": "<laquelle devrait mieux performer et pourquoi>"
}}"""

        try:
            claude = self._get_claude()
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(raw)
        except Exception as exc:
            logger.error("generate_variants failed", extra={"error": str(exc)})
            return {
                "caption_a": original_caption,
                "caption_b": original_caption + "\n\nEt toi, tu en penses quoi ?",
                "strategy": "Avec vs sans appel a l'action",
                "hypothesis": "La version avec question genere plus de commentaires",
            }

    async def create_ab_test(
        self,
        business_id: str,
        platform: str,
        original_caption: str,
        business_dna: dict | None = None,
        post_topic: str = "",
    ) -> ABTest:
        """Create a new A/B test with 2 caption variants."""
        variants = await self.generate_variants(original_caption, business_dna, post_topic)

        return ABTest(
            id=str(uuid.uuid4()),
            business_id=business_id,
            platform=platform,
            caption_a=variants.get("caption_a", original_caption),
            caption_b=variants.get("caption_b", original_caption),
            status="pending",
            created_at=datetime.utcnow().isoformat(),
        )

    async def analyze_results(self, test: ABTest) -> ABTest:
        """Analyze metrics and determine the winner."""
        if test.engagement_a > test.engagement_b:
            winner = "A"
        elif test.engagement_b > test.engagement_a:
            winner = "B"
        else:
            winner = "A"  # tie goes to A (first published)

        prompt = f"""Un test A/B de caption Instagram vient de se terminer.

Variante A : "{test.caption_a[:200]}"
Metriques A : {test.likes_a} likes, {test.comments_a} commentaires, {test.reach_a} reach

Variante B : "{test.caption_b[:200]}"
Metriques B : {test.likes_b} likes, {test.comments_b} commentaires, {test.reach_b} reach

Gagnant : Variante {winner}

En 1 phrase courte, explique ce qui a fonctionne et pourquoi.
Reponds uniquement la phrase, sans guillemets."""

        try:
            claude = self._get_claude()
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            insight = response.content[0].text.strip()
        except Exception as e:
            from app.core.observability import get_logger
            get_logger(__name__).warning("AB testing AI insight generation failed", error=str(e))
            insight = f"La variante {winner} a mieux performe sur cette audience."

        test.winner = winner
        test.winner_insight = insight
        test.status = "complete"
        test.completed_at = datetime.utcnow().isoformat()

        return test

    async def get_tests_for_business(self, business_id: str) -> list[dict]:
        """Get A/B test history for a business (placeholder)."""
        return []
