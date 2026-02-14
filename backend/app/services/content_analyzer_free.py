"""
PresenceOS - Content Analyzer (Free Tier)

Analyzes Instagram content to extract brand tone and vocabulary patterns.
Uses OpenRouter free tier (Llama 3.3 70B) for analysis.
Stores results in BrandVoice and KnowledgeItems.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.brand import Brand, BrandVoice, KnowledgeItem, KnowledgeType

logger = logging.getLogger(__name__)

INSTAGRAM_APP_ID = "936619743392459"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "meta-llama/llama-3.3-70b-instruct:free"


@dataclass
class ToneMetrics:
    tone_formal: int = 50       # 0=casual, 100=formal
    tone_playful: int = 50      # 0=serious, 100=playful
    tone_bold: int = 50         # 0=subtle, 100=bold
    tone_emotional: int = 50    # 0=rational, 100=emotional
    humor_level: int = 50       # 0=none, 100=very humorous


@dataclass
class VocabularyAnalysis:
    favorite_words: list[str] = field(default_factory=list)
    favorite_emojis: list[str] = field(default_factory=list)
    cta_style: str = ""
    sentence_style: str = ""
    hashtag_style: str = ""
    words_to_prefer: list[str] = field(default_factory=list)
    words_to_avoid: list[str] = field(default_factory=list)


@dataclass
class ContentAnalysis:
    tone: ToneMetrics = field(default_factory=ToneMetrics)
    vocabulary: VocabularyAnalysis = field(default_factory=VocabularyAnalysis)
    summary: str = ""
    posts_analyzed: int = 0
    custom_instructions: str = ""


class ContentAnalyzerFree:
    """Analyzes Instagram content using free LLM tier."""

    def __init__(self):
        self.openrouter_key = settings.openrouter_api_key

    # ── Instagram Scraping ──────────────────────────────────────

    async def fetch_instagram_posts(
        self, username: str, max_posts: int = 12
    ) -> list[dict]:
        """
        Fetch recent Instagram posts for a given username.
        Uses Instagram's web API (no auth required for public profiles).
        """
        username = username.strip().lstrip("@").lower()
        posts = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Try Instagram web profile API
                url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "x-ig-app-id": INSTAGRAM_APP_ID,
                    "Accept": "application/json",
                }

                resp = await client.get(url, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    user_data = data.get("data", {}).get("user", {})
                    edges = (
                        user_data
                        .get("edge_owner_to_timeline_media", {})
                        .get("edges", [])
                    )

                    for edge in edges[:max_posts]:
                        node = edge.get("node", {})
                        caption_edges = (
                            node
                            .get("edge_media_to_caption", {})
                            .get("edges", [])
                        )
                        caption = ""
                        if caption_edges:
                            caption = caption_edges[0].get("node", {}).get("text", "")

                        if caption:
                            posts.append({
                                "caption": caption,
                                "likes": node.get("edge_liked_by", {}).get("count", 0),
                                "comments": node.get("edge_media_to_comment", {}).get("count", 0),
                                "timestamp": node.get("taken_at_timestamp", 0),
                            })

                    logger.info(
                        f"Fetched {len(posts)} posts from Instagram for @{username}"
                    )
                else:
                    logger.warning(
                        f"Instagram API returned status {resp.status_code} for @{username}"
                    )

        except Exception as e:
            logger.error(f"Error fetching Instagram posts for @{username}: {e}")

        return posts

    # ── LLM Analysis ────────────────────────────────────────────

    async def analyze_content(
        self, posts: list[dict], brand_name: str
    ) -> ContentAnalysis:
        """
        Analyze post captions using OpenRouter free tier LLM.
        Falls back to basic analysis if LLM is unavailable.
        """
        if not posts:
            return ContentAnalysis(summary="Aucun post trouve a analyser.")

        captions = [p["caption"] for p in posts if p.get("caption")]
        if not captions:
            return ContentAnalysis(summary="Aucune caption trouvee dans les posts.")

        captions_text = "\n---\n".join(captions[:12])

        prompt = f"""Analyse ces captions Instagram de la marque "{brand_name}".
