"""
PresenceOS - Market Analyzer

AI-powered market analysis using GPT-4. Analyzes niches across trends,
tone, hashtags, posting times, and overall strategy using parallel sub-analyses.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import openai
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class MarketAnalyzer:
    """Market analysis service powered by GPT-4.

    Runs 5 parallel sub-analyses (trends, tone, hashtags, posting times,
    strategy) and aggregates results into a comprehensive market report.
    """

    def __init__(self) -> None:
        self._client: openai.AsyncOpenAI | None = None

    def _get_client(self) -> openai.AsyncOpenAI:
        """Lazy initialization of the OpenAI client."""
        if self._client is None:
            if not settings.openai_api_key:
                raise RuntimeError(
                    "OpenAI API key is not configured. "
                    "Set OPENAI_API_KEY in your environment."
                )
            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def analyze_niche(
        self,
        niche: str,
        location: str = "France",
    ) -> dict[str, Any]:
        """Perform a full market analysis for the given niche and location.

        Runs 5 parallel sub-analyses via GPT-4 and returns a consolidated report.

        Args:
            niche: The business niche to analyze (e.g. "restaurant", "beauty salon").
            location: Geographic market to target (default: "France").

        Returns:
            Dict containing: niche, location, analyzed_at, trends, optimal_tone,
            top_hashtags, best_posting_times, strategy, confidence_score.
        """
        logger.info("Starting niche analysis", niche=niche, location=location)

        try:
            (
                trends,
                tone,
                hashtags,
                times,
                strategy,
            ) = await asyncio.gather(
                self._analyze_trends(niche, location),
                self._analyze_tone(niche, location),
                self._analyze_hashtags(niche, location),
                self._analyze_times(niche, location),
                self._generate_strategy(niche, location),
            )
        except Exception as exc:
            logger.error(
                "Niche analysis failed",
                niche=niche,
                location=location,
                error=str(exc),
            )
            raise

        # Compute a basic confidence score based on data completeness
        confidence_score = self._compute_confidence(trends, tone, hashtags, times, strategy)

        result: dict[str, Any] = {
            "niche": niche,
            "location": location,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "trends": trends,
            "optimal_tone": tone,
            "top_hashtags": hashtags,
            "best_posting_times": times,
            "strategy": strategy,
            "confidence_score": confidence_score,
        }

        logger.info(
            "Niche analysis complete",
            niche=niche,
            location=location,
            confidence_score=confidence_score,
        )
        return result

    # ── Sub-analysis methods ────────────────────────────────────────────────────

    async def _analyze_trends(self, niche: str, location: str) -> dict[str, Any]:
        """Identify current market trends for the niche."""
        client = self._get_client()

        prompt = (
            f"Analyse les tendances actuelles du marché pour le secteur '{niche}' "
            f"en '{location}'. Concentre-toi sur les tendances émergentes, les "
            f"comportements des consommateurs et les opportunités de contenu pour "
            f"les réseaux sociaux.\n\n"
            "Réponds en JSON avec ce format exact:\n"
            "{\n"
            '  "emerging_trends": ["trend1", "trend2", "trend3"],\n'
            '  "consumer_behaviors": ["behavior1", "behavior2"],\n'
            '  "content_opportunities": ["opportunity1", "opportunity2"],\n'
            '  "market_sentiment": "positive|neutral|negative",\n'
            '  "trend_summary": "résumé en 2-3 phrases"\n'
            "}"
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en marketing digital et analyse de marché. "
                        "Réponds toujours en JSON valide sans markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def _analyze_tone(self, niche: str, location: str) -> dict[str, Any]:
        """Determine the optimal communication tone for the niche."""
        client = self._get_client()

        prompt = (
            f"Détermine le ton de communication optimal pour une marque dans le "
            f"secteur '{niche}' ciblant le marché '{location}'. Analyse ce qui "
            f"résonne le mieux avec l'audience cible sur les réseaux sociaux.\n\n"
            "Réponds en JSON avec ce format exact:\n"
            "{\n"
            '  "primary_tone": "ex: chaleureux et authentique",\n'
            '  "secondary_tones": ["tone1", "tone2"],\n'
            '  "formality_level": "formal|semi-formal|casual",\n'
            '  "emotional_register": "ex: enthousiaste, bienveillant",\n'
            '  "language_style": "ex: simple et accessible",\n'
            '  "tone_rationale": "explication en 2-3 phrases"\n'
            "}"
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en brand voice et stratégie de communication. "
                        "Réponds toujours en JSON valide sans markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def _analyze_hashtags(self, niche: str, location: str) -> dict[str, Any]:
        """Identify the top-performing hashtags for the niche."""
        client = self._get_client()

        prompt = (
            f"Identifie les meilleurs hashtags pour le secteur '{niche}' "
            f"en '{location}'. Inclus des hashtags de différentes tailles "
            f"(niche, moyen, large) et pour différentes plateformes.\n\n"
            "Réponds en JSON avec ce format exact:\n"
            "{\n"
            '  "niche_hashtags": ["#tag1", "#tag2", "#tag3"],\n'
            '  "medium_hashtags": ["#tag1", "#tag2", "#tag3"],\n'
            '  "broad_hashtags": ["#tag1", "#tag2", "#tag3"],\n'
            '  "instagram_recommended": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],\n'
            '  "tiktok_recommended": ["#tag1", "#tag2", "#tag3"],\n'
            '  "trending_now": ["#tag1", "#tag2"],\n'
            '  "hashtag_strategy": "conseil en 1-2 phrases"\n'
            "}"
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en stratégie hashtag et SEO social media. "
                        "Réponds toujours en JSON valide sans markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def _analyze_times(self, niche: str, location: str) -> dict[str, Any]:
        """Determine optimal posting times for the niche audience."""
        client = self._get_client()

        prompt = (
            f"Détermine les meilleurs moments pour publier sur les réseaux sociaux "
            f"pour une entreprise dans le secteur '{niche}' en '{location}'. "
            f"Base-toi sur les habitudes des consommateurs locaux et le secteur d'activité.\n\n"
            "Réponds en JSON avec ce format exact:\n"
            "{\n"
            '  "instagram": {\n'
            '    "best_days": ["Mardi", "Jeudi", "Samedi"],\n'
            '    "best_hours": ["12:00", "19:00", "21:00"],\n'
            '    "peak_engagement_window": "ex: 18h-21h"\n'
            "  },\n"
            '  "facebook": {\n'
            '    "best_days": ["Mercredi", "Vendredi"],\n'
            '    "best_hours": ["13:00", "15:00"],\n'
            '    "peak_engagement_window": "ex: 13h-16h"\n'
            "  },\n"
            '  "tiktok": {\n'
            '    "best_days": ["Lundi", "Mardi", "Vendredi"],\n'
            '    "best_hours": ["07:00", "19:00", "21:00"],\n'
            '    "peak_engagement_window": "ex: 19h-22h"\n'
            "  },\n"
            '  "general_advice": "conseil général en 1-2 phrases",\n'
            '  "timezone": "Europe/Paris"\n'
            "}"
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en social media scheduling et analytics. "
                        "Réponds toujours en JSON valide sans markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def _generate_strategy(self, niche: str, location: str) -> dict[str, Any]:
        """Generate a high-level social media content strategy."""
        client = self._get_client()

        prompt = (
            f"Génère une stratégie de contenu social media pour une entreprise "
            f"dans le secteur '{niche}' en '{location}'. La stratégie doit être "
            f"actionnable et adaptée aux spécificités du marché local.\n\n"
            "Réponds en JSON avec ce format exact:\n"
            "{\n"
            '  "content_pillars": [\n'
            '    {"name": "pilier1", "percentage": 30, "description": "..."},\n'
            '    {"name": "pilier2", "percentage": 25, "description": "..."}\n'
            "  ],\n"
            '  "posting_frequency": {\n'
            '    "instagram": "ex: 5x par semaine",\n'
            '    "facebook": "ex: 3x par semaine",\n'
            '    "tiktok": "ex: 4x par semaine"\n'
            "  },\n"
            '  "content_mix": {\n'
            '    "photos": 40,\n'
            '    "videos": 35,\n'
            '    "stories": 15,\n'
            '    "carousels": 10\n'
            "  },\n"
            '  "key_messages": ["message1", "message2", "message3"],\n'
            '  "differentiation_angle": "ce qui distingue cette approche",\n'
            '  "quick_wins": ["action rapide 1", "action rapide 2"],\n'
            '  "strategy_summary": "résumé de la stratégie en 3-4 phrases"\n'
            "}"
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un stratège digital senior spécialisé dans les PME locales. "
                        "Réponds toujours en JSON valide sans markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _compute_confidence(
        self,
        trends: dict,
        tone: dict,
        hashtags: dict,
        times: dict,
        strategy: dict,
    ) -> float:
        """Compute a confidence score (0.0–1.0) based on data completeness."""
        score = 0.0
        total_checks = 0

        def _check_field(data: dict, key: str) -> None:
            nonlocal score, total_checks
            total_checks += 1
            value = data.get(key)
            if value and (not isinstance(value, list) or len(value) > 0):
                score += 1.0

        # Trends
        _check_field(trends, "emerging_trends")
        _check_field(trends, "trend_summary")

        # Tone
        _check_field(tone, "primary_tone")
        _check_field(tone, "formality_level")

        # Hashtags
        _check_field(hashtags, "instagram_recommended")
        _check_field(hashtags, "niche_hashtags")

        # Times
        _check_field(times, "instagram")
        _check_field(times, "general_advice")

        # Strategy
        _check_field(strategy, "content_pillars")
        _check_field(strategy, "strategy_summary")

        if total_checks == 0:
            return 0.0

        raw = score / total_checks
        # Round to 2 decimal places and cap at 0.95 (never 100% certain)
        return round(min(raw, 0.95), 2)
