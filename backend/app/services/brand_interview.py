"""
PresenceOS - Brand Interview Service

AI-powered conversational interview that learns about a brand,
then stores structured data into Brand, BrandVoice, and KnowledgeItems.
Sessions are persisted in Redis (resumable, TTL 7 days).
"""
import json
import structlog
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import openai
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.brand import Brand, BrandVoice, KnowledgeItem, KnowledgeType

logger = structlog.get_logger()

# ── Redis helpers ───────────────────────────────────────────────────

SESSION_TTL = 7 * 24 * 3600  # 7 days
KEY_PREFIX = "presenceos:interview:"


async def _get_redis():
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        logger.warning("Redis not available for interview sessions")
        return None


# ── Question Bank ───────────────────────────────────────────────────

QUESTION_BANK = {
    "identity": {
        "label": "Identite",
        "priority": "critical",
        "questions": [
            "Ou est situe votre etablissement / entreprise ? (ville, quartier)",
            "Decrivez votre activite en 2-3 phrases.",
            "Qui sont vos clients typiques ? (age, profil, habitudes)",
            "Y a-t-il des contraintes specifiques ? (halal, bio, horaires, saisonnier...)",
        ],
        "targets": ["brand.locations", "brand.description", "brand.target_persona", "brand.constraints"],
    },
    "voice": {
        "label": "Ton & Style",
        "priority": "critical",
        "questions": [
            "Quel ton preferez-vous sur les reseaux ? (decontracte, pro, drole, premium...)",
            "Y a-t-il des mots ou expressions a eviter absolument ?",
            "Y a-t-il des mots ou expressions qui vous representent bien ?",
            "Utilisez-vous des emojis ? Lesquels preferez-vous ?",
            "Des consignes particulieres pour l'IA ? (tutoiement, vouvoiement, style...)",
        ],
        "targets": ["brand_voice.tone", "brand_voice.words_to_avoid", "brand_voice.words_to_prefer", "brand_voice.emojis_allowed", "brand_voice.custom_instructions"],
    },
    "menu": {
        "label": "Carte / Menu",
        "priority": "important",
        "brand_types": ["restaurant"],
        "questions": [
            "Quels sont vos plats signatures ? (nom, description, prix)",
            "Quelles categories avez-vous ? (entrees, plats, desserts, boissons...)",
            "Avez-vous des specialites ou des plats du jour recurrents ?",
        ],
        "targets": ["knowledge_item.menu"],
    },
    "products": {
        "label": "Produits / Services",
        "priority": "important",
        "brand_types": ["saas", "ecommerce", "service"],
        "questions": [
            "Quels sont vos produits ou services principaux ?",
            "Quel est votre produit phare ou best-seller ?",
        ],
        "targets": ["knowledge_item.product"],
    },
    "offers": {
        "label": "Offres & Promos",
        "priority": "optional",
        "questions": [
            "Avez-vous des offres en cours ou recurrentes ? (happy hour, menu midi, promo...)",
        ],
        "targets": ["knowledge_item.offer"],
    },
    "team": {
        "label": "Equipe",
        "priority": "optional",
        "questions": [
            "Souhaitez-vous mettre en avant des membres de votre equipe ? (chef, fondateur...)",
        ],
        "targets": ["knowledge_item.team"],
    },
    "proof": {
        "label": "Preuves sociales",
        "priority": "optional",
        "questions": [
            "Avez-vous des avis clients, temoignages ou recompenses a mettre en avant ?",
        ],
        "targets": ["knowledge_item.proof"],
    },
}


def _get_categories_for_brand(brand_type: str) -> list[str]:
    """Return relevant question categories for a brand type."""
    categories = []
    for cat_key, cat_data in QUESTION_BANK.items():
        allowed_types = cat_data.get("brand_types")
        if allowed_types and brand_type not in allowed_types:
            continue
        categories.append(cat_key)
    return categories


# ── GPT System Prompt Builder ───────────────────────────────────────

