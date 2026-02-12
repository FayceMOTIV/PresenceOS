"""
PresenceOS - AI Service for Content Generation
"""
import json
import structlog
from datetime import datetime
from typing import Any

import anthropic
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.brand import Brand
from app.models.content import Platform, VariantStyle
from app.prompts.caption_generator import (
    build_draft_generation_prompt,
    build_photo_captions_prompt,
    CAPTION_STYLE_DESCRIPTIONS,
    TONE_DESCRIPTIONS,
    PROMPT_VERSION,
)
from app.schemas.content import (
    CaptionStyle,
    GeneratedIdea,
    GeneratedDraft,
    GeneratedVariant,
    PhotoCaptionSuggestion,
)

logger = structlog.get_logger()

# Prompt templates
IDEA_GENERATION_PROMPT = """Tu es un expert en marketing digital et création de contenu pour les réseaux sociaux.

BRAND CONTEXT:
- Nom: {brand_name}
- Type: {brand_type}
- Description: {brand_description}
- Persona cible: {target_persona}
- Localisations: {locations}
- Contraintes: {constraints}

BRAND VOICE:
- Ton formel/décontracté: {tone_formal}/100
- Ton joueur/sérieux: {tone_playful}/100
- Ton audacieux/subtil: {tone_bold}/100
- Langue principale: {language}
- Instructions spéciales: {custom_instructions}

CONTENT PILLARS (répartition souhaitée):
{content_pillars}

CONTEXTE ADDITIONNEL:
{context}

TÂCHE:
Génère {count} idées de contenu créatives et engageantes pour cette marque.
{platform_instruction}
{date_instruction}

Pour chaque idée, fournis:
1. Un titre accrocheur
2. Une description détaillée (2-3 phrases)
3. Le pilier de contenu correspondant
4. Les plateformes cibles
5. 3 hooks possibles (phrases d'accroche)
6. Ton raisonnement (pourquoi cette idée est pertinente)

Réponds en JSON avec ce format:
{{
  "ideas": [
    {{
      "title": "...",
      "description": "...",
      "content_pillar": "education|entertainment|engagement|promotion|behind_scenes",
      "target_platforms": ["instagram_post", "tiktok", "linkedin"],
      "hooks": ["...", "...", "..."],
      "ai_reasoning": "...",
      "suggested_date": "YYYY-MM-DD" ou null
    }}
  ]
}}
"""

VARIANT_PROMPT = """Transforme cette caption en version "{style}":

Caption originale:
{original_caption}

Style demandé: {style_description}

Garde le même message mais adapte le ton selon le style demandé.
Réponds en JSON:
{{
  "caption": "...",
  "hashtags": [...],
  "ai_notes": "explication des changements"
}}
"""

TREND_ANALYSIS_PROMPT = """Analyse ces tendances pour la marque {brand_name}:

{trends}

1. Résume les tendances en 2-3 phrases
2. Identifie les thèmes clés
3. {idea_instruction}

Réponds en JSON:
{{
  "summary": "...",
  "key_themes": ["theme1", "theme2", ...],
  "ideas": [...] ou null
}}
"""


