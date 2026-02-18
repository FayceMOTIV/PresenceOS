"""
PresenceOS - Market Analyzer

AI-powered market analysis using GPT-4. Analyzes any business niche across
trends, tone, hashtags, posting times, and strategy using parallel sub-analyses.

Accepts optional Brand context to deliver hyper-personalized recommendations
instead of generic niche advice.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import openai
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Current month/year injected into every prompt so the model reasons about
# seasonal and timely trends instead of giving generic evergreen advice.
_CURRENT_PERIOD = datetime.now(timezone.utc).strftime("%B %Y")


def _build_brand_block(brand_context: dict[str, Any] | None) -> str:
    """Build a rich BRAND CONTEXT block from the optional brand dict.

    When brand_context is provided (from the Brand + BrandVoice models),
    every prompt gets hyper-personalized instead of generic niche analysis.
    """
    if not brand_context:
        return ""

    parts = ["\n\n--- BRAND CONTEXT (use this to personalize your analysis) ---"]

    if brand_context.get("name"):
        parts.append(f"Brand name: {brand_context['name']}")
    if brand_context.get("brand_type"):
        parts.append(f"Business type: {brand_context['brand_type']}")
    if brand_context.get("description"):
        parts.append(f"Description: {brand_context['description']}")
    if brand_context.get("target_persona"):
        persona = brand_context["target_persona"]
        if isinstance(persona, dict):
            parts.append(
                f"Target audience: {persona.get('name', 'N/A')}, "
                f"age {persona.get('age_range', 'N/A')}, "
                f"interests: {', '.join(persona.get('interests', []))}"
            )
        else:
            parts.append(f"Target audience: {persona}")
    if brand_context.get("locations"):
        parts.append(f"Locations: {', '.join(brand_context['locations'])}")
    if brand_context.get("constraints"):
        parts.append(f"Business constraints: {json.dumps(brand_context['constraints'], ensure_ascii=False)}")
    if brand_context.get("content_pillars"):
        parts.append(f"Content pillars weights: {json.dumps(brand_context['content_pillars'], ensure_ascii=False)}")

    # Voice info
    voice = brand_context.get("voice")
    if voice and isinstance(voice, dict):
        tone_desc = []
        if voice.get("tone_formal") is not None:
            formality = "très formel" if voice["tone_formal"] > 70 else ("formel" if voice["tone_formal"] > 50 else "décontracté")
            tone_desc.append(f"formalité: {formality} ({voice['tone_formal']}/100)")
        if voice.get("tone_playful") is not None:
            playful = "joueur" if voice["tone_playful"] > 60 else "sérieux"
            tone_desc.append(f"registre: {playful} ({voice['tone_playful']}/100)")
        if voice.get("tone_bold") is not None:
            bold = "audacieux" if voice["tone_bold"] > 60 else "subtil"
            tone_desc.append(f"audace: {bold} ({voice['tone_bold']}/100)")
        if tone_desc:
            parts.append(f"Brand voice: {', '.join(tone_desc)}")
        if voice.get("words_to_avoid"):
            parts.append(f"Words to AVOID: {', '.join(voice['words_to_avoid'])}")
        if voice.get("words_to_prefer"):
            parts.append(f"Words to PREFER: {', '.join(voice['words_to_prefer'])}")
        if voice.get("example_phrases"):
            parts.append(f"Example phrases: {' | '.join(voice['example_phrases'][:3])}")

    parts.append("--- END BRAND CONTEXT ---\n")
    return "\n".join(parts)


# ── Master system prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""Tu es un stratège senior en marketing digital avec 15 ans d'expérience.
Tu as travaillé avec des centaines de PME et grandes marques dans tous les secteurs.

RÈGLES ABSOLUES :
1. Tu raisonnes TOUJOURS par rapport au marché local et à la période actuelle ({_CURRENT_PERIOD}).
2. Tu ne donnes JAMAIS de conseils génériques. Chaque recommandation doit être spécifique au secteur ET à la localisation.
3. Tu prends en compte la saisonnalité (vacances, fêtes, météo, événements locaux).
4. Tu distingues les petites entreprises locales des grandes chaînes — tes conseils sont adaptés aux PME.
5. Quand un Brand Context est fourni, tu personnalises TOUT par rapport à cette marque spécifique.
6. Tu réponds TOUJOURS en JSON valide. Jamais de markdown, jamais de texte avant/après le JSON.
7. Tu écris en français sauf les hashtags (qui peuvent être en anglais si pertinent).
"""