def _build_system_prompt(brand_name: str, brand_type: str, collected_data: dict, remaining_categories: list[str]) -> str:
    categories_desc = []
    for cat in remaining_categories:
        info = QUESTION_BANK.get(cat, {})
        categories_desc.append(f"- \"{cat}\" = {info.get('label', cat)} ({info.get('priority', 'optional')}): {', '.join(info.get('questions', []))}")

    collected_summary = json.dumps(collected_data, ensure_ascii=False, indent=2) if collected_data else "Rien encore"

    return f"""Tu es l'assistant IA de PresenceOS. Tu menes une interview conversationnelle avec le proprietaire de la marque "{brand_name}" (type: {brand_type}).

TON ROLE:
- Poser UNE question a la fois, de maniere naturelle et chaleureuse
- Reformuler et confirmer ce que tu comprends avant de passer a la suite
- Extraire des informations structurees de chaque reponse

DONNEES DEJA COLLECTEES:
{collected_summary}

CATEGORIES RESTANTES A COUVRIR:
{chr(10).join(categories_desc) if categories_desc else "Toutes les categories ont ete couvertes!"}

REGLES:
- Parle en francais, tutoie le user
- Sois concis mais chaleureux
- Si le user donne plusieurs infos d'un coup, extrais-les TOUTES dans extracted_data
- CRITIQUE: Quand le user mentionne des plats, produits, offres, ou membres d'equipe, tu DOIS creer des knowledge_items dans extracted_data. Chaque plat = 1 knowledge_item avec target "knowledge_item"
- Si une categorie n'est pas pertinente, passe a la suivante
- Quand toutes les categories critiques et importantes sont couvertes, propose de terminer
- Apres avoir extrait les donnees, pose la question suivante (ne repete JAMAIS la meme reponse)

Tu DOIS retourner ta reponse au format JSON suivant (et RIEN d'autre):
{{
  "message": "Ta reponse conversationnelle ici...",
  "extracted_data": [
    {{"target": "brand.locations", "value": ["Bourg-en-Bresse"]}},
    {{"target": "brand.description", "value": "Restaurant familial..."}},
    {{"target": "brand.target_persona", "value": {{"name": "Familles", "age_range": "25-45"}}}},
    {{"target": "brand.constraints", "value": {{"halal": true}}}},
    {{"target": "brand_voice.tone_formal", "value": 30}},
    {{"target": "brand_voice.tone_playful", "value": 70}},
    {{"target": "brand_voice.words_to_avoid", "value": ["cheap", "discount"]}},
    {{"target": "brand_voice.words_to_prefer", "value": ["fait maison", "artisanal"]}},
    {{"target": "brand_voice.emojis_allowed", "value": ["🍔", "❤️", "🔥"]}},
    {{"target": "brand_voice.custom_instructions", "value": "Toujours tutoyer..."}},
    {{"target": "knowledge_item", "knowledge_type": "menu", "title": "Tajine d'agneau", "content": "Notre tajine signature aux pruneaux et amandes", "category": "Plats", "metadata": {{"price": 16.90, "is_bestseller": true}}}}
  ],
  "categories_covered": ["identity"],
  "is_complete": false
}}

IMPORTANT:
- "extracted_data" ne contient QUE les nouvelles infos de ce message (peut etre vide [])
- "categories_covered" = liste de CLES de categories couvertes (ex: ["identity", "menu"], PAS les labels)
- "is_complete" = true seulement quand toutes les categories critiques+importantes sont faites
- Quand le user mentionne des plats avec prix, CREE un knowledge_item pour CHAQUE plat (ne les ignore pas!)
- Si le user dit quelque chose de hors sujet ou ambigu, pose une question de clarification et retourne extracted_data: []
- Ne repete JAMAIS le meme message. Avance toujours vers la prochaine question.
"""


# ── Main Service ────────────────────────────────────────────────────