Retourne un JSON STRICT (pas de texte avant/apres) avec cette structure exacte:

{{
  "tone": {{
    "tone_formal": <0-100, 0=tres casual/familier, 100=tres formel/corporate>,
    "tone_playful": <0-100, 0=tres serieux, 100=tres joueur/amusant>,
    "tone_bold": <0-100, 0=discret/subtil, 100=audacieux/percutant>,
    "tone_emotional": <0-100, 0=tres rationnel/factuel, 100=tres emotionnel>,
    "humor_level": <0-100, 0=pas d'humour, 100=tres humoristique>
  }},
  "vocabulary": {{
    "favorite_words": ["mot1", "mot2", ...],
    "favorite_emojis": ["emoji1", "emoji2", ...],
    "cta_style": "description du style de call-to-action utilise",
    "sentence_style": "court et percutant / long et narratif / questions rhetoriques / etc.",
    "hashtag_style": "lowercase / PascalCase / melange / etc.",
    "words_to_prefer": ["expressions signatures", ...],
    "words_to_avoid": ["mots jamais utilises dans ce style", ...]
  }},
  "summary": "Resume en 2-3 phrases du style editorial de la marque",
  "custom_instructions": "Instructions pour une IA qui devrait ecrire comme cette marque (2-3 phrases)"
}}