class MarketAnalyzer:
    """Market analysis service powered by GPT-4.

    Runs 5 parallel sub-analyses (trends, tone, hashtags, posting times,
    strategy) and aggregates results into a comprehensive market report.

    Optionally accepts a brand_context dict to hyper-personalize all analyses.
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
        brand_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform a full market analysis for the given niche and location.

        Args:
            niche: The business sector (any string: "restaurant", "fleuriste",
                   "avocat", "e-commerce textile", "salle de sport", etc.).
            location: Geographic market (city, region, or country).
            brand_context: Optional dict with Brand + BrandVoice data for
                          hyper-personalized analysis.

        Returns:
            Dict containing: niche, location, analyzed_at, trends, optimal_tone,
            top_hashtags, best_posting_times, strategy, confidence_score.
        """
        logger.info("Starting niche analysis", niche=niche, location=location,
                     has_brand_context=brand_context is not None)

        brand_block = _build_brand_block(brand_context)

        try:
            # Phase 1: Run trends, tone, hashtags, times in parallel
            trends, tone, hashtags, times = await asyncio.gather(
                self._analyze_trends(niche, location, brand_block),
                self._analyze_tone(niche, location, brand_block),
                self._analyze_hashtags(niche, location, brand_block),
                self._analyze_times(niche, location, brand_block),
            )

            # Phase 2: Strategy uses the results from Phase 1 for coherent output
            strategy = await self._generate_strategy(
                niche, location, brand_block, trends, tone, hashtags, times,
            )
        except Exception as exc:
            logger.error("Niche analysis failed", niche=niche, location=location, error=str(exc))
            raise

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

        logger.info("Niche analysis complete", niche=niche, confidence_score=confidence_score)
        return result

    # ── Sub-analysis methods ──────────────────────────────────────────────────

    async def _analyze_trends(
        self, niche: str, location: str, brand_block: str,
    ) -> dict[str, Any]:
        """Identify current market trends with seasonal awareness."""
        client = self._get_client()

        prompt = f"""MISSION : Analyse approfondie des tendances pour le secteur « {niche} » en {location}, en {_CURRENT_PERIOD}.

CONSIGNES :
- Identifie 5-7 tendances ÉMERGENTES spécifiques à ce secteur ET cette localisation.
- Pour chaque tendance, indique si elle est en croissance, à maturité ou en déclin.
- Analyse les comportements consommateurs ACTUELS (post-COVID, inflation, digital-first).
- Identifie les opportunités de contenu que la plupart des concurrents ignorent.
- Prends en compte la SAISONNALITÉ : quels événements, fêtes, saisons impactent ce secteur en {_CURRENT_PERIOD} ?
- Indique le sentiment général du marché avec une justification.
{brand_block}

FORMAT JSON STRICT :
{{
  "emerging_trends": [
    {{"name": "...", "status": "growing|mature|declining", "relevance_score": 85, "description": "description concrète en 1-2 phrases", "content_angle": "comment exploiter cette tendance en contenu"}}
  ],
  "consumer_behaviors": [
    {{"behavior": "...", "impact": "high|medium|low", "content_opportunity": "type de contenu à créer"}}
  ],
  "seasonal_factors": [
    {{"factor": "...", "dates": "...", "content_ideas": ["idée 1", "idée 2"]}}
  ],
  "content_opportunities": [
    {{"opportunity": "...", "difficulty": "easy|medium|hard", "expected_impact": "high|medium|low", "example_post": "description d'un post concret"}}
  ],
  "market_sentiment": "positive|neutral|negative",
  "sentiment_rationale": "justification en 2-3 phrases",
  "trend_summary": "synthèse actionnable en 3-4 phrases"
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)

    async def _analyze_tone(
        self, niche: str, location: str, brand_block: str,
    ) -> dict[str, Any]:
        """Determine the optimal communication tone."""
        client = self._get_client()

        prompt = f"""MISSION : Détermine la voix et le ton de communication OPTIMAUX pour une marque dans le secteur « {niche} » en {location}.

