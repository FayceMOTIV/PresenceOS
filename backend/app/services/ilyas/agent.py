"""
PresenceOS - Ilyas Agent

Conversational CM AI powered by Claude Sonnet.
Features:
- Anthropic Claude with native tool calling
- Mem0 conversational memory
- GPT-4o Vision for food photo analysis
- BrandBrain integration
- CalendarIntelligence temporal context
- Intelligence modules: Google Trends, Instagram, TikTok, Reddit, YouTube (Sprint 3)
"""
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from anthropic import AsyncAnthropic
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.data.niches import detect_niche, get_niche_system_prompt
from app.models.ai_proposal import AIProposal
from app.models.brand import Brand, BrandVoice, KnowledgeItem
from app.models.cm_session import CmMessage, CmSession
from app.services.calendar_intelligence import CalendarIntelligence
from app.services.ilyas.memory import Mem0Memory
from app.services.ilyas.tools import ILYAS_TOOLS
from app.services.ilyas.vision import FoodVisionAnalyzer

logger = structlog.get_logger()

MAX_HISTORY_MESSAGES = 20
MAX_TOOL_ROUNDS = 3  # Max consecutive tool-use rounds to prevent infinite loops


class IlyasAgent:
    """Ilyas — the AI Community Manager, powered by Claude."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._client: AsyncAnthropic | None = None
        self._memory = Mem0Memory()
        self._vision = FoodVisionAnalyzer()
        # Intelligence modules — lazy init
        self._google_trends = None
        self._instagram = None
        self._tiktok = None
        self._reddit = None
        self._youtube = None

    # ── Lazy intelligence module accessors ──

    @property
    def google_trends(self):
        if self._google_trends is None:
            from app.services.ilyas.intelligence.google_trends import GoogleTrendsIntel
            self._google_trends = GoogleTrendsIntel()
        return self._google_trends

    @property
    def instagram(self):
        if self._instagram is None:
            from app.services.ilyas.intelligence.instagram_intel import InstagramIntel
            self._instagram = InstagramIntel()
        return self._instagram

    @property
    def tiktok(self):
        if self._tiktok is None:
            from app.services.ilyas.intelligence.tiktok_intel import TikTokIntel
            self._tiktok = TikTokIntel()
        return self._tiktok

    @property
    def reddit(self):
        if self._reddit is None:
            from app.services.ilyas.intelligence.reddit_intel import RedditIntel
            self._reddit = RedditIntel()
        return self._reddit

    @property
    def youtube(self):
        if self._youtube is None:
            from app.services.ilyas.intelligence.youtube_intel import YouTubeIntel
            self._youtube = YouTubeIntel()
        return self._youtube

    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError(
                    "Anthropic API key not configured. Set ANTHROPIC_API_KEY."
                )
            self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    # ── DNA context loader ──

    async def _get_dna_context(self, brand_id: str) -> str:
        """Load Business DNA from Firestore and format for system prompt."""
        try:
            from app.services.ilyas.onboarding_agent import OnboardingAgent
            agent = OnboardingAgent()
            dna = await agent.get_dna(str(brand_id))
            if dna and dna.onboarding_complete:
                return dna.to_system_prompt_section()
        except Exception as exc:
            logger.debug("DNA context load failed", error=str(exc))
        return ""

    # ── System prompt builder ────────────────────────────────────────

    async def _build_system_prompt(
        self,
        brand: Brand,
        user_id: str,
    ) -> str:
        """Build a rich system prompt with brand context, brain, and memories."""
        sections: list[str] = []

        # ── Niche-aware Persona (Niche Engine) ──
        business_type = brand.niche or (brand.brand_type.value if brand.brand_type else "restaurant")
        niche_profile = detect_niche(business_type)

        # Build Mem0 memories for niche prompt
        niche_memories_text = ""
        try:
            niche_memories = await self._memory.search(
                query="business DNA brand values audience editorial voice",
                user_id=user_id,
                limit=8,
            )
            if niche_memories:
                niche_memories_text = "\n".join(
                    m.get("memory", m.get("text", str(m)))
                    for m in niche_memories
                )
        except Exception as e:
            logger.warning("Mem0 niche memories retrieval failed", error=str(e))

        locations = ", ".join(brand.locations) if brand.locations else "non renseigné"
        brand_dna_for_niche = {
            "name": brand.name,
            "description": brand.description or "",
            "values": "",
            "voice": "",
            "target_audience": "",
            "location": locations,
            "memories": niche_memories_text,
        }

        niche_system_prompt = get_niche_system_prompt(niche_profile, brand_dna_for_niche)
        sections.append(niche_system_prompt)

        # ── Business DNA (Sprint 4) ──
        dna_section = await self._get_dna_context(str(brand.id))
        if dna_section:
            sections.append(dna_section)

        if brand.description:
            sections.append(f"Description : {brand.description}")

        # Voice
        if brand.voice:
            v = brand.voice
            voice_lines: list[str] = []
            formality = "formel" if v.tone_formal and v.tone_formal > 60 else "décontracté"
            playful = "joueur" if v.tone_playful and v.tone_playful > 60 else "sérieux"
            voice_lines.append(f"Ton : {formality}, {playful}")
            if v.custom_instructions:
                voice_lines.append(f"Instructions : {v.custom_instructions}")
            if v.words_to_avoid:
                voice_lines.append(f"Mots interdits : {', '.join(v.words_to_avoid)}")
            sections.append("VOIX DE LA MARQUE :\n" + "\n".join(voice_lines))

        # Knowledge base
        knowledge_list = getattr(brand, "knowledge_items", None) or []
        kb_lines: list[str] = []
        for ki in knowledge_list:
            if not ki.is_active:
                continue
            prefix = ki.knowledge_type.value.upper() if hasattr(ki, "knowledge_type") else "INFO"
            kb_lines.append(f"[{prefix}] {ki.title}: {ki.content}")
        if kb_lines:
            sections.append("BASE DE CONNAISSANCES :\n" + "\n".join(kb_lines[:30]))

        # Brand DNA
        if brand.brand_dna:
            sections.append(f"ADN de marque : {json.dumps(brand.brand_dna, ensure_ascii=False)}")

        # Constraints
        if brand.constraints:
            sections.append(f"Contraintes : {json.dumps(brand.constraints, ensure_ascii=False)}")

        # ── BrandBrain memories ──
        try:
            from app.services.brand_brain import BrandBrain
            brain = BrandBrain(brand.id, self.db)
            brain_memories = await brain.recall("content strategy preferences style", top_k=5)
            if brain_memories:
                brain_text = "\n".join(
                    f"- {m['content']} (confiance: {m['confidence']})"
                    for m in brain_memories
                )
                sections.append(f"MÉMOIRE DU CERVEAU IA :\n{brain_text}")
        except Exception as exc:
            logger.warning("BrandBrain recall failed", error=str(exc))

        # ── Mem0 conversational memories ──
        try:
            mem0_memories = await self._memory.search(
                query="restaurant preferences style content",
                user_id=user_id,
                limit=5,
            )
            if mem0_memories:
                mem_text = "\n".join(
                    f"- {m.get('memory', m.get('text', str(m)))}"
                    for m in mem0_memories
                )
                sections.append(f"SOUVENIRS DE CONVERSATION :\n{mem_text}")
        except Exception as exc:
            logger.debug("Mem0 search failed (may not be configured)", error=str(exc))

        # ── Temporal context ──
        try:
            cal = CalendarIntelligence()
            temporal_ctx = await cal.get_temporal_context(
                brand_locations=brand.locations,
                brand_niche=brand.niche,
                brand_constraints=brand.constraints,
            )
            if temporal_ctx:
                sections.append(temporal_ctx)
        except Exception as exc:
            logger.warning("Temporal context failed", error=str(exc))

        # ── Capabilities ──
        sections.append(
            "TES CAPACITÉS :\n"
            "- Créer des posts, Reels, Stories pour Instagram, Facebook, TikTok\n"
            "- Rédiger des légendes optimisées avec hashtags\n"
            "- Analyser des photos de plats (si l'utilisateur en envoie)\n"
            "- Conseiller sur la stratégie social media\n"
            "- Proposer un calendrier éditorial\n"
            "- Répondre aux avis Google\n"
            "\n"
            "INTELLIGENCE (utilise les outils disponibles) :\n"
            "- google_trends / compare_trends : tendances Google en France\n"
            "- instagram_competitor / instagram_hashtag : veille Instagram\n"
            "- tiktok_search / tiktok_video_info : tendances TikTok\n"
            "- reddit_search : discussions food/restaurant sur Reddit\n"
            "- youtube_search / youtube_channel : vidéos food YouTube\n"
            "\n"
            "Quand tu proposes du contenu concret (post, reel, story), "
            "emballe CHAQUE proposition dans un bloc <proposals> JSON :\n"
            "<proposals>\n"
            '[{"type":"post","platform":"instagram","caption":"...","hashtags":["..."]}]'
            "\n</proposals>\n"
            "Ce bloc sera parsé automatiquement."
        )

        # ── Rules ──
        sections.append(
            "RÈGLES :\n"
            "1. Réponds toujours en français.\n"
            "2. Sois concis : max 3-4 paragraphes.\n"
            "3. Personnalise TOUT au restaurant.\n"
            "4. Tu es Ilyas, pas « une IA » — ne dis jamais que tu es une IA.\n"
            "5. Si tu proposes du contenu, utilise le bloc <proposals>.\n"
            "6. Tutoie le restaurateur, sois chaleureux et pro."
        )

        return "\n\n".join(sections)

    # ── Session management (reuses CmSession with source='ilyas') ──

    async def get_or_create_session(
        self,
        brand_id: uuid.UUID,
        session_id: uuid.UUID | None = None,
    ) -> CmSession:
        if session_id:
            result = await self.db.execute(
                select(CmSession)
                .options(selectinload(CmSession.messages))
                .where(
                    CmSession.id == session_id,
                    CmSession.brand_id == brand_id,
                    CmSession.source == "ilyas",
                )
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        session = CmSession(brand_id=brand_id, source="ilyas")
        self.db.add(session)
        await self.db.flush()
        return session

    async def list_sessions(
        self,
        brand_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[CmSession], int]:
        count_result = await self.db.execute(
            select(func.count(CmSession.id)).where(
                CmSession.brand_id == brand_id,
                CmSession.source == "ilyas",
            )
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(CmSession)
            .where(CmSession.brand_id == brand_id, CmSession.source == "ilyas")
            .order_by(CmSession.updated_at.desc())
            .limit(min(limit, 50))
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def get_session_messages(
        self,
        session_id: uuid.UUID,
        brand_id: uuid.UUID,
    ) -> list[CmMessage]:
        result = await self.db.execute(
            select(CmMessage)
            .join(CmSession)
            .where(
                CmMessage.session_id == session_id,
                CmSession.brand_id == brand_id,
                CmSession.source == "ilyas",
            )
            .order_by(CmMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_session(
        self,
        session_id: uuid.UUID,
        brand_id: uuid.UUID,
    ) -> bool:
        result = await self.db.execute(
            select(CmSession).where(
                CmSession.id == session_id,
                CmSession.brand_id == brand_id,
                CmSession.source == "ilyas",
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return False
        await self.db.delete(session)
        await self.db.commit()
        return True

    # ── Tool dispatch ──

    async def _dispatch_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool call and return the result as a JSON string."""
        try:
            match tool_name:
                # Google Trends
                case "google_trends":
                    result = await self.google_trends.get_food_trends(
                        category=tool_input.get("category", "restaurant"),
                    )
                case "compare_trends":
                    result = await self.google_trends.compare_keywords(
                        keywords=tool_input.get("keywords", []),
                    )
                # Instagram
                case "instagram_competitor":
                    result = await self.instagram.analyze_competitor(
                        username=tool_input["username"],
                    )
                case "instagram_hashtag":
                    result = await self.instagram.analyze_hashtag(
                        tag=tool_input["tag"],
                    )
                # TikTok
                case "tiktok_search":
                    result = await self.tiktok.search_videos(
                        keyword=tool_input["keyword"],
                        count=tool_input.get("count", 10),
                    )
                case "tiktok_video_info":
                    result = await self.tiktok.get_video_info(
                        url=tool_input["url"],
                    )
                # Reddit
                case "reddit_search":
                    result = await self.reddit.search_food_discussions(
                        query=tool_input["query"],
                        subreddits=tool_input.get("subreddits"),
                    )
                # YouTube
                case "youtube_search":
                    result = await self.youtube.search_food_videos(
                        query=tool_input["query"],
                        max_results=tool_input.get("max_results", 10),
                    )
                case "youtube_channel":
                    result = await self.youtube.analyze_channel(
                        channel_id=tool_input["channel_id"],
                    )
                # Action tools (not yet wired — return placeholder)
                case "generate_post" | "analyze_photo" | "schedule_post":
                    result = {"status": "not_implemented", "tool": tool_name}
                case _:
                    result = {"error": f"Unknown tool: {tool_name}"}

            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            logger.warning("Tool dispatch failed", tool=tool_name, error=str(exc))
            return json.dumps({"error": str(exc)})

    # ── Chat ──

    async def chat(
        self,
        brand: Brand,
        session: CmSession,
        user_message: str,
        user_id: str,
        image_url: str | None = None,
    ) -> CmMessage:
        """Send a message to Ilyas and get a response."""
        # 1. If image provided, analyze it first
        vision_analysis: str | None = None
        if image_url:
            brand_ctx = f"{brand.name} — {brand.niche or 'restaurant'}"
            vision_analysis = await self._vision.analyze_food_photo(image_url, brand_ctx)

        # 2. Build the user message content (with vision if applicable)
        full_user_message = user_message
        if vision_analysis:
            full_user_message += f"\n\n[Analyse de la photo envoyée]\n{vision_analysis}"

        # 3. Save user message
        user_msg = CmMessage(
            session_id=session.id,
            role="user",
            content=user_message,  # Store original (without vision analysis)
        )
        self.db.add(user_msg)
        session.message_count = (session.message_count or 0) + 1
        await self.db.flush()

        # 4. Build system prompt
        system_prompt = await self._build_system_prompt(brand, user_id)

        # 5. Load conversation history
        history_result = await self.db.execute(
            select(CmMessage)
            .where(CmMessage.session_id == session.id)
            .order_by(CmMessage.created_at.desc())
            .limit(MAX_HISTORY_MESSAGES)
        )
        history_msgs = list(reversed(history_result.scalars().all()))

        # Build Claude messages
        claude_messages: list[dict[str, Any]] = []
        for msg in history_msgs:
            claude_messages.append({"role": msg.role, "content": msg.content})

        # Replace last user message with the vision-enriched version
        if vision_analysis and claude_messages and claude_messages[-1]["role"] == "user":
            claude_messages[-1]["content"] = full_user_message

        # 6. Call Claude with tool calling (multi-turn loop)
        client = self._get_client()
        ai_text = ""
        tokens_used = 0
        try:
            for _round in range(MAX_TOOL_ROUNDS + 1):
                response = await client.messages.create(
                    model=settings.ilyas_model,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=claude_messages,
                    tools=ILYAS_TOOLS,
                    max_tokens=1024,
                    temperature=0.7,
                )
                tokens_used += (
                    (response.usage.input_tokens + response.usage.output_tokens)
                    if response.usage else 0
                )

                # If no tool use, extract text and break
                if response.stop_reason != "tool_use":
                    text_parts = [
                        block.text for block in response.content
                        if hasattr(block, "text")
                    ]
                    ai_text = "\n".join(text_parts)
                    break

                # Process tool calls
                assistant_content = response.content
                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        logger.info(
                            "Ilyas tool call",
                            tool=block.name,
                            input=block.input,
                        )
                        result_str = await self._dispatch_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })

                # Append assistant turn (with tool_use blocks) + tool results
                claude_messages.append({"role": "assistant", "content": assistant_content})
                claude_messages.append({"role": "user", "content": tool_results})
            else:
                # Exhausted tool rounds — extract whatever text we have
                text_parts = [
                    block.text for block in response.content
                    if hasattr(block, "text")
                ]
                ai_text = "\n".join(text_parts) or (
                    "J'ai fait mes recherches mais j'ai besoin d'un instant de plus. "
                    "Peux-tu reformuler ta question ?"
                )

        except Exception as exc:
            logger.error("Ilyas Claude call failed", error=str(exc))
            ai_text = (
                "Désolé, je rencontre un souci technique. "
                "Réessaie dans quelques instants !"
            )
            tokens_used = 0

        # 7. Parse proposals
        proposals = self._extract_proposals(ai_text)

        # 8. Save assistant message
        assistant_msg = CmMessage(
            session_id=session.id,
            role="assistant",
            content=ai_text,
            proposals=proposals if proposals else None,
            tokens_used=tokens_used,
        )
        self.db.add(assistant_msg)
        session.message_count = (session.message_count or 0) + 1

        # 9. Auto-title
        if session.title == "Nouvelle conversation" and len(history_msgs) <= 2:
            session.title = user_message[:80]

        await self.db.flush()

        # 10. Create AIProposal rows
        if proposals:
            await self._create_proposals(brand.id, proposals)

        await self.db.commit()
        await self.db.refresh(assistant_msg)

        # 11. Store in Mem0 (fire and forget — don't block response)
        try:
            await self._memory.add(
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": ai_text},
                ],
                user_id=user_id,
                metadata={"brand_id": str(brand.id), "brand_name": brand.name},
            )
        except Exception as exc:
            logger.debug("Mem0 storage failed (may not be configured)", error=str(exc))

        return assistant_msg

    # ── Proposal extraction (same as CMChatService) ──

    _PROPOSALS_RE = re.compile(
        r"<proposals>\s*(.*?)\s*</proposals>", re.DOTALL
    )

    def _extract_proposals(self, text: str) -> list[dict[str, Any]] | None:
        match = self._PROPOSALS_RE.search(text)
        if not match:
            return None
        raw = match.group(1).strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                parsed = [parsed]
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse Ilyas proposals JSON", raw=raw[:200])
        return None

    async def _create_proposals(
        self,
        brand_id: uuid.UUID,
        proposals: list[dict[str, Any]],
    ) -> None:
        for p in proposals:
            proposal = AIProposal(
                brand_id=brand_id,
                proposal_type=p.get("type", "post"),
                platform=p.get("platform", "instagram"),
                caption=p.get("caption"),
                hashtags=p.get("hashtags"),
                source="ilyas",
                status="pending",
                confidence_score=0.88,
            )
            self.db.add(proposal)

    # ── Context debug endpoint ──

    async def get_context(self, brand: Brand, user_id: str) -> dict[str, Any]:
        """Return the full context Ilyas would use (for debugging)."""
        system_prompt = await self._build_system_prompt(brand, user_id)

        mem0_memories: list[dict] = []
        try:
            mem0_memories = await self._memory.get_all(user_id)
        except Exception as e:
            logger.warning("Mem0 get_all failed for context", error=str(e), user_id=user_id)

        return {
            "system_prompt_length": len(system_prompt),
            "system_prompt_preview": system_prompt[:500],
            "mem0_memories_count": len(mem0_memories),
            "model": settings.ilyas_model,
        }