CAPTIONS A ANALYSER:
{captions_text}"""

        try:
            result = await self._call_openrouter(prompt)
            if result:
                return self._parse_analysis(result, len(captions))
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")

        # Fallback: basic analysis
        return self._basic_analysis(captions)

    async def _call_openrouter(self, prompt: str) -> str | None:
        """Call OpenRouter API with the free model."""
        if not self.openrouter_key:
            logger.warning("OpenRouter API key not configured")
            return None

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://presenceos.com",
            "X-Title": "PresenceOS Content Analyzer",
        }

        payload = {
            "model": FREE_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en analyse de contenu social media. "
                        "Tu reponds UNIQUEMENT en JSON valide, sans texte avant ou apres."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    return content
                else:
                    logger.error(
                        f"OpenRouter API error: {resp.status_code} - {resp.text}"
                    )
                    return None
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            return None

    def _parse_analysis(self, raw: str, post_count: int) -> ContentAnalysis:
        """Parse the LLM JSON response into ContentAnalysis."""
        try:
            # Extract JSON from the response (handle markdown code blocks)
            json_str = raw.strip()
            if json_str.startswith("```"):
                json_str = re.sub(r"^```(?:json)?\s*", "", json_str)
                json_str = re.sub(r"\s*```$", "", json_str)

            data = json.loads(json_str)
            tone_data = data.get("tone", {})
            vocab_data = data.get("vocabulary", {})

            tone = ToneMetrics(
                tone_formal=self._clamp(tone_data.get("tone_formal", 50)),
                tone_playful=self._clamp(tone_data.get("tone_playful", 50)),
                tone_bold=self._clamp(tone_data.get("tone_bold", 50)),
                tone_emotional=self._clamp(tone_data.get("tone_emotional", 50)),
                humor_level=self._clamp(tone_data.get("humor_level", 50)),
            )

            vocabulary = VocabularyAnalysis(
                favorite_words=vocab_data.get("favorite_words", [])[:20],
                favorite_emojis=vocab_data.get("favorite_emojis", [])[:10],
                cta_style=vocab_data.get("cta_style", ""),
                sentence_style=vocab_data.get("sentence_style", ""),
                hashtag_style=vocab_data.get("hashtag_style", "lowercase"),
                words_to_prefer=vocab_data.get("words_to_prefer", [])[:15],
                words_to_avoid=vocab_data.get("words_to_avoid", [])[:15],
            )

            return ContentAnalysis(
                tone=tone,
                vocabulary=vocabulary,
                summary=data.get("summary", ""),
                posts_analyzed=post_count,
                custom_instructions=data.get("custom_instructions", ""),
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {raw[:500]}")
            return ContentAnalysis(
                summary="Analyse partielle - erreur de parsing LLM",
                posts_analyzed=post_count,
            )

    def _basic_analysis(self, captions: list[str]) -> ContentAnalysis:
        """Fallback: basic statistical analysis without LLM."""
        all_text = " ".join(captions)
        words = all_text.lower().split()

        # Extract emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U0000FE00-\U0000FE0F"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "]+",
            flags=re.UNICODE,
        )
        emojis = emoji_pattern.findall(all_text)

        # Extract hashtags
        hashtags = re.findall(r"#\w+", all_text)

        # Average sentence length
        sentences = re.split(r"[.!?]+", all_text)
        avg_words = sum(len(s.split()) for s in sentences if s.strip()) / max(
            len(sentences), 1
        )

        # Determine formality (heuristic)
        informal_markers = ["!", "?", "haha", "lol", "omg", "btw", "...", "xd"]
        informal_count = sum(all_text.lower().count(m) for m in informal_markers)
        formality = max(10, min(90, 50 - informal_count * 3))

        # Unique emojis list
        unique_emojis = list(dict.fromkeys(emojis))[:10]

        return ContentAnalysis(
            tone=ToneMetrics(
                tone_formal=formality,
                tone_playful=min(90, 50 + informal_count * 2),
                tone_bold=50,
                tone_emotional=50,
                humor_level=min(90, 20 + informal_count * 3),
            ),
            vocabulary=VocabularyAnalysis(
                favorite_emojis=unique_emojis,
                hashtag_style="lowercase" if all(h == h.lower() for h in hashtags) else "mixed",
            ),
            summary=f"Analyse basique de {len(captions)} posts. Longueur moyenne: {avg_words:.0f} mots/phrase.",
            posts_analyzed=len(captions),
        )

    @staticmethod
    def _clamp(value: int, min_val: int = 0, max_val: int = 100) -> int:
        """Clamp value between min and max."""
        try:
            return max(min_val, min(max_val, int(value)))
        except (ValueError, TypeError):
            return 50

    # ── Store Results in DB ─────────────────────────────────────

    async def store_analysis(
        self,
        analysis: ContentAnalysis,
        brand_id: UUID,
        db: AsyncSession,
    ) -> dict:
        """
        Store analysis results in BrandVoice and KnowledgeItems.
        Returns a summary of what was updated.
        """
        updated = {"voice_updated": False, "knowledge_items_created": 0}

        # 1. Update BrandVoice
        result = await db.execute(
            select(BrandVoice).where(BrandVoice.brand_id == brand_id)
        )
        voice = result.scalar_one_or_none()

        if voice:
            voice.tone_formal = analysis.tone.tone_formal
            voice.tone_playful = analysis.tone.tone_playful
            voice.tone_bold = analysis.tone.tone_bold
            voice.tone_emotional = analysis.tone.tone_emotional

            if analysis.vocabulary.words_to_prefer:
                voice.words_to_prefer = analysis.vocabulary.words_to_prefer
            if analysis.vocabulary.words_to_avoid:
                voice.words_to_avoid = analysis.vocabulary.words_to_avoid
            if analysis.vocabulary.favorite_emojis:
                voice.emojis_allowed = analysis.vocabulary.favorite_emojis
            if analysis.vocabulary.hashtag_style:
                voice.hashtag_style = analysis.vocabulary.hashtag_style
            if analysis.custom_instructions:
                voice.custom_instructions = analysis.custom_instructions

            updated["voice_updated"] = True
        else:
            # Create BrandVoice if it doesn't exist
            voice = BrandVoice(
                brand_id=brand_id,
                tone_formal=analysis.tone.tone_formal,
                tone_playful=analysis.tone.tone_playful,
                tone_bold=analysis.tone.tone_bold,
                tone_emotional=analysis.tone.tone_emotional,
                words_to_prefer=analysis.vocabulary.words_to_prefer or None,
                words_to_avoid=analysis.vocabulary.words_to_avoid or None,
                emojis_allowed=analysis.vocabulary.favorite_emojis or None,
                hashtag_style=analysis.vocabulary.hashtag_style or "lowercase",
                custom_instructions=analysis.custom_instructions or None,
            )
            db.add(voice)
            updated["voice_updated"] = True

        # 2. Create KnowledgeItem for the tone analysis summary
        if analysis.summary:
            tone_item = KnowledgeItem(
                brand_id=brand_id,
                knowledge_type=KnowledgeType.OTHER,
                category="Analyse de contenu",
                title="Analyse du ton Instagram",
                content=analysis.summary,
                item_metadata={
                    "source": "content_analysis",
                    "posts_analyzed": analysis.posts_analyzed,
                    "tone_formal": analysis.tone.tone_formal,
                    "tone_playful": analysis.tone.tone_playful,
                    "tone_bold": analysis.tone.tone_bold,
                    "tone_emotional": analysis.tone.tone_emotional,
                    "humor_level": analysis.tone.humor_level,
                },
                is_active=True,
            )
            db.add(tone_item)
            updated["knowledge_items_created"] += 1

        # 3. Create KnowledgeItem for vocabulary patterns
        if analysis.vocabulary.favorite_words or analysis.vocabulary.cta_style:
            vocab_content_parts = []
            if analysis.vocabulary.favorite_words:
                vocab_content_parts.append(
                    f"Mots favoris: {', '.join(analysis.vocabulary.favorite_words)}"
                )
            if analysis.vocabulary.cta_style:
                vocab_content_parts.append(f"Style CTA: {analysis.vocabulary.cta_style}")
            if analysis.vocabulary.sentence_style:
                vocab_content_parts.append(
                    f"Style de phrases: {analysis.vocabulary.sentence_style}"
                )
            if analysis.vocabulary.favorite_emojis:
                vocab_content_parts.append(
                    f"Emojis favoris: {' '.join(analysis.vocabulary.favorite_emojis)}"
                )

            vocab_item = KnowledgeItem(
                brand_id=brand_id,
                knowledge_type=KnowledgeType.OTHER,
                category="Analyse de contenu",
                title="Vocabulaire et style Instagram",
                content="\n".join(vocab_content_parts),
                item_metadata={
                    "source": "content_analysis",
                    "favorite_words": analysis.vocabulary.favorite_words,
                    "favorite_emojis": analysis.vocabulary.favorite_emojis,
                    "cta_style": analysis.vocabulary.cta_style,
                    "sentence_style": analysis.vocabulary.sentence_style,
                    "hashtag_style": analysis.vocabulary.hashtag_style,
                },
                is_active=True,
            )
            db.add(vocab_item)
            updated["knowledge_items_created"] += 1

        await db.commit()

        return updated

    # ── Full Pipeline ───────────────────────────────────────────

    async def analyze_and_store(
        self,
        username: str,
        brand: Brand,
        db: AsyncSession,
    ) -> dict:
        """
        Full pipeline: fetch posts -> analyze -> store.
        Returns combined results.
        """
        # 1. Fetch posts
        posts = await self.fetch_instagram_posts(username)

        if not posts:
            return {
                "success": False,
                "error": f"Impossible de recuperer les posts de @{username}. Verifiez que le profil est public.",
                "posts_found": 0,
            }

        # 2. Analyze
        analysis = await self.analyze_content(posts, brand.name)

        # 3. Store
        stored = await self.store_analysis(analysis, brand.id, db)

        return {
            "success": True,
            "posts_found": len(posts),
            "posts_analyzed": analysis.posts_analyzed,
            "summary": analysis.summary,
            "tone": {
                "tone_formal": analysis.tone.tone_formal,
                "tone_playful": analysis.tone.tone_playful,
                "tone_bold": analysis.tone.tone_bold,
                "tone_emotional": analysis.tone.tone_emotional,
                "humor_level": analysis.tone.humor_level,
            },
            "vocabulary": {
                "favorite_words": analysis.vocabulary.favorite_words,
                "favorite_emojis": analysis.vocabulary.favorite_emojis,
                "cta_style": analysis.vocabulary.cta_style,
                "sentence_style": analysis.vocabulary.sentence_style,
                "hashtag_style": analysis.vocabulary.hashtag_style,
                "words_to_prefer": analysis.vocabulary.words_to_prefer,
            },
            "stored": stored,
            "custom_instructions": analysis.custom_instructions,
        }