class AIService:
    """Unified AI service with provider abstraction."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.ai_provider

        if self.provider == "openai":
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            self.model_name = settings.openai_model
        else:
            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model_name = settings.anthropic_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def _complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """Send completion request to AI provider."""
        try:
            if self.provider == "openai":
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content

            else:  # anthropic
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    system=system or "Tu es un assistant expert en marketing digital.",
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text

        except Exception as e:
            logger.error("AI completion failed", provider=self.provider, error=str(e))
            raise

    def _parse_json_response(self, response: str) -> dict:
        """Extract and parse JSON from response."""
        # Try to find JSON in the response
        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")

        json_str = response[start:end]
        return json.loads(json_str)

    def _build_brand_context(self, brand: Brand) -> dict:
        """Build brand context dict for prompts."""
        voice = brand.voice
        return {
            "brand_name": brand.name,
            "brand_type": brand.brand_type.value,
            "brand_description": brand.description or "Non spécifié",
            "target_persona": json.dumps(brand.target_persona, ensure_ascii=False)
            if brand.target_persona
            else "Non spécifié",
            "locations": ", ".join(brand.locations) if brand.locations else "Non spécifié",
            "constraints": json.dumps(brand.constraints, ensure_ascii=False)
            if brand.constraints
            else "Aucune",
            "tone_formal": voice.tone_formal if voice else 50,
            "tone_playful": voice.tone_playful if voice else 50,
            "tone_bold": voice.tone_bold if voice else 50,
            "language": voice.primary_language if voice else "fr",
            "custom_instructions": voice.custom_instructions if voice else "",
            "words_to_avoid": ", ".join(voice.words_to_avoid) if voice and voice.words_to_avoid else "Aucun",
            "words_to_prefer": ", ".join(voice.words_to_prefer) if voice and voice.words_to_prefer else "Aucun",
            "emojis_allowed": ", ".join(voice.emojis_allowed) if voice and voice.emojis_allowed else "Tous",
            "max_emojis": voice.max_emojis_per_post if voice else 3,
            "hashtag_style": voice.hashtag_style if voice else "lowercase",
            "content_pillars": json.dumps(brand.content_pillars, ensure_ascii=False, indent=2)
            if brand.content_pillars
            else "Répartition égale",
        }

    async def generate_ideas(
        self,
        brand: Brand,
        count: int = 3,
        content_pillars: list[str] | None = None,
        platforms: list[str] | None = None,
        context: str | None = None,
        date_range: tuple[datetime | None, datetime | None] = (None, None),
    ) -> list[GeneratedIdea]:
        """Generate content ideas for a brand."""
        brand_context = self._build_brand_context(brand)

        platform_instruction = ""
        if platforms:
            platform_instruction = f"Cible ces plateformes: {', '.join(platforms)}"

        date_instruction = ""
        if date_range[0] and date_range[1]:
            date_instruction = f"Suggère des dates entre {date_range[0].strftime('%Y-%m-%d')} et {date_range[1].strftime('%Y-%m-%d')}"

        prompt = IDEA_GENERATION_PROMPT.format(
            **brand_context,
            count=count,
            context=context or "Aucun contexte spécifique",
            platform_instruction=platform_instruction,
            date_instruction=date_instruction,
        )

        response = await self._complete(prompt)
        data = self._parse_json_response(response)

        ideas = []
        for idea_data in data.get("ideas", []):
            ideas.append(
                GeneratedIdea(
                    title=idea_data["title"],
                    description=idea_data["description"],
                    content_pillar=idea_data["content_pillar"],
                    target_platforms=idea_data["target_platforms"],
                    hooks=idea_data["hooks"],
                    ai_reasoning=idea_data["ai_reasoning"],
                    suggested_date=datetime.fromisoformat(idea_data["suggested_date"])
                    if idea_data.get("suggested_date")
                    else None,
                )
            )

        return ideas

    async def generate_draft(
        self,
        brand: Brand,
        platform: Platform,
        topic: str | None = None,
        idea_context: dict | None = None,
        relevant_knowledge: list[dict] | None = None,
        media_urls: list[str] | None = None,
        generate_variants: bool = True,
        variant_styles: list[str] | None = None,
        additional_instructions: str | None = None,
    ) -> tuple[GeneratedDraft, list[GeneratedVariant]]:
        """Generate a content draft with variants."""
        brand_context = self._build_brand_context(brand)

        prompt = build_draft_generation_prompt(
            brand_context=brand_context,
            platform=platform.value,
            idea_context=json.dumps(idea_context, ensure_ascii=False) if idea_context else "Aucun",
            relevant_knowledge=json.dumps(relevant_knowledge, ensure_ascii=False, indent=2)
            if relevant_knowledge
            else "Aucune connaissance specifique",
            media_info=f"Medias attaches: {len(media_urls)} fichiers" if media_urls else "Aucun media",
            additional_instructions=additional_instructions or "Aucune",
        )

        response = await self._complete(prompt, temperature=0.8)
        data = self._parse_json_response(response)

        draft = GeneratedDraft(
            platform=platform,
            caption=data["caption"],
            hashtags=data.get("hashtags", []),
            platform_data=data.get("platform_data"),
        )

        # Generate variants
        variants = []
        if generate_variants:
            style_descriptions = {
                "conservative": "Plus sobre, professionnel, mesuré. Moins d'emojis, ton plus neutre.",
                "balanced": "Équilibré entre professionnel et engageant. Ton naturel.",
                "bold": "Audacieux, provocateur (dans les limites de la marque). Accrocheur.",
                "faical_style": "Style Faïçal: direct, authentique, avec une touche d'humour. Comme si tu parlais à un ami entrepreneur.",
            }

            styles_to_generate = variant_styles or ["conservative", "balanced", "bold"]

            for style in styles_to_generate:
                variant_prompt = VARIANT_PROMPT.format(
                    original_caption=draft.caption,
                    style=style,
                    style_description=style_descriptions.get(style, ""),
                )

                try:
                    variant_response = await self._complete(variant_prompt, temperature=0.8)
                    variant_data = self._parse_json_response(variant_response)

                    variants.append(
                        GeneratedVariant(
                            style=VariantStyle(style),
                            caption=variant_data["caption"],
                            hashtags=variant_data.get("hashtags", draft.hashtags),
                            ai_notes=variant_data.get("ai_notes", ""),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate {style} variant", error=str(e))

        return draft, variants

    async def analyze_trends(
        self,
        brand: Brand,
        trends: list[dict],
        generate_ideas: bool = True,
        idea_count: int = 3,
    ) -> dict:
        """Analyze trends and optionally generate ideas."""
        trends_text = "\n".join(
            [
                f"- {t.get('description', '')} (Source: {t.get('url', 'N/A')}, Platform: {t.get('platform', 'N/A')})"
                for t in trends
            ]
        )

        idea_instruction = (
            f"Génère {idea_count} idées de contenu basées sur ces tendances, adaptées à la marque."
            if generate_ideas
            else "Ne génère pas d'idées, juste l'analyse."
        )

        prompt = TREND_ANALYSIS_PROMPT.format(
            brand_name=brand.name,
            trends=trends_text,
            idea_instruction=idea_instruction,
        )

        response = await self._complete(prompt)
        data = self._parse_json_response(response)

        result = {
            "summary": data.get("summary", ""),
            "key_themes": data.get("key_themes", []),
        }

        if generate_ideas and data.get("ideas"):
            result["ideas"] = [
                GeneratedIdea(
                    title=i["title"],
                    description=i["description"],
                    content_pillar=i.get("content_pillar", "engagement"),
                    target_platforms=i.get("target_platforms", ["instagram_post"]),
                    hooks=i.get("hooks", []),
                    ai_reasoning=i.get("ai_reasoning", "Inspiré par les tendances"),
                )
                for i in data["ideas"]
            ]

        return result

    async def transcribe_audio(self, audio_content: bytes, filename: str) -> str:
        """Transcribe audio using OpenAI Whisper."""
        if self.provider != "openai":
            # Fall back to OpenAI for transcription
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            client = self.client

        # Create a file-like object
        from io import BytesIO

        audio_file = BytesIO(audio_content)
        audio_file.name = filename

        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="fr",
        )

        return response.text

    async def enhance_caption(
        self, brand: Brand, caption: str, platform: str
    ) -> dict:
        """Enhance a caption with brand voice."""
        brand_context = self._build_brand_context(brand)

        prompt = f"""Améliore cette caption pour {platform} en respectant la voix de la marque:

Caption originale: {caption}

Brand voice:
- Ton: {brand_context['tone_formal']}/100 formel, {brand_context['tone_playful']}/100 joueur
- Mots à éviter: {brand_context['words_to_avoid']}
- Max emojis: {brand_context['max_emojis']}

Réponds en JSON:
{{
  "caption": "...",
  "hashtags": [...],
  "changes_made": ["changement 1", "changement 2", ...]
}}
"""

        response = await self._complete(prompt)
        return self._parse_json_response(response)

    async def suggest_replies(
        self, brand: Brand, comment: str, context: str | None = None
    ) -> list[str]:
        """Generate reply suggestions for a comment."""
        brand_context = self._build_brand_context(brand)

        prompt = f"""Génère 3 réponses possibles à ce commentaire pour la marque {brand.name}:

Commentaire: {comment}
Contexte: {context or 'Aucun contexte spécifique'}

Voix de la marque:
- Ton: {brand_context['tone_formal']}/100 formel, {brand_context['tone_playful']}/100 joueur

Réponds en JSON:
{{
  "replies": ["réponse 1", "réponse 2", "réponse 3"]
}}
"""

        response = await self._complete(prompt)
        data = self._parse_json_response(response)
        return data.get("replies", [])

    # ── Photo Caption Methods (visual flow) ─────────────────────────

    async def generate_photo_captions(
        self,
        brand: Brand,
        image_analysis: dict,
        platforms: list[str] | None = None,
    ) -> list[PhotoCaptionSuggestion]:
        """Generate 3 caption styles from photo analysis in ONE AI call."""
        brand_context = self._build_brand_context(brand)

        prompt = build_photo_captions_prompt(
            brand_context=brand_context,
            image_analysis=image_analysis,
            platforms=platforms,
        )

        response = await self._complete(prompt, temperature=0.8, max_tokens=4000)
        data = self._parse_json_response(response)

        suggestions = []
        for s in data.get("suggestions", []):
            suggestions.append(
                PhotoCaptionSuggestion(
                    style=CaptionStyle(s["style"]),
                    caption=s["caption"],
                    hashtags=s.get("hashtags", []),
                    ai_notes=s.get("ai_notes", ""),
                )
            )

        return suggestions

    async def regenerate_hashtags(
        self,
        brand: Brand,
        caption: str,
        platform: str = "instagram_post",
        count: int = 10,
    ) -> list[str]:
        """Regenerate just hashtags for a given caption."""
        brand_context = self._build_brand_context(brand)

        prompt = f"""Genere exactement {count} hashtags optimises pour cette caption sur {platform}.

