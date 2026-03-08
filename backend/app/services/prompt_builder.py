"""
PresenceOS - Prompt Builder Service (Content Library)

Transforms the compiled Knowledge Base into dynamic system and user prompts
for AI content generation (posts, reels, stories).
"""
import json
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()


class PromptBuilder:
    """Builds dynamic AI prompts from the compiled Knowledge Base."""

    def build_system_prompt(self, kb: dict) -> str:
        """Build a system prompt from the compiled KB.

        Includes: identity, menu (featured, has_photo, price), voice,
        avoid last-7-days dishes, today's brief, performance data,
        niche tone guide.
        """
        identity = kb.get("identity", {})
        menu = kb.get("menu", {})
        media_section = kb.get("media", {})
        today = kb.get("today", {})
        history = kb.get("posting_history", {})
        voice = identity.get("voice", {})

        brand_name = identity.get("name", "la marque")
        brand_type = identity.get("type", "service")
        language = voice.get("language", "fr")
        lang_label = {"fr": "français", "en": "anglais", "es": "espagnol"}.get(
            language, language
        )

        sections = []

        # ── Identity ──
        sections.append(
            f"Tu es le créateur de contenu IA de « {brand_name} ».\n"
            f"Secteur : {brand_type}.\n"
            f"Tu rédiges en {lang_label}."
        )

        if identity.get("description"):
            sections.append(f"Description du business : {identity['description']}")

        # ── Voice ──
        voice_lines = []
        formality = "formel" if voice.get("tone_formal", 50) > 60 else "décontracté"
        playful = "joueur" if voice.get("tone_playful", 50) > 60 else "sérieux"
        bold = "audacieux" if voice.get("tone_bold", 50) > 60 else "subtil"
        voice_lines.append(f"Ton : {formality}, {playful}, {bold}")

        if voice.get("words_to_avoid"):
            voice_lines.append(f"Mots INTERDITS : {', '.join(voice['words_to_avoid'])}")
        if voice.get("words_to_prefer"):
            voice_lines.append(f"Mots à PRIVILÉGIER : {', '.join(voice['words_to_prefer'])}")
        if voice.get("emojis_allowed"):
            voice_lines.append("Emojis autorisés (avec modération)")
        else:
            voice_lines.append("Pas d'emojis")
        if voice.get("custom_instructions"):
            voice_lines.append(f"Instructions spéciales : {voice['custom_instructions']}")

        sections.append("VOIX DE LA MARQUE :\n" + "\n".join(voice_lines))

        # ── Menu ──
        categories = menu.get("categories", {})
        if categories:
            menu_lines = []
            for cat, dishes in categories.items():
                dish_strs = []
                for d in dishes:
                    parts = [d["name"]]
                    if d.get("is_featured"):
                        parts.insert(0, "⭐")
                    if d.get("has_photo"):
                        parts.append("📸")
                    if d.get("price"):
                        parts.append(f"{d['price']}€")
                    dish_strs.append(" ".join(parts))
                menu_lines.append(f"{cat.upper()} : {', '.join(dish_strs)}")

            sections.append("MENU :\n" + "\n".join(menu_lines))

        # ── Avoid recently posted dishes ──
        recent_dishes = self._get_recently_posted_dishes(menu)
        if recent_dishes:
            sections.append(
                f"PLATS À ÉVITER (déjà postés cette semaine) : {', '.join(recent_dishes)}"
            )

        # ── Today's brief ──
        if today.get("has_brief") and today.get("response"):
            sections.append(f"BRIEF DU JOUR : {today['response']}")

        # ── Media assets ──
        if media_section.get("total_assets", 0) > 0:
            sections.append(
                f"PHOTOS DISPONIBLES : {media_section['total_assets']} images/vidéos de qualité"
            )

        # ── Trending hashtags ──
        trends = kb.get("trends", [])
        if trends:
            tags_str = ", ".join(h["tag"] for h in trends[:10])
            sections.append(
                f"HASHTAGS TENDANCE (cette semaine) : {tags_str}\n"
                "Intègre 2-3 de ces hashtags s'ils sont pertinents pour le post."
            )

        # ── Performance hints ──
        perf = kb.get("performance", {})
        if perf.get("avg_engagement_rate"):
            sections.append(
                f"Taux d'engagement moyen : {perf['avg_engagement_rate']}%"
            )

        # ── Posting history ──
        history_count = history.get("last_7_days_count", 0)
        if history_count > 0:
            sections.append(
                f"Posts des 7 derniers jours : {history_count}"
            )

        # ── Rules ──
        sections.append(
            "RÈGLES DE GÉNÉRATION :\n"
            "1. Contenu original, engageant et adapté au réseau social cible.\n"
            "2. Utiliser le contexte du menu et des photos disponibles.\n"
            "3. Varier les plats mis en avant (éviter les répétitions).\n"
            "4. Respecter la voix de marque et les contraintes.\n"
            "5. Répondre UNIQUEMENT en JSON valide."
        )

        return "\n\n".join(sections)

    def build_generation_prompt(
        self,
        kb: dict,
        source_type: str,
        source_data: dict,
        content_type: str = "post",
        platform: str = "instagram",
    ) -> str:
        """Build a user prompt for content generation.

        Args:
            kb: Compiled knowledge base dict
            source_type: "brief", "asset", "request", "auto"
            source_data: Context for the source (brief response, asset info, request text)
            content_type: "post", "reel", "story"
            platform: Target platform
        """
        format_guide = self._get_format_guide(content_type, platform)

        context_block = ""
        if source_type == "brief":
            context_block = f"Le restaurateur a dit aujourd'hui : \"{source_data.get('response', '')}\""
        elif source_type == "asset":
            asset_desc = source_data.get("description", "une photo/vidéo")
            context_block = (
                f"Crée un post à partir de cette image/vidéo :\n"
                f"Description : {asset_desc}\n"
                f"Label : {source_data.get('label', 'N/A')}"
            )
            if source_data.get("dish_name"):
                context_block += f"\nPlat associé : {source_data['dish_name']}"
        elif source_type == "request":
            context_block = f"Demande du restaurateur : \"{source_data.get('text', '')}\""
        elif source_type == "auto":
            context_block = "Génère un post automatique en utilisant le menu et les photos disponibles."

        prompt = f"""Génère un contenu {content_type} pour {platform}.

{context_block}

{format_guide}

Réponds en JSON strict :
{{
  "caption": "<le texte du post, engageant et adapté>",
  "hashtags": ["#hashtag1", "#hashtag2", ...],
  "confidence": <float 0.0-1.0>,
  "reasoning": "<1 phrase expliquant tes choix>"
}}"""

        return prompt

    # ── Helpers ────────────────────────────────────────────────────────────

    def _get_recently_posted_dishes(self, menu: dict) -> list[str]:
        """Get dish names that were posted in the last 7 days."""
        recent = []
        for cat, dishes in menu.get("categories", {}).items():
            for d in dishes:
                if d.get("last_posted_at"):
                    # Already filtered by last 7 days at compile time
                    recent.append(d["name"])
        return recent

    def _get_format_guide(self, content_type: str, platform: str) -> str:
        """Get format-specific guidelines."""
        guides = {
            "post": (
                "FORMAT POST :\n"
                "- Caption : 1-3 paragraphes courts, accrocheur dès la 1ère ligne\n"
                "- Inclure un call-to-action (CTA) naturel\n"
                "- 5-15 hashtags pertinents et variés"
            ),
            "reel": (
                "FORMAT REEL :\n"
                "- Caption : courte (1-2 phrases max) + emojis\n"
                "- Hook fort dans la première phrase\n"
                "- 5-10 hashtags tendance"
            ),
            "story": (
                "FORMAT STORY :\n"
                "- Texte : ultra-court (1 phrase ou quelques mots)\n"
                "- Engageant, sondage/question possible\n"
                "- Max 3 hashtags"
            ),
        }

        platform_hints = {
            "instagram": "Optimisé pour Instagram : visuel, emojis, hashtags.",
            "facebook": "Optimisé pour Facebook : conversationnel, communautaire.",
            "tiktok": "Optimisé pour TikTok : tendance, hook rapide, argot.",
        }

        guide = guides.get(content_type, guides["post"])
        hint = platform_hints.get(platform, "")

        return f"{guide}\n{hint}" if hint else guide