class BrandInterviewService:
    """Service for conducting brand interviews via AI chat."""

    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def _load_session(self, brand_id: str) -> dict | None:
        r = await _get_redis()
        if not r:
            return None
        data = await r.get(f"{KEY_PREFIX}{brand_id}")
        if data:
            return json.loads(data)
        return None

    async def _save_session(self, brand_id: str, session: dict):
        r = await _get_redis()
        if not r:
            return
        await r.set(f"{KEY_PREFIX}{brand_id}", json.dumps(session, ensure_ascii=False, default=str), ex=SESSION_TTL)

    async def start_or_resume(self, brand_id: str, db: AsyncSession) -> dict:
        """Start a new interview or resume an existing one."""
        # Load brand
        result = await db.execute(
            select(Brand).where(Brand.id == UUID(brand_id))
        )
        brand = result.scalar_one_or_none()
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")

        # Try to resume existing session
        session = await self._load_session(brand_id)
        if session and session.get("phase") != "completed":
            logger.info("Resuming interview session", brand_id=brand_id)
            return {
                "messages": session.get("messages", []),
                "completeness": await self._calculate_completeness(brand_id, db),
                "is_new": False,
            }

        # Start new session
        categories = _get_categories_for_brand(brand.brand_type.value if brand.brand_type else "other")
        session = {
            "brand_id": brand_id,
            "brand_name": brand.name,
            "brand_type": brand.brand_type.value if brand.brand_type else "other",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "categories_done": [],
            "collected_data": {},
            "phase": "active",
        }

        # Generate first AI message
        first_message = await self._generate_ai_message(session, is_first=True)
        session["messages"].append({
            "role": "assistant",
            "content": first_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        await self._save_session(brand_id, session)

        logger.info("Started new interview session", brand_id=brand_id)
        return {
            "messages": session["messages"],
            "completeness": await self._calculate_completeness(brand_id, db),
            "is_new": True,
        }

    async def process_message(self, brand_id: str, user_message: str, db: AsyncSession) -> dict:
        """Process a user message and return AI response with extracted data."""
        session = await self._load_session(brand_id)
        if not session:
            # Auto-start if no session
            await self.start_or_resume(brand_id, db)
            session = await self._load_session(brand_id)

        # Add user message
        session["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Call GPT
        brand_name = session.get("brand_name", "")
        brand_type = session.get("brand_type", "other")
        categories_done = session.get("categories_done", [])
        all_categories = _get_categories_for_brand(brand_type)
        remaining = [c for c in all_categories if c not in categories_done]

        system_prompt = _build_system_prompt(
            brand_name=brand_name,
            brand_type=brand_type,
            collected_data=session.get("collected_data", {}),
            remaining_categories=remaining,
        )

        # Build messages for GPT (keep last 20 messages for context)
        gpt_messages = [{"role": "system", "content": system_prompt}]
        for msg in session["messages"][-20:]:
            gpt_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=gpt_messages,
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            raw_response = response.choices[0].message.content
            parsed = json.loads(raw_response)

        except (json.JSONDecodeError, Exception) as e:
            logger.error("GPT interview response parse error", error=str(e))
            ai_message = "Desole, je n'ai pas bien compris. Peux-tu reformuler ?"
            parsed = {"message": ai_message, "extracted_data": [], "categories_covered": [], "is_complete": False}

        ai_message = parsed.get("message", "...")
        extracted_data = parsed.get("extracted_data", [])
        categories_covered = parsed.get("categories_covered", [])
        is_complete = parsed.get("is_complete", False)

        # Store extracted data in DB
        stored_items = []
        if extracted_data:
            stored_items = await self._parse_and_store(extracted_data, brand_id, db)
            # Update session collected_data
            for item in extracted_data:
                target = item.get("target", "")
                if target.startswith("brand.") or target.startswith("brand_voice."):
                    session.setdefault("collected_data", {})[target] = item.get("value")

        # Update categories done
        for cat in categories_covered:
            if cat not in session.get("categories_done", []):
                session.setdefault("categories_done", []).append(cat)

        # Add AI message to session
        session["messages"].append({
            "role": "assistant",
            "content": ai_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "extracted_items": [{"type": s.get("type", ""), "title": s.get("title", "")} for s in stored_items],
        })

        if is_complete:
            session["phase"] = "completed"

        await self._save_session(brand_id, session)

        completeness = await self._calculate_completeness(brand_id, db)

        return {
            "ai_message": ai_message,
            "extracted_items": stored_items,
            "completeness": completeness,
            "is_complete": is_complete,
        }

    async def get_status(self, brand_id: str, db: AsyncSession) -> dict:
        """Get interview status and completeness for a brand."""
        session = await self._load_session(brand_id)
        completeness = await self._calculate_completeness(brand_id, db)

        # Count knowledge items
        result = await db.execute(
            select(func.count(KnowledgeItem.id)).where(
                KnowledgeItem.brand_id == UUID(brand_id),
                KnowledgeItem.is_active == True,
            )
        )
        knowledge_count = result.scalar() or 0

        return {
            "completeness": completeness,
            "knowledge_count": knowledge_count,
            "has_active_session": session is not None and session.get("phase") == "active",
        }

    # ── Private helpers ─────────────────────────────────────────────

    async def _generate_ai_message(self, session: dict, is_first: bool = False) -> str:
        """Generate the first AI message to kick off the interview."""
        brand_name = session.get("brand_name", "ta marque")
        brand_type = session.get("brand_type", "other")

        type_labels = {
            "restaurant": "restaurant",
            "saas": "SaaS",
            "ecommerce": "e-commerce",
            "service": "entreprise de services",
            "personal": "marque personnelle",
            "other": "activite",
        }
        type_label = type_labels.get(brand_type, "activite")

        return (
            f"Salut ! Je suis ton assistant PresenceOS. "
            f"Je vais te poser quelques questions pour bien comprendre {brand_name} "
            f"et generer du contenu qui te ressemble vraiment.\n\n"
            f"On commence ? Dis-moi d'abord : ou est situe ton {type_label} ? "
            f"(ville, quartier, adresse...)"
        )

    async def _parse_and_store(self, extracted_data: list[dict], brand_id: str, db: AsyncSession) -> list[dict]:
        """Parse extracted data from GPT and store in DB."""
        stored = []
        bid = UUID(brand_id)

        for item in extracted_data:
            target = item.get("target", "")
            if not target:
                continue

            value = item.get("value")

            try:
                if target == "knowledge_item":
                    # knowledge_items don't use "value" — they have title/content/etc
                    ki = await self._create_knowledge_item(bid, item, db)
                    if ki:
                        stored.append({"type": "knowledge", "title": ki.title, "knowledge_type": item.get("knowledge_type", "other")})

                elif target.startswith("brand.") and value is not None:
                    field = target.replace("brand.", "")
                    await self._update_brand_field(bid, field, value, db)
                    stored.append({"type": "brand", "title": field, "value": str(value)[:100]})

                elif target.startswith("brand_voice.") and value is not None:
                    field = target.replace("brand_voice.", "")
                    await self._update_voice_field(bid, field, value, db)
                    stored.append({"type": "voice", "title": field, "value": str(value)[:100]})

            except Exception as e:
                logger.error("Failed to store interview data", target=target, error=str(e))
                continue

        if stored:
            await db.commit()
            logger.info("Stored interview data", brand_id=brand_id, items_count=len(stored))

        return stored

    async def _update_brand_field(self, brand_id: UUID, field: str, value: Any, db: AsyncSession):
        """Update a single field on the Brand model."""
        allowed_fields = {"locations", "description", "target_persona", "constraints", "content_pillars", "website_url"}
        if field not in allowed_fields:
            return

        result = await db.execute(select(Brand).where(Brand.id == brand_id))
        brand = result.scalar_one_or_none()
        if not brand:
            return

        setattr(brand, field, value)
        db.add(brand)

    async def _update_voice_field(self, brand_id: UUID, field: str, value: Any, db: AsyncSession):
        """Update a single field on BrandVoice, creating it if needed."""
        result = await db.execute(select(BrandVoice).where(BrandVoice.brand_id == brand_id))
        voice = result.scalar_one_or_none()

        if not voice:
            voice = BrandVoice(brand_id=brand_id)
            db.add(voice)
            await db.flush()

        # Map tone descriptions to slider values
        if field == "tone":
            if isinstance(value, dict):
                for tone_key, tone_val in value.items():
                    tone_field = f"tone_{tone_key}" if not tone_key.startswith("tone_") else tone_key
                    if hasattr(voice, tone_field):
                        setattr(voice, tone_field, tone_val)
            return

        # Direct field mapping
        voice_fields = {
            "tone_formal", "tone_playful", "tone_bold", "tone_technical", "tone_emotional",
            "words_to_avoid", "words_to_prefer", "emojis_allowed", "custom_instructions",
            "example_phrases", "primary_language", "hashtag_style",
        }
        if field in voice_fields:
            setattr(voice, field, value)

    async def _create_knowledge_item(self, brand_id: UUID, data: dict, db: AsyncSession) -> KnowledgeItem | None:
        """Create a KnowledgeItem, deduplicating by title + type."""
        title = data.get("title", "").strip()
        knowledge_type_str = data.get("knowledge_type", "other")
        content = data.get("content", title)

        if not title:
            return None

        # Map string to enum
        try:
            kt = KnowledgeType(knowledge_type_str)
        except ValueError:
            kt = KnowledgeType.OTHER

        # Check for duplicate
        existing = await db.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.brand_id == brand_id,
                KnowledgeItem.title == title,
                KnowledgeItem.knowledge_type == kt,
            )
        )
        if existing.scalar_one_or_none():
            logger.debug("Skipping duplicate knowledge item", title=title)
            return None

        ki = KnowledgeItem(
            brand_id=brand_id,
            knowledge_type=kt,
            title=title,
            content=content,
            category=data.get("category"),
            item_metadata=data.get("metadata"),
            is_featured=data.get("metadata", {}).get("is_bestseller", False) if isinstance(data.get("metadata"), dict) else False,
        )
        db.add(ki)
        await db.flush()

        # Generate embedding
        try:
            from app.services.embeddings import EmbeddingService
            embedding_svc = EmbeddingService()
            embedding = await embedding_svc.generate_embedding(f"{title} {content}")
            ki.embedding = embedding
        except Exception as e:
            logger.warning("Failed to generate embedding for knowledge item", title=title, error=str(e))

        return ki

    async def _calculate_completeness(self, brand_id: str, db: AsyncSession) -> dict:
        """Calculate completeness scores based on filled DB fields."""
        bid = UUID(brand_id)

        # Load brand
        result = await db.execute(select(Brand).where(Brand.id == bid))
        brand = result.scalar_one_or_none()
        if not brand:
            return {"overall": 0, "identity": 0, "voice": 0, "knowledge": 0}

        # Identity score (brand fields)
        identity_score = 0
        identity_checks = [
            (brand.locations, 30),
            (brand.description, 30),
            (brand.target_persona, 20),
            (brand.constraints, 20),
        ]
        for value, weight in identity_checks:
            if value:
                identity_score += weight

        # Voice score
        voice_score = 0
        result = await db.execute(select(BrandVoice).where(BrandVoice.brand_id == bid))
        voice = result.scalar_one_or_none()
        if voice:
            # Check if tones have been customized (not all defaults)
            tones_customized = any([
                voice.tone_formal != 50,
                voice.tone_playful != 50,
                voice.tone_bold != 50,
                voice.tone_emotional != 50,
            ])
            if tones_customized:
                voice_score += 30
            if voice.words_to_avoid:
                voice_score += 20
            if voice.words_to_prefer:
                voice_score += 20
            if voice.custom_instructions:
                voice_score += 20
            if voice.emojis_allowed:
                voice_score += 10

        # Knowledge score
        result = await db.execute(
            select(
                KnowledgeItem.knowledge_type,
                func.count(KnowledgeItem.id),
            ).where(
                KnowledgeItem.brand_id == bid,
                KnowledgeItem.is_active == True,
            ).group_by(KnowledgeItem.knowledge_type)
        )
        type_counts = {row[0].value: row[1] for row in result.all()}
        total_items = sum(type_counts.values())
        knowledge_score = min(100, total_items * 15)  # Each item = 15 points, max 100

        # Overall
        overall = round((identity_score * 0.35 + voice_score * 0.30 + knowledge_score * 0.35))

        return {
            "overall": overall,
            "identity": identity_score,
            "voice": voice_score,
            "knowledge": knowledge_score,
            "knowledge_by_type": type_counts,
        }