CONSIGNES :
- Analyse les marques qui performent le mieux sur les réseaux sociaux dans ce secteur.
- Distingue le ton par plateforme (Instagram = plus visuel/émotionnel, LinkedIn = plus pro, TikTok = plus spontané).
- Fournis des EXEMPLES CONCRETS de phrases types, pas juste des adjectifs vagues.
- Indique les mots/expressions à utiliser ET ceux à éviter absolument.
- Recommande un style de légende (court punchy vs storytelling long).
- Adapte au marché local (le ton en France n'est pas le même qu'au Québec ou en Belgique).
{brand_block}

FORMAT JSON STRICT :
{{
  "primary_tone": "description précise du ton principal (ex: 'chaleureux et gourmand, comme un ami passionné qui partage ses découvertes')",
  "tone_by_platform": {{
    "instagram": "ton spécifique IG",
    "facebook": "ton spécifique FB",
    "tiktok": "ton spécifique TT",
    "linkedin": "ton spécifique LI"
  }},
  "formality_level": "formal|semi-formal|casual",
  "emotional_register": "registre émotionnel dominant",
  "caption_style": {{
    "ideal_length": "court (1-2 lignes)|moyen (3-5 lignes)|long (storytelling)",
    "structure": "description de la structure idéale",
    "cta_style": "style d'appel à l'action"
  }},
  "vocabulary": {{
    "power_words": ["mot1", "mot2", "mot3", "mot4", "mot5"],
    "words_to_avoid": ["mot1", "mot2", "mot3"],
    "recommended_emojis": ["emoji1", "emoji2", "emoji3", "emoji4"],
    "max_emojis_per_post": 3
  }},
  "example_captions": {{
    "instagram": "exemple de légende IG complète (2-3 lignes + hashtags)",
    "facebook": "exemple de post FB",
    "tiktok": "exemple de description TT"
  }},
  "tone_rationale": "pourquoi ce ton fonctionne pour ce secteur, en 2-3 phrases"
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)

    async def _analyze_hashtags(
        self, niche: str, location: str, brand_block: str,
    ) -> dict[str, Any]:
        """Identify the top-performing hashtags with volume tiers."""
        client = self._get_client()

        prompt = f"""MISSION : Stratégie hashtag complète pour le secteur « {niche} » en {location}, en {_CURRENT_PERIOD}.

CONSIGNES :
- Fournis des hashtags RÉELS et ACTUELS, pas des inventions. Chaque hashtag doit exister sur Instagram.
- Classe par volume : niche (<50K posts), moyen (50K-500K), large (>500K).
- Inclus des hashtags LOCAUX spécifiques à {location} (ex: #ParisFoodie, #LyonRestaurant).
- Fournis une stratégie de mix : combien de chaque taille par post.
- Adapte par plateforme (Instagram = 15-20 hashtags, TikTok = 3-5, LinkedIn = 3-5).
- Identifie les hashtags qui TRENDING maintenant (pas juste les classiques).
- Indique les hashtags bannis ou shadow-banned à éviter.
{brand_block}

FORMAT JSON STRICT :
{{
  "niche_hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "medium_hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "broad_hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "local_hashtags": ["#tag1", "#tag2", "#tag3"],
  "trending_now": ["#tag1", "#tag2", "#tag3"],
  "hashtags_to_avoid": ["#tag1", "#tag2"],
  "platform_sets": {{
    "instagram": {{
      "recommended_count": 20,
      "example_set": "#tag1 #tag2 #tag3 ... (un set complet de 20)"
    }},
    "tiktok": {{
      "recommended_count": 4,
      "example_set": "#tag1 #tag2 #tag3 #tag4"
    }},
    "linkedin": {{
      "recommended_count": 4,
      "example_set": "#tag1 #tag2 #tag3 #tag4"
    }}
  }},
  "mix_strategy": "recommandation du ratio niche/moyen/large par post",
  "hashtag_strategy": "stratégie globale en 2-3 phrases"
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)

    async def _analyze_times(
        self, niche: str, location: str, brand_block: str,
    ) -> dict[str, Any]:
        """Determine optimal posting times based on audience behavior."""
        client = self._get_client()

        prompt = f"""MISSION : Horaires de publication optimaux pour le secteur « {niche} » en {location}.

CONSIGNES :
- Base-toi sur le comportement RÉEL des audiences dans ce secteur et cette zone géographique.
- Pour un restaurant : les gens cherchent de l'inspiration AVANT les repas (11h, 17h).
- Pour un salon de beauté : pics le soir et le week-end quand les gens planifient.
- Pour du B2B/service : heures de bureau, pause déjeuner, trajet matin.
- Indique le fuseau horaire.
- Différencie CLAIREMENT semaine vs week-end.
- Donne un conseil spécifique pour maximiser le Reach vs l'Engagement (pas le même horaire).
{brand_block}

FORMAT JSON STRICT :
{{
  "instagram": {{
    "weekday_best": ["HH:MM", "HH:MM", "HH:MM"],
    "weekend_best": ["HH:MM", "HH:MM"],
    "peak_engagement": "créneau précis (ex: 18h30-20h00)",
    "peak_reach": "créneau pour maximiser la portée",
    "worst_times": ["HH:MM", "HH:MM"],
    "rationale": "pourquoi ces horaires pour ce secteur"
  }},
  "facebook": {{
    "weekday_best": ["HH:MM", "HH:MM"],
    "weekend_best": ["HH:MM"],
    "peak_engagement": "créneau",
    "rationale": "explication"
  }},
  "tiktok": {{
    "weekday_best": ["HH:MM", "HH:MM", "HH:MM"],
    "weekend_best": ["HH:MM", "HH:MM"],
    "peak_virality": "créneau où les vidéos ont le plus de chance de devenir virales",
    "rationale": "explication"
  }},
  "linkedin": {{
    "weekday_best": ["HH:MM", "HH:MM"],
    "avoid_days": ["Samedi", "Dimanche"],
    "rationale": "explication"
  }},
  "weekly_schedule": {{
    "lundi": "plateforme recommandée + horaire",
    "mardi": "...",
    "mercredi": "...",
    "jeudi": "...",
    "vendredi": "...",
    "samedi": "...",
    "dimanche": "..."
  }},
  "timezone": "Europe/Paris",
  "general_advice": "conseil stratégique sur le timing en 2-3 phrases"
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)

    async def _generate_strategy(
        self,
        niche: str,
        location: str,
        brand_block: str,
        trends: dict[str, Any],
        tone: dict[str, Any],
        hashtags: dict[str, Any],
        times: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a coherent strategy informed by the other 4 analyses."""
        client = self._get_client()

        # Summarize Phase 1 results so the strategy is data-driven
        context_summary = json.dumps({
            "trends_summary": trends.get("trend_summary", ""),
            "top_trends": [t.get("name", t) if isinstance(t, dict) else t
                          for t in trends.get("emerging_trends", [])[:3]],
            "recommended_tone": tone.get("primary_tone", ""),
            "caption_style": tone.get("caption_style", {}),
            "top_hashtags": hashtags.get("niche_hashtags", [])[:5],
            "best_times_ig": times.get("instagram", {}).get("weekday_best", []),
        }, ensure_ascii=False)

        prompt = f"""MISSION : Stratégie de contenu social media complète pour le secteur « {niche} » en {location}, en {_CURRENT_PERIOD}.

DONNÉES D'ANALYSE PRÉALABLE (utilise-les pour construire une stratégie cohérente) :
{context_summary}
{brand_block}

CONSIGNES :
- La stratégie doit être ACTIONNABLE dès demain par une PME avec 1-2 personnes au marketing.
- Définis 4-5 piliers de contenu avec un pourcentage de répartition (total = 100%).
- Pour chaque pilier, donne 3 exemples CONCRETS de posts (pas juste le titre, le concept complet).
- La fréquence de publication doit être réaliste (pas "poster 7j/7" pour une petite équipe).
- Inclus un plan de contenu type pour une semaine.
- Identifie 3 "quick wins" réalisables en moins de 24h.
- Donne un objectif chiffré à 90 jours (ex: +500 followers, engagement rate > 3%).

FORMAT JSON STRICT :
{{
  "content_pillars": [
    {{
      "name": "nom du pilier",
      "percentage": 30,
      "description": "description détaillée",
      "example_posts": [
        "description complète d'un post concret",
        "description complète d'un autre post",
        "et un troisième"
      ],
      "best_formats": ["photo", "carrousel", "reel"]
    }}
  ],
  "posting_frequency": {{
    "instagram": "Nx par semaine",
    "facebook": "Nx par semaine",
    "tiktok": "Nx par semaine",
    "linkedin": "Nx par semaine",
    "total_weekly": N
  }},
  "content_mix": {{
    "photos": N,
    "reels_videos": N,
    "carousels": N,
    "stories": N
  }},
  "weekly_plan": {{
    "lundi": {{"platform": "...", "pillar": "...", "format": "...", "idea": "..."}},
    "mardi": {{"platform": "...", "pillar": "...", "format": "...", "idea": "..."}},
    "mercredi": {{"platform": "...", "pillar": "...", "format": "...", "idea": "..."}},
    "jeudi": {{"platform": "...", "pillar": "...", "format": "...", "idea": "..."}},
    "vendredi": {{"platform": "...", "pillar": "...", "format": "...", "idea": "..."}}
  }},
  "key_messages": ["message clé 1", "message clé 2", "message clé 3"],
  "differentiation_angle": "ce qui va distinguer cette marque de ses concurrents sur les réseaux",
  "quick_wins": [
    {{"action": "...", "expected_result": "...", "time_needed": "..."}},
    {{"action": "...", "expected_result": "...", "time_needed": "..."}},
    {{"action": "...", "expected_result": "...", "time_needed": "..."}}
  ],
  "goals_90_days": {{
    "followers_target": "+N followers",
    "engagement_rate_target": "N%",
    "posts_published": N,
    "key_milestone": "objectif principal"
  }},
  "strategy_summary": "résumé exécutif de la stratégie en 4-5 phrases"
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _compute_confidence(
        self,
        trends: dict,
        tone: dict,
        hashtags: dict,
        times: dict,
        strategy: dict,
    ) -> float:
        """Compute a confidence score (0.0-1.0) based on data completeness."""
        score = 0.0
        total_checks = 0

        def _check_field(data: dict, key: str) -> None:
            nonlocal score, total_checks
            total_checks += 1
            value = data.get(key)
            if value and (not isinstance(value, list) or len(value) > 0):
                score += 1.0

        _check_field(trends, "emerging_trends")
        _check_field(trends, "trend_summary")
        _check_field(trends, "seasonal_factors")
        _check_field(tone, "primary_tone")
        _check_field(tone, "tone_by_platform")
        _check_field(tone, "example_captions")
        _check_field(hashtags, "niche_hashtags")
        _check_field(hashtags, "local_hashtags")
        _check_field(hashtags, "platform_sets")
        _check_field(times, "instagram")
        _check_field(times, "weekly_schedule")
        _check_field(strategy, "content_pillars")
        _check_field(strategy, "weekly_plan")
        _check_field(strategy, "quick_wins")
        _check_field(strategy, "strategy_summary")

        if total_checks == 0:
            return 0.0

        raw = score / total_checks
        return round(min(raw, 0.95), 2)