Caption: {caption}

Marque: {brand_context['brand_name']} ({brand_context['brand_type']})
Style hashtags: {brand_context['hashtag_style']}

Regles:
- Mix de hashtags populaires (portee) et niche (ciblage)
- Pertinents pour le contenu et la marque
- Sans le symbole # (juste les mots)

Reponds en JSON:
{{
  "hashtags": ["hashtag1", "hashtag2", "..."]
}}"""

        response = await self._complete(prompt, temperature=0.7, max_tokens=500)
        data = self._parse_json_response(response)
        return data.get("hashtags", [])

    async def change_caption_tone(
        self,
        brand: Brand,
        caption: str,
        tone: str,
        platform: str = "instagram_post",
    ) -> dict:
        """Rewrite caption in a new tone (fun/premium/urgence)."""
        brand_context = self._build_brand_context(brand)
        tone_desc = TONE_DESCRIPTIONS.get(tone, "")

        prompt = f"""Reecris cette caption avec le ton "{tone}".

Caption originale:
{caption}

Ton demande: {tone_desc}

Marque: {brand_context['brand_name']}
Plateforme: {platform}

IMPORTANT: Garde la meme structure (Hook + Body + CTA) et les memes informations cles.
Change UNIQUEMENT le ton, le vocabulaire et le style.

Reponds en JSON:
{{
  "caption": "nouvelle caption reecrite",
  "changes_made": ["changement 1", "changement 2", "..."]
}}"""

        response = await self._complete(prompt, temperature=0.8, max_tokens=2000)
        data = self._parse_json_response(response)
        return {
            "caption": data.get("caption", caption),
            "changes_made": data.get("changes_made", []),
        }

    async def suggest_emojis(
        self,
        brand: Brand,
        caption: str,
    ) -> dict:
        """Suggest strategic emoji placements for a caption."""
        brand_context = self._build_brand_context(brand)
        max_emojis = brand_context.get("max_emojis", 3)

        prompt = f"""Suggere des emojis strategiques pour cette caption.

Caption: {caption}

Marque: {brand_context['brand_name']}
Maximum emojis: {max_emojis}

Regles:
- Place les emojis de facon strategique (hook, transitions, CTA)
- Maximum {max_emojis} emojis au total
- Chaque emoji doit renforcer le message, pas decorer

Reponds en JSON:
{{
  "suggestions": [
    {{"emoji": "emoji_ici", "position": "hook|body|cta", "reason": "pourquoi cet emoji"}},
    ...
  ],
  "caption_with_emojis": "la caption complete avec les emojis integres"
}}"""

        response = await self._complete(prompt, temperature=0.7, max_tokens=2000)
        return self._parse_json_response(response)
