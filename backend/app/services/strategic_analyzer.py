"""
StrategicAnalyzer — Analyse multimodale pour Ilyas War Room.
Reçoit URL / Image / Audio / Texte → retourne plan stratégique complet.
"""
import asyncio
import base64
import json
import re
import uuid
from functools import partial
from typing import Any

import aiohttp
import anthropic
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class StrategicAnalyzer:

    def __init__(self) -> None:
        self._claude: anthropic.AsyncAnthropic | None = None

    @property
    def claude(self) -> anthropic.AsyncAnthropic:
        if self._claude is None:
            self._claude = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._claude

    # ── URL ──────────────────────────────────────────────────────────────

    async def analyze_url(
        self, url: str, brand_context: dict, niche_profile: dict
    ) -> dict:
        """Analyse une URL (TikTok, Instagram, article, site concurrent)."""
        content = await self._fetch_url(url)
        brand_name = brand_context.get("name", "Mon business")

        prompt = f"""Tu es expert marketing {niche_profile['label']} analysant ce contenu web pour : {brand_name}

URL : {url}
CONTENU :
{content[:3000]}

Analyse et réponds UNIQUEMENT en JSON valide :
{{
  "summary": "résumé en 2 phrases de ce contenu",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "what_works": "ce qui fonctionne dans ce contenu et pourquoi",
  "adaptation": "comment adapter exactement pour {brand_name}",
  "action_plan": {{
    "this_week": ["action concrète 1", "action concrète 2", "action concrète 3"],
    "this_month": ["objectif 1", "objectif 2"],
    "next_3_months": ["vision 1", "vision 2"]
  }},
  "revenue_impact": "impact estimé sur le chiffre d'affaires et comment le mesurer",
  "content_ideas": ["idée de post 1", "idée de post 2", "idée de post 3"],
  "urgency": "low|medium|high|critical",
  "ilyas_response": "ma réponse naturelle en tant que Ilyas, ton CM IA"
}}"""

        response = await self.claude.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_json(response.content[0].text)

    async def _fetch_url(self, url: str) -> str:
        """Fetch URL via Firecrawl (fallback: simple HTTP)."""
        firecrawl_key = settings.firecrawl_api_key
        if firecrawl_key:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://api.firecrawl.dev/v0/scrape",
                        headers={
                            "Authorization": f"Bearer {firecrawl_key}",
                            "Content-Type": "application/json",
                        },
                        json={"url": url, "formats": ["markdown"]},
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("data", {}).get("markdown", "")[:3000]
            except Exception as e:
                logger.warning("firecrawl_failed", error=str(e))

        # Fallback HTTP simple
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "Mozilla/5.0 (compatible; PresenceOS/1.0)"}
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    text = await resp.text()
                    clean = re.sub(r"<[^>]+>", " ", text)
                    clean = re.sub(r"\s+", " ", clean).strip()
                    return clean[:2500]
        except Exception as e:
            logger.error("url_fetch_failed", error=str(e))
            return f"Contenu de {url} (non accessible directement)"

    # ── IMAGE ─────────────────────────────────────────────────────────────

    async def analyze_image(
        self,
        image_bytes: bytes,
        brand_context: dict,
        niche_profile: dict,
        user_note: str = "",
    ) -> dict:
        """Analyse une image avec Gemini 2.0 Flash (vision)."""
        brand_name = brand_context.get("name", "Mon business")
        api_key = settings.google_api_key or getattr(settings, "gemini_api_key", "")

        if api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                image_data = base64.b64encode(image_bytes).decode("utf-8")

                prompt = f"""Tu es expert marketing {niche_profile['label']} analysant cette image pour : {brand_name}

Note de l'utilisateur : {user_note if user_note else 'Analyse générale'}

Réponds UNIQUEMENT en JSON valide :
{{
  "image_description": "description détaillée de ce que montre l'image",
  "marketing_potential": "high|medium|low",
  "caption_instagram": "caption Instagram prête à poster (max 150 chars + hashtags)",
  "caption_tiktok": "version TikTok courte avec hook fort (max 80 chars)",
  "hashtags": ["#hash1", "#hash2", "#hash3", "#hash4", "#hash5"],
  "visual_tips": "conseils pour améliorer la photo/vidéo",
  "content_ideas": ["autre idée de contenu avec cette image", "idée 2"],
  "action_plan": {{
    "immediate": "action à faire maintenant avec cette image",
    "this_week": "plan cette semaine autour de ce contenu"
  }},
  "revenue_impact": "comment ce contenu peut générer du business",
  "ilyas_response": "ma réponse naturelle en tant que Ilyas"
}}"""

                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    partial(
                        model.generate_content,
                        [{"mime_type": "image/jpeg", "data": image_data}, prompt],
                    ),
                )
                return self._parse_json(response.text)

            except Exception as e:
                logger.warning("gemini_image_failed", error=str(e))

        # Fallback Claude vision
        return await self._analyze_image_claude(
            image_bytes, brand_context, niche_profile, user_note
        )

    async def _analyze_image_claude(
        self,
        image_bytes: bytes,
        brand_context: dict,
        niche_profile: dict,
        user_note: str,
    ) -> dict:
        """Fallback: analyse image via Claude vision."""
        brand_name = brand_context.get("name", "Mon business")
        try:
            image_data = base64.b64encode(image_bytes).decode("utf-8")
            response = await self.claude.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=800,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"Analyse cette image pour un business {niche_profile['label']} ({brand_name}). "
                                    f"Note: {user_note}. "
                                    "Réponds en JSON avec caption_instagram, hashtags, content_ideas, ilyas_response."
                                ),
                            },
                        ],
                    }
                ],
            )
            return self._parse_json(response.content[0].text)
        except Exception as e:
            logger.error("claude_image_fallback_failed", error=str(e))
            return {
                "ilyas_response": "Je n'ai pas pu analyser cette image. Essaie avec une image plus claire.",
                "marketing_potential": "medium",
            }

    # ── AUDIO ─────────────────────────────────────────────────────────────

    async def analyze_audio(
        self,
        audio_bytes: bytes,
        brand_context: dict,
        niche_profile: dict,
    ) -> dict:
        """Transcrit un vocal (Whisper) puis analyse stratégiquement."""
        try:
            import openai

            oai = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            transcript_resp = await oai.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.m4a", audio_bytes, "audio/m4a"),
                language="fr",
            )
            transcript = transcript_resp.text
            logger.info("whisper_transcript", preview=transcript[:100])

            result = await self.analyze_text(
                transcript, brand_context, niche_profile, source="vocal"
            )
            result["transcript"] = transcript
            return result

        except Exception as e:
            logger.error("audio_analysis_failed", error=str(e))
            return {
                "ilyas_response": "Je n'ai pas pu transcrire ce vocal. Essaie en texte directement.",
                "transcript": "",
            }

    # ── TEXT ──────────────────────────────────────────────────────────────

    async def analyze_text(
        self,
        text: str,
        brand_context: dict,
        niche_profile: dict,
        source: str = "text",
    ) -> dict:
        """Analyse un texte libre (retour client, idée, observation)."""
        brand_name = brand_context.get("name", "Mon business")

        prompt = f"""Tu es Ilyas, expert marketing {niche_profile['label']} pour {brand_name}.

L'utilisateur t'a envoyé ce message ({source}) :
"{text}"

Analyse et construis un plan stratégique. Réponds UNIQUEMENT en JSON valide :
{{
  "understanding": "ce que j'ai compris de ce message",
  "key_insight": "l'insight marketing principal",
  "action_plan": {{
    "this_week": ["action concrète 1", "action concrète 2", "action concrète 3"],
    "this_month": ["objectif mesurable 1", "objectif mesurable 2"],
    "next_3_months": ["vision long terme 1", "vision long terme 2"]
  }},
  "content_opportunities": ["idée de contenu 1 prête à utiliser", "idée 2", "idée 3"],
  "revenue_connection": "lien direct avec le CA et comment mesurer l'impact",
  "risks": "risques à éviter dans cette situation",
  "ilyas_response": "ma réponse naturelle et directe en tant que Ilyas, ton CM IA — sans jargon, actionnable"
}}"""

        response = await self.claude.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )

        result = self._parse_json(response.content[0].text)

        # Sauvegarder dans Mem0 pour mémoire long terme
        await self._save_to_memory(text, result, brand_context)

        return result

    # ── HELPERS ───────────────────────────────────────────────────────────

    def _parse_json(self, text: str) -> dict:
        """Parse JSON avec nettoyage des backticks."""
        try:
            clean = text.strip()
            if clean.startswith("```"):
                parts = clean.split("```")
                clean = parts[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean.strip())
        except Exception as e:
            logger.warning("Strategic analyzer JSON parse failed — using raw text", error=str(e))
            return {"ilyas_response": text, "urgency": "medium"}

    async def _save_to_memory(
        self, input_text: str, analysis: dict, brand_context: dict
    ) -> None:
        """Sauvegarde l'analyse dans Mem0 pour mémoire stratégique long terme."""
        try:
            from app.services.ilyas.memory import Mem0Memory

            ilyas_memory = Mem0Memory()

            key_insight = analysis.get("key_insight", "")
            plan_summary = str(analysis.get("action_plan", {}))[:200]
            memory = f"Analyse stratégique reçue: {key_insight}. Plan: {plan_summary}"

            await ilyas_memory.add(
                messages=[
                    {"role": "user", "content": input_text[:500]},
                    {"role": "assistant", "content": memory},
                ],
                user_id=f"brand_{brand_context.get('id', 'unknown')}",
            )
        except Exception as e:
            logger.warning("mem0_save_failed", error=str(e))


strategic_analyzer = StrategicAnalyzer()
