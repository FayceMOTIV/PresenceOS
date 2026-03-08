"""
PresenceOS - CM Chat Service

Conversational Community Manager AI using GPT-4o.
Builds a rich system prompt from the Brand Brain (voice, KB, constraints),
streams conversation context, parses <proposals> blocks into AIProposal rows.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.ai_proposal import AIProposal
from app.models.brand import Brand, BrandVoice, KnowledgeItem
from app.models.cm_session import CmMessage, CmSession
from app.models.dish import Dish
from app.models.media import MediaAsset, MediaType
from app.models.publishing import SocialConnector, SocialPlatform, ConnectorStatus
from app.models.video_credits import VideoCredits
from app.services.calendar_intelligence import CalendarIntelligence

logger = structlog.get_logger()

# Max messages sent to OpenAI per turn (to stay within context window)
MAX_HISTORY_MESSAGES = 20


class CMChatService:
    """Conversational CM AI powered by GPT-4o."""

    MODEL = "gpt-4o"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not settings.openai_api_key:
                raise RuntimeError(
                    "OpenAI API key not configured. Set OPENAI_API_KEY in environment."
                )
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    # ── System prompt builder ────────────────────────────────────────────────

    async def _build_system_prompt(self, brand: Brand) -> str:
        """Build a rich system prompt from brand data, including temporal context."""
        sections: list[str] = []

        # Identity
        niche = brand.niche or (brand.brand_type.value if brand.brand_type else "business")
        locations = ", ".join(brand.locations) if brand.locations else "non renseigné"
        sections.append(
            f"Tu es le Community Manager IA de « {brand.name} ».\n"
            f"Niche : {niche}.\n"
            f"Localisation : {locations}.\n"
            f"Tu parles en français, de manière professionnelle et chaleureuse."
        )

        # Description
        if brand.description:
            sections.append(f"Description : {brand.description}")

        # Brand voice
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

        # Knowledge base items
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

        # ── Temporal context (F1: Conscience Temporelle) ──
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
            logger.warning("Temporal context failed, skipping", error=str(exc))

        # ── Weather context (Open-Meteo) ──
        try:
            from app.services.weather_service import WeatherService

            weather_svc = WeatherService()
            weather_ctx = await weather_svc.get_current_weather(brand.locations)
            if weather_ctx:
                sections.append(weather_ctx)
        except Exception as exc:
            logger.warning("Weather context failed, skipping", error=str(exc))

        # ── Superpowers: enrichissement contextuel ──
        superpower_fns = [
            self._social_accounts_section,
            self._video_credits_section,
            self._menu_section,
            self._media_library_section,
            self._proposals_section,
            self._visual_style_section,
        ]
        for section_fn in superpower_fns:
            try:
                section = await section_fn(brand.id)
                if section:
                    sections.append(section)
            except Exception as exc:
                logger.warning(
                    "Superpower section failed",
                    fn=section_fn.__name__,
                    error=str(exc),
                )

        # Capabilities
        sections.append(
            "TES CAPACITÉS :\n"
            "- Répondre sur la stratégie social media\n"
            "- Proposer des posts (Reel, Story, Post) pour les plateformes connectées\n"
            "- Rédiger des légendes optimisées\n"
            "- Analyser les performances passées et proposer des améliorations\n"
            "- Suggérer du contenu basé sur le menu et les plats\n"
            "- Conseiller sur le calendrier éditorial\n"
            "- Référencer les assets médias existants\n"
            "- Proposer des vidéos si crédits disponibles\n"
            "\n"
            "Quand tu proposes du contenu concret (post, reel, story), "
            "emballe CHAQUE proposition dans un bloc <proposals> JSON :\n"
            "<proposals>\n"
            '[{"type":"post","platform":"instagram","caption":"...","hashtags":["..."]}'
            "\n</proposals>\n"
            "Ce bloc sera parsé automatiquement pour créer des propositions dans l'app."
        )

        # Rules
        sections.append(
            "RÈGLES :\n"
            "1. Réponds toujours en français.\n"
            "2. Sois concis : max 3-4 paragraphes par réponse.\n"
            "3. Personnalise TOUT au business de l'utilisateur.\n"
            "4. Ne mentionne jamais que tu es une IA.\n"
            "5. Si tu proposes du contenu, utilise le bloc <proposals>."
        )

        return "\n\n".join(sections)

    # ── Superpower sections (fail-safe, each returns Optional[str]) ─────────

    async def _social_accounts_section(self, brand_id: uuid.UUID) -> str | None:
        """List connected/disconnected social platforms."""
        result = await self.db.execute(
            select(SocialConnector).where(SocialConnector.brand_id == brand_id)
        )
        connectors = list(result.scalars().all())
        if not connectors:
            return "COMPTES SOCIAUX : Aucun compte connecté. Suggère de connecter Instagram, TikTok, Facebook."

        lines: list[str] = []
        all_platforms = {p.value for p in SocialPlatform}
        connected_platforms: set[str] = set()
        for c in connectors:
            status_icon = "✓" if c.status == ConnectorStatus.CONNECTED else "✗"
            platform_name = c.platform.value if hasattr(c.platform, "value") else str(c.platform)
            lines.append(f"{platform_name} {status_icon}")
            if c.status == ConnectorStatus.CONNECTED:
                connected_platforms.add(platform_name)

        missing = all_platforms - connected_platforms
        if missing:
            lines.append(f"Non connectés : {', '.join(sorted(missing))}")

        return "COMPTES SOCIAUX : " + " | ".join(lines)

    async def _video_credits_section(self, brand_id: uuid.UUID) -> str | None:
        """Show video credit balance."""
        result = await self.db.execute(
            select(VideoCredits).where(VideoCredits.brand_id == brand_id)
        )
        credits = result.scalar_one_or_none()
        if not credits:
            return "VIDÉO : Pas de crédits vidéo. Suggère l'achat si le client demande une vidéo."

        remaining = credits.credits_remaining or 0
        if remaining > 0:
            return f"CRÉDITS VIDÉO : {remaining} crédits restants (Kling 3.0). Tu peux proposer des vidéos."
        return "VIDÉO : 0 crédits restants. Suggère l'achat de crédits si le client veut une vidéo."

    async def _menu_section(self, brand_id: uuid.UUID) -> str | None:
        """List top dishes from the menu."""
        result = await self.db.execute(
            select(Dish)
            .where(Dish.brand_id == brand_id, Dish.is_available == True)
            .order_by(Dish.is_featured.desc(), Dish.display_order.asc())
            .limit(15)
        )
        dishes = list(result.scalars().all())
        if not dishes:
            return None

        dish_parts: list[str] = []
        for d in dishes:
            tag = " (vedette)" if d.is_featured else ""
            cat = f" [{d.category}]" if d.category else ""
            dish_parts.append(f"{d.name}{tag}{cat}")

        return "MENU SPÉCIALITÉS : " + ", ".join(dish_parts)

    async def _media_library_section(self, brand_id: uuid.UUID) -> str | None:
        """Count available media assets by type."""
        result = await self.db.execute(
            select(MediaAsset.media_type, func.count(MediaAsset.id))
            .where(MediaAsset.brand_id == brand_id, MediaAsset.is_archived == False)
            .group_by(MediaAsset.media_type)
        )
        counts = {row[0]: row[1] for row in result.all()}
        if not counts:
            return "MÉDIATHÈQUE : Vide. Suggère d'uploader des photos/vidéos."

        photos = counts.get(MediaType.IMAGE, 0)
        videos = counts.get(MediaType.VIDEO, 0)
        return f"MÉDIATHÈQUE : {photos} photos, {videos} vidéos disponibles."

    async def _proposals_section(self, brand_id: uuid.UUID) -> str | None:
        """Show proposal stats and top performers."""
        # Count by status
        result = await self.db.execute(
            select(AIProposal.status, func.count(AIProposal.id))
            .where(AIProposal.brand_id == brand_id)
            .group_by(AIProposal.status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}
        if not status_counts:
            return None

        pending = status_counts.get("pending", 0)
        published = status_counts.get("published", 0)
        approved = status_counts.get("approved", 0)

        parts = [f"{pending} en attente, {approved} approuvées, {published} publiées"]

        # Top 3 published with highest confidence
        if published > 0:
            top_result = await self.db.execute(
                select(AIProposal)
                .where(
                    AIProposal.brand_id == brand_id,
                    AIProposal.status == "published",
                )
                .order_by(AIProposal.confidence_score.desc())
                .limit(3)
            )
            top_proposals = list(top_result.scalars().all())
            if top_proposals:
                top_parts: list[str] = []
                for p in top_proposals:
                    caption_preview = (p.caption or "")[:60]
                    score = f" ({p.confidence_score:.0%})" if p.confidence_score else ""
                    top_parts.append(f"'{caption_preview}'{score}")
                parts.append("Top publiés : " + " | ".join(top_parts))

        return "HISTORIQUE PROPOSITIONS : " + ". ".join(parts)

    async def _visual_style_section(self, brand_id: uuid.UUID) -> str | None:
        """Get visual brain preferences if available."""
        try:
            from app.services.visual_brain import VisualBrain

            vb = VisualBrain(brand_id=brand_id, db=self.db)
            status = await vb.get_visual_brain_status()
            if status and status.get("total_memories", 0) > 0:
                maturity = status.get("maturity_pct", 0)
                return f"STYLE VISUEL : Cerveau visuel actif ({maturity}% maturité). Adapte tes suggestions visuelles au style appris."
        except Exception:
            pass
        return None

    # ── Session management ───────────────────────────────────────────────────

    async def get_or_create_session(
        self, brand_id: uuid.UUID, session_id: uuid.UUID | None = None
    ) -> CmSession:
        """Get existing session or create a new one."""
        if session_id:
            result = await self.db.execute(
                select(CmSession)
                .options(selectinload(CmSession.messages))
                .where(CmSession.id == session_id, CmSession.brand_id == brand_id)
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        # Create new session
        session = CmSession(brand_id=brand_id)
        self.db.add(session)
        await self.db.flush()
        return session

    async def list_sessions(
        self, brand_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[CmSession], int]:
        """List sessions for a brand, ordered by most recent."""
        from sqlalchemy import func

        count_result = await self.db.execute(
            select(func.count(CmSession.id)).where(CmSession.brand_id == brand_id)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(CmSession)
            .where(CmSession.brand_id == brand_id)
            .order_by(CmSession.updated_at.desc())
            .limit(min(limit, 50))
            .offset(offset)
        )
        sessions = list(result.scalars().all())
        return sessions, total

    async def get_session_messages(
        self, session_id: uuid.UUID, brand_id: uuid.UUID
    ) -> list[CmMessage]:
        """Get all messages for a session."""
        result = await self.db.execute(
            select(CmMessage)
            .join(CmSession)
            .where(
                CmMessage.session_id == session_id,
                CmSession.brand_id == brand_id,
            )
            .order_by(CmMessage.created_at.asc())
        )
        return list(result.scalars().all())

    # ── Chat completion ──────────────────────────────────────────────────────

    async def send_message(
        self,
        brand: Brand,
        session: CmSession,
        user_message: str,
    ) -> CmMessage:
        """Send a user message and get AI response."""
        # 1. Save user message
        user_msg = CmMessage(
            session_id=session.id,
            role="user",
            content=user_message,
        )
        self.db.add(user_msg)
        session.message_count = (session.message_count or 0) + 1
        await self.db.flush()

        # 2. Build messages for OpenAI (async — includes temporal context)
        system_prompt = await self._build_system_prompt(brand)

        # Load recent conversation history
        history_result = await self.db.execute(
            select(CmMessage)
            .where(CmMessage.session_id == session.id)
            .order_by(CmMessage.created_at.desc())
            .limit(MAX_HISTORY_MESSAGES)
        )
        history_msgs = list(reversed(history_result.scalars().all()))

        openai_messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        for msg in history_msgs:
            openai_messages.append({"role": msg.role, "content": msg.content})

        # 3. Call GPT-4o
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self.MODEL,
                messages=openai_messages,
                max_tokens=1024,
                temperature=0.7,
            )
            ai_text = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
        except Exception as exc:
            logger.error("CM Chat GPT-4o call failed", error=str(exc))
            ai_text = (
                "Désolé, je rencontre un problème technique. "
                "Réessayez dans quelques instants."
            )
            tokens_used = 0

        # 4. Parse proposals from response
        proposals = self._extract_proposals(ai_text)

        # 5. Save assistant message
        assistant_msg = CmMessage(
            session_id=session.id,
            role="assistant",
            content=ai_text,
            proposals=proposals if proposals else None,
            tokens_used=tokens_used,
        )
        self.db.add(assistant_msg)
        session.message_count = (session.message_count or 0) + 1

        # 6. Auto-title session from first user message
        if session.title == "Nouvelle conversation" and len(history_msgs) <= 2:
            session.title = user_message[:80]

        await self.db.flush()

        # 7. Create AIProposal rows for each parsed proposal
        if proposals:
            await self._create_proposals(brand.id, proposals)

        await self.db.commit()
        await self.db.refresh(assistant_msg)

        return assistant_msg

    # ── Proposal extraction ──────────────────────────────────────────────────

    _PROPOSALS_RE = re.compile(
        r"<proposals>\s*(.*?)\s*</proposals>", re.DOTALL
    )

    def _extract_proposals(self, text: str) -> list[dict[str, Any]] | None:
        """Extract JSON proposals from <proposals>...</proposals> blocks."""
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
            logger.warning("Failed to parse proposals JSON", raw=raw[:200])
        return None

    async def _create_proposals(
        self,
        brand_id: uuid.UUID,
        proposals: list[dict[str, Any]],
    ) -> None:
        """Create AIProposal rows from parsed proposals."""
        for p in proposals:
            proposal = AIProposal(
                brand_id=brand_id,
                proposal_type=p.get("type", "post"),
                platform=p.get("platform", "instagram"),
                caption=p.get("caption"),
                hashtags=p.get("hashtags"),
                source="cm_chat",
                status="pending",
                confidence_score=0.85,
            )
            self.db.add(proposal)

    # ── Session deletion ─────────────────────────────────────────────────────

    async def delete_session(
        self, session_id: uuid.UUID, brand_id: uuid.UUID
    ) -> bool:
        """Delete a session and all its messages."""
        result = await self.db.execute(
            select(CmSession).where(
                CmSession.id == session_id, CmSession.brand_id == brand_id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True
