"""
PresenceOS - Conversation Engine (Refonte v2)

Redis-backed state machine simplifie pour conversations Telegram/WhatsApp.
Maximum 3 interactions avant publication.

Flow:
  IDLE ──photo──→ ENRICHING ──reponse──→ CONFIRMING ──bouton──→ IDLE

States:
  IDLE       → Aucune conversation active
  ENRICHING  → Photo recue, IA a reagi, attend contexte ou "publie"
  CONFIRMING → Preview envoyee, attend confirmation/modification/annulation
"""
import json
import enum
import uuid
import structlog
from datetime import datetime, timezone
from typing import Any

import openai

from app.core.config import settings
from app.prompts.caption_generator import (
    build_caption_system_prompt,
    build_caption_user_prompt,
    build_photo_reaction_prompt,
    INDUSTRY_GUIDELINES,
)

logger = structlog.get_logger()


# ── States ──────────────────────────────────────────────────────────

class ConversationState(str, enum.Enum):
    IDLE = "idle"
    ENRICHING = "enriching"
    CONFIRMING = "confirming"


# ── Context (serialized to Redis) ──────────────────────────────────

class ConversationContext:
    """Serializable conversation context stored in Redis."""

    def __init__(
        self,
        sender_phone: str,
        brand_id: str,
        config_id: str,
    ):
        self.sender_phone = sender_phone
        self.brand_id = brand_id
        self.config_id = config_id
        self.state = ConversationState.IDLE
        self.media_urls: list[str] = []
        self.media_keys: list[str] = []
        self.media_types: list[str] = []
        self.media_analyses: list[dict] = []
        self.user_context: str = ""
        self.generated_caption: str = ""
        self.platforms: list[str] = ["instagram"]
        self.pending_post_ids: list[str] = []
        self.last_activity: str = datetime.now(timezone.utc).isoformat()
        self.message_count: int = 0

    def to_dict(self) -> dict:
        return {
            "sender_phone": self.sender_phone,
            "brand_id": self.brand_id,
            "config_id": self.config_id,
            "state": self.state.value,
            "media_urls": self.media_urls,
            "media_keys": self.media_keys,
            "media_types": self.media_types,
            "media_analyses": self.media_analyses,
            "user_context": self.user_context,
            "generated_caption": self.generated_caption,
            "platforms": self.platforms,
            "pending_post_ids": self.pending_post_ids,
            "last_activity": self.last_activity,
            "message_count": self.message_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        ctx = cls(
            sender_phone=data["sender_phone"],
            brand_id=data["brand_id"],
            config_id=data["config_id"],
        )
        ctx.state = ConversationState(data.get("state", "idle"))
        ctx.media_urls = data.get("media_urls", [])
        ctx.media_keys = data.get("media_keys", [])
        ctx.media_types = data.get("media_types", [])
        ctx.media_analyses = data.get("media_analyses", [])
        ctx.user_context = data.get("user_context", "")
        ctx.generated_caption = data.get("generated_caption", "")
        ctx.platforms = data.get("platforms", ["instagram"])
        ctx.pending_post_ids = data.get("pending_post_ids", [])
        ctx.last_activity = data.get("last_activity", datetime.now(timezone.utc).isoformat())
        ctx.message_count = data.get("message_count", 0)
        return ctx

    def touch(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc).isoformat()
        self.message_count += 1


# ── Redis Store ────────────────────────────────────────────────────

class ConversationStore:
    """Redis-backed conversation store."""

    KEY_PREFIX = "presenceos:conv:"
    TTL = settings.conversation_ttl_seconds

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                r = aioredis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                )
                await r.ping()
                self._redis = r
            except Exception:
                logger.warning("Redis not available, using in-memory fallback")
                self._redis = _InMemoryRedis()
        return self._redis

    def _key(self, phone: str) -> str:
        return f"{self.KEY_PREFIX}{phone.lstrip('+').replace(' ', '')}"

    async def get(self, phone: str) -> ConversationContext | None:
        """Get conversation context for a phone number."""
        r = await self._get_redis()
        data = await r.get(self._key(phone))
        if data is None:
            return None
        try:
            return ConversationContext.from_dict(json.loads(data))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Invalid conversation data in Redis", phone=phone, error=str(e))
            return None

    async def save(self, ctx: ConversationContext):
        """Save conversation context."""
        ctx.touch()
        r = await self._get_redis()
        await r.set(
            self._key(ctx.sender_phone),
            json.dumps(ctx.to_dict()),
            ex=self.TTL,
        )

    async def delete(self, phone: str):
        """Delete conversation context (reset to IDLE)."""
        r = await self._get_redis()
        await r.delete(self._key(phone))

    async def close(self):
        if self._redis and hasattr(self._redis, "close"):
            await self._redis.close()


class _InMemoryRedis:
    """Fallback for when redis.asyncio is not available (testing, dev)."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self._store[key] = value

    async def delete(self, key: str):
        self._store.pop(key, None)


# ── Conversation Engine ────────────────────────────────────────────

class ConversationEngine:
    """
    Simplified conversation engine (3 states max).

    Flow: Photo → ENRICHING → CONFIRMING → Publish
    """

    def __init__(self):
        self.store = ConversationStore()
        self._media_downloader = None

    async def handle_message(
        self,
        sender_phone: str,
        msg_type: str,
        message: dict,
        brand_id: str,
        config_id: str,
        messaging_service=None,
        media_downloader=None,
    ) -> None:
        """
        Main entry point: route a message through the state machine.

        Args:
            sender_phone: Sender identifier (phone number or chat_id)
            msg_type: 'text', 'image', 'video', 'audio', 'interactive'
            message: Normalized message dict
            brand_id: Resolved brand UUID
            config_id: Resolved autopilot config UUID
            messaging_service: Optional messaging service (defaults to WhatsAppService)
            media_downloader: Optional async callable(media_id) -> (bytes, mime_type)
        """
        if messaging_service is None:
            from app.services.whatsapp import WhatsAppService
            messaging_service = WhatsAppService()

        wa = messaging_service
        self._media_downloader = media_downloader

        # Get or create context
        ctx = await self.store.get(sender_phone)
        if ctx is None:
            ctx = ConversationContext(
                sender_phone=sender_phone,
                brand_id=brand_id,
                config_id=config_id,
            )

        # Handle special commands regardless of state
        if msg_type == "text":
            text_body = message.get("text", {}).get("body", "").strip().lower()
            if text_body in ("annuler", "cancel", "stop", "reset", "/cancel"):
                await self.store.delete(sender_phone)
                await wa.send_text_message(
                    sender_phone,
                    "Pas de souci, annule ! Envoie-moi une autre photo quand tu veux 😊",
                )
                return
            if text_body in ("aide", "help", "?", "/help", "/start"):
                await wa.send_text_message(
                    sender_phone,
                    "👋 Salut ! Je suis ton assistant PresenceOS.\n\n"
                    "📸 Envoie-moi une photo → je cree ta publication\n"
                    "🎤 Envoie un vocal → je comprends tes instructions\n"
                    "❌ 'annuler' → reinitialiser la conversation\n"
                    "ℹ️ 'aide' → ce message\n\n"
                    "C'est parti ! Envoie-moi une photo 📸",
                )
                return

        # Handle interactive button replies
        if msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                button_id = interactive["button_reply"]["id"]
                await self._handle_button(ctx, button_id, wa)
                return

        # State machine dispatch
        state = ctx.state

        if state == ConversationState.IDLE:
            await self._handle_idle(ctx, msg_type, message, wa)

        elif state == ConversationState.ENRICHING:
            await self._handle_enriching(ctx, msg_type, message, wa)

        elif state == ConversationState.CONFIRMING:
            await self._handle_confirming(ctx, msg_type, message, wa)

    # ── State Handlers ─────────────────────────────────────────────

    async def _handle_idle(self, ctx, msg_type, message, wa):
        """IDLE → first message. Only photos start the flow."""
        if msg_type in ("image", "video"):
            # Download, store and analyze
            await self._ingest_media(ctx, msg_type, message)

            # Load brand info for personalized reaction
            brand_info = await self._get_brand_info(ctx.brand_id)
            brand_name = brand_info.get("name", "Entreprise")
            brand_type = brand_info.get("brand_type", "other")
            analysis = ctx.media_analyses[-1] if ctx.media_analyses else {}

            # Generate a warm reaction
            reaction = await self._generate_photo_reaction(analysis, brand_name, brand_type)

            # Send reaction + buttons
            body = (
                f"{reaction}\n\n"
                "Tu veux ajouter quelque chose ? Par exemple :\n"
                "• Un prix (\"12€\")\n"
                "• Une promo (\"offert pour 2 achetes\")\n"
                "• Des horaires (\"disponible ce midi\")\n"
                "• Ou autre chose !\n\n"
                "Sinon, je prepare ta publication directement 👇"
            )

            await wa.send_interactive_buttons(
                ctx.sender_phone,
                body_text=body,
                buttons=[
                    {"id": "enrich_publish", "title": "C'est bon, publie !"},
                    {"id": "enrich_add", "title": "Je veux ajouter"},
                ],
                header_text="📸 Nouvelle photo",
            )

            ctx.state = ConversationState.ENRICHING
            await self.store.save(ctx)

        elif msg_type == "text":
            await wa.send_text_message(
                ctx.sender_phone,
                "Envoie-moi une photo et je m'occupe de tout ! 📸",
            )

        elif msg_type == "audio":
            await wa.send_text_message(
                ctx.sender_phone,
                "Envoie-moi d'abord une photo, puis tu pourras me donner des instructions en vocal 🎤",
            )

    async def _handle_enriching(self, ctx, msg_type, message, wa):
        """ENRICHING → photo received, waiting for context or 'publish'."""
        if msg_type in ("image", "video"):
            # Additional media
            await self._ingest_media(ctx, msg_type, message)
            n = len(ctx.media_urls)
            await wa.send_interactive_buttons(
                ctx.sender_phone,
                body_text=f"📸 Photo ajoutee ! ({n} photo{'s' if n > 1 else ''}).\n"
                          "Envoie-en d'autres ou dis-moi quand c'est bon !",
                buttons=[
                    {"id": "enrich_publish", "title": "C'est tout !"},
                    {"id": "enrich_add", "title": "J'en ajoute"},
                ],
            )
            await self.store.save(ctx)

        elif msg_type == "text":
            text_body = message.get("text", {}).get("body", "").strip()
            if text_body:
                ctx.user_context = text_body
                await self._generate_and_preview(ctx, wa)

        elif msg_type == "audio":
            # Transcribe and treat as context
            transcription = await self._transcribe_voice(message)
            if transcription:
                ctx.user_context = transcription
                await self._generate_and_preview(ctx, wa)
            else:
                await wa.send_text_message(
                    ctx.sender_phone,
                    "Je n'ai pas reussi a comprendre le vocal. Reessaie ou ecris ton message 😊",
                )

    async def _handle_confirming(self, ctx, msg_type, message, wa):
        """CONFIRMING → preview sent, waiting for action."""
        if msg_type == "text":
            # Treat as modification instruction
            text_body = message.get("text", {}).get("body", "").strip()
            if text_body:
                await self._regenerate_caption(ctx, text_body, wa)

        elif msg_type in ("image", "video"):
            # New photo = new flow
            ctx.media_urls = []
            ctx.media_keys = []
            ctx.media_types = []
            ctx.media_analyses = []
            ctx.user_context = ""
            ctx.generated_caption = ""
            ctx.state = ConversationState.IDLE
            await self.store.save(ctx)
            # Re-enter as IDLE with the new media
            await self._handle_idle(ctx, msg_type, message, wa)

        elif msg_type == "audio":
            # Transcribe and treat as modification
            transcription = await self._transcribe_voice(message)
            if transcription:
                await self._regenerate_caption(ctx, transcription, wa)

    # ── Button Handler ──────────────────────────────────────────────

    async def _handle_button(self, ctx, button_id: str, wa):
        """Handle interactive button replies."""

        # ENRICHING buttons
        if button_id == "enrich_publish":
            # Generate caption without additional context
            await self._generate_and_preview(ctx, wa)
            return

        if button_id == "enrich_add":
            await wa.send_text_message(
                ctx.sender_phone,
                "Dis-moi ce que tu veux ajouter ! 📝\n"
                "(prix, promo, horaires, description...)",
            )
            return

        # CONFIRMING buttons
        if button_id == "confirm_publish":
            await self._publish_posts(ctx, wa)
            return

        if button_id == "confirm_edit":
            await wa.send_text_message(
                ctx.sender_phone,
                "Dis-moi ce que tu veux changer ! ✏️\n"
                "(ex: \"enleve les hashtags\", \"ajoute notre adresse\", \"plus court\")",
            )
            return

        if button_id == "confirm_cancel":
            await self.store.delete(ctx.sender_phone)
            await wa.send_text_message(
                ctx.sender_phone,
                "Pas de souci, annule ! Envoie-moi une autre photo quand tu veux 😊",
            )
            return

        # Legacy approve/reject buttons (from autopilot)
        if button_id.startswith("approve_") or button_id.startswith("reject_"):
            try:
                from app.api.webhooks.whatsapp import _handle_button_reply
                await _handle_button_reply(button_id, ctx.sender_phone)
            except Exception as e:
                logger.warning("Legacy button handling failed", error=str(e))
            return

        logger.warning("Unknown button_id", button_id=button_id)

    # ── Core Logic ──────────────────────────────────────────────────

    async def _generate_and_preview(self, ctx, wa):
        """Generate caption and send preview for confirmation."""
        # Load brand info
        brand_info = await self._get_brand_info(ctx.brand_id)
        platforms = await self._get_config_platforms(ctx.config_id)
        ctx.platforms = platforms if platforms else ["instagram"]

        # Build analysis summary
        analyses_text = ""
        for i, analysis in enumerate(ctx.media_analyses):
            desc = analysis.get("description", "Image")
            objects = ", ".join(analysis.get("detected_objects", []))
            mood = analysis.get("mood", "")
            analyses_text += f"Photo {i+1}: {desc}"
            if objects:
                analyses_text += f" (objets: {objects})"
            if mood:
                analyses_text += f" (ambiance: {mood})"
            analyses_text += "\n"

        # Generate caption
        caption = await self._generate_caption(
            analyses_text=analyses_text,
            user_context=ctx.user_context,
            brand_info=brand_info,
            platforms=ctx.platforms,
        )
        ctx.generated_caption = caption

        # Build preview
        platforms_str = " + ".join(p.capitalize() for p in ctx.platforms)
        media_str = f"{len(ctx.media_urls)} photo{'s' if len(ctx.media_urls) > 1 else ''}"

        body = (
            f"📱 Voici ta publication :\n\n"
            f"\"{caption}\"\n\n"
            f"📸 {platforms_str} • {media_str}\n\n"
            f"Ca te plait ?"
        )

        await wa.send_interactive_buttons(
            ctx.sender_phone,
            body_text=body,
            buttons=[
                {"id": "confirm_publish", "title": "Publier maintenant"},
                {"id": "confirm_edit", "title": "Modifier le texte"},
                {"id": "confirm_cancel", "title": "Annuler"},
            ],
            header_text="Confirmation",
        )

        ctx.state = ConversationState.CONFIRMING
        await self.store.save(ctx)

    async def _regenerate_caption(self, ctx, instruction: str, wa):
        """Regenerate caption based on user instruction."""
        brand_info = await self._get_brand_info(ctx.brand_id)
        brand_type = brand_info.get("brand_type", "other")
        guidelines = INDUSTRY_GUIDELINES.get(brand_type, INDUSTRY_GUIDELINES["other"])
        label = guidelines["terminology_label"].capitalize()

        prompt = (
            f"Voici la publication actuelle :\n\"{ctx.generated_caption}\"\n\n"
            f"{label} demande : \"{instruction}\"\n\n"
            f"Regenere la publication en tenant compte de cette demande. "
            f"Garde le meme style et la meme longueur sauf si demande contraire."
        )

        caption = await self._call_gpt(
            system_prompt=self._build_caption_system_prompt(brand_info),
            user_prompt=prompt,
        )
        ctx.generated_caption = caption

        platforms_str = " + ".join(p.capitalize() for p in ctx.platforms)
        media_str = f"{len(ctx.media_urls)} photo{'s' if len(ctx.media_urls) > 1 else ''}"

        body = (
            f"📱 Voici la nouvelle version :\n\n"
            f"\"{caption}\"\n\n"
            f"📸 {platforms_str} • {media_str}\n\n"
            f"Ca te plait ?"
        )

        await wa.send_interactive_buttons(
            ctx.sender_phone,
            body_text=body,
            buttons=[
                {"id": "confirm_publish", "title": "Publier maintenant"},
                {"id": "confirm_edit", "title": "Modifier encore"},
                {"id": "confirm_cancel", "title": "Annuler"},
            ],
            header_text="Confirmation",
        )

        await self.store.save(ctx)

    async def _publish_posts(self, ctx, wa):
        """Create PendingPosts and confirm to user."""
        from app.core.database import async_session_maker
        from app.models.autopilot import PendingPost, PendingPostStatus

        try:
            async with async_session_maker() as db:
                for platform in ctx.platforms:
                    pending = PendingPost(
                        config_id=ctx.config_id,
                        brand_id=ctx.brand_id,
                        platform=platform,
                        caption=ctx.generated_caption,
                        media_urls=ctx.media_urls if ctx.media_urls else None,
                        ai_reasoning=f"Conversation ({len(ctx.media_urls)} medias, contexte: {ctx.user_context[:100] if ctx.user_context else 'aucun'})",
                        status=PendingPostStatus.PENDING,
                    )
                    db.add(pending)
                    ctx.pending_post_ids.append(str(pending.id))
                await db.commit()

            platforms_str = " + ".join(p.capitalize() for p in ctx.platforms)
            await wa.send_text_message(
                ctx.sender_phone,
                f"✅ Publie sur {platforms_str} ! 🎉\n\n"
                "Tu recevras une confirmation quand ce sera en ligne.\n"
                "Envoie-moi une autre photo quand tu veux !",
            )

            # Trigger content generation
            try:
                from app.workers.celery_app import celery_app
                for post_id in ctx.pending_post_ids:
                    celery_app.send_task(
                        "app.workers.tasks.generate_whatsapp_content",
                        args=[post_id],
                    )
            except Exception as e:
                logger.warning("Failed to trigger content generation", error=str(e))

            logger.info(
                "Posts created from conversation",
                brand_id=ctx.brand_id,
                platforms=ctx.platforms,
                media_count=len(ctx.media_urls),
            )

        except Exception as e:
            logger.error("Post creation failed", error=str(e))
            await wa.send_text_message(
                ctx.sender_phone,
                "Oups, erreur lors de la publication. Reessaie ! 🙏",
            )

        await self.store.delete(ctx.sender_phone)

    # ── Media Helpers ───────────────────────────────────────────────

    async def _ingest_media(self, ctx, msg_type: str, message: dict):
        """Download, store and analyze media."""
        from app.services.storage import get_storage_service
        from app.models.media import MediaAsset, MediaSource, MediaType
        from app.core.database import async_session_maker

        media_info = message.get(msg_type, {})
        media_id = media_info.get("id")
        if not media_id:
            return

        try:
            if self._media_downloader:
                file_bytes, mime_type = await self._media_downloader(media_id)
            else:
                from app.api.webhooks.whatsapp import _download_whatsapp_media
                file_bytes, mime_type = await _download_whatsapp_media(media_id)

            # Store in S3
            storage = get_storage_service()
            ext = "jpg" if msg_type == "image" else "mp4"
            key = storage.generate_key(ctx.brand_id, msg_type, f"conv_{media_id}.{ext}")
            upload_result = await storage.upload_bytes(
                file_bytes, key, content_type=mime_type
            )

            ctx.media_urls.append(upload_result["url"])
            ctx.media_keys.append(upload_result["key"])
            ctx.media_types.append(msg_type)

            # Save MediaAsset in DB
            mt = MediaType.IMAGE if msg_type == "image" else MediaType.VIDEO
            async with async_session_maker() as db:
                asset = MediaAsset(
                    brand_id=ctx.brand_id,
                    storage_key=upload_result["key"],
                    public_url=upload_result["url"],
                    media_type=mt,
                    mime_type=mime_type,
                    file_size=upload_result["size"],
                    source=MediaSource.WHATSAPP,
                    whatsapp_media_id=media_id,
                )
                db.add(asset)
                await db.commit()

            # Vision analysis
            if msg_type == "image":
                try:
                    from app.services.vision import VisionService
                    vision = VisionService()
                    analysis = await vision.analyze_image(file_bytes, mime_type)
                    ctx.media_analyses.append(analysis)
                except Exception as e:
                    logger.warning("Vision analysis failed", error=str(e))
                    ctx.media_analyses.append({
                        "description": "Photo recue",
                        "detected_objects": [],
                        "mood": "unknown",
                        "tags": [],
                    })
            else:
                ctx.media_analyses.append({
                    "description": "Video recue",
                    "detected_objects": [],
                    "mood": "unknown",
                    "tags": [],
                })

        except Exception as e:
            logger.error("Media ingestion failed", error=str(e), media_id=media_id)
            # Add a fallback analysis so the flow can continue
            ctx.media_analyses.append({
                "description": "Media recu (analyse non disponible)",
                "detected_objects": [],
                "mood": "unknown",
                "tags": [],
            })

    async def _transcribe_voice(self, message: dict) -> str | None:
        """Transcribe a voice message, return text or None."""
        from app.services.transcription import TranscriptionService

        audio_info = message.get("audio", {})
        media_id = audio_info.get("id")
        if not media_id:
            return None

        try:
            if self._media_downloader:
                file_bytes, mime_type = await self._media_downloader(media_id)
            else:
                from app.api.webhooks.whatsapp import _download_whatsapp_media
                file_bytes, mime_type = await _download_whatsapp_media(media_id)

            ext = "ogg" if "ogg" in mime_type else "mp3"
            transcriber = TranscriptionService()
            text = await transcriber.transcribe(file_bytes, filename=f"voice.{ext}")
            return text if text else None

        except Exception as e:
            logger.error("Voice transcription failed", error=str(e))
            return None

    # ── GPT-4o Prompts ──────────────────────────────────────────────

    async def _generate_photo_reaction(self, analysis: dict, brand_name: str, brand_type: str = "other") -> str:
        """Generate a warm, short reaction to a photo."""
        description = analysis.get("description", "une photo")
        objects = ", ".join(analysis.get("detected_objects", []))

        user_prompt = (
            f"Analyse de la photo : {description}\n"
        )
        if objects:
            user_prompt += f"Objets : {objects}\n"
        user_prompt += (
            "\nGenere une reaction courte, chaleureuse et enthousiaste (1-2 phrases max). "
            "Decris ce que tu vois de maniere naturelle. Utilise 1-2 emojis. "
            "Exemple : \"Magnifique tajine aux legumes, ca a l'air delicieux ! 😍\"\n"
            "Reponds UNIQUEMENT avec la reaction, rien d'autre."
        )

        system_prompt = build_photo_reaction_prompt(brand_name, brand_type)

        try:
            return await self._call_gpt(system_prompt, user_prompt)
        except Exception as e:
            logger.warning("Photo reaction generation failed", error=str(e))
            return f"📸 Belle photo ! Ca donne envie !"

    async def _generate_caption(
        self,
        analyses_text: str,
        user_context: str,
        brand_info: dict,
        platforms: list[str],
    ) -> str:
        """Generate a publication caption with GPT-4o."""
        system_prompt = self._build_caption_system_prompt(brand_info)
        brand_type = brand_info.get("brand_type", "other")

        user_prompt = build_caption_user_prompt(
            analyses_text=analyses_text,
            user_context=user_context,
            platforms=platforms,
            brand_type=brand_type,
        )

        try:
            return await self._call_gpt(system_prompt, user_prompt)
        except Exception as e:
            logger.error("Caption generation failed", error=str(e))
            # Fallback caption with industry-appropriate hashtags
            guidelines = INDUSTRY_GUIDELINES.get(brand_type, INDUSTRY_GUIDELINES["other"])
            fallback_tags = " ".join(guidelines["fallback_hashtags"])
            if user_context:
                return f"{user_context}\n\n{fallback_tags}"
            return f"Decouvrez-nous !\n\n{fallback_tags}"

    def _build_caption_system_prompt(self, brand_info: dict) -> str:
        """Build the system prompt for caption generation."""
        return build_caption_system_prompt(
            brand_name=brand_info.get("name", "Entreprise"),
            brand_type=brand_info.get("brand_type", "other"),
            brand_description=brand_info.get("description", ""),
            voice=brand_info.get("voice"),
            target_persona=brand_info.get("target_persona"),
            locations=brand_info.get("locations"),
            constraints=brand_info.get("constraints"),
        )

    async def _call_gpt(self, system_prompt: str, user_prompt: str) -> str:
        """Call GPT-4o and return the text response."""
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    # ── DB Helpers ──────────────────────────────────────────────────

    async def _get_brand_name(self, brand_id: str) -> str:
        """Get brand name from DB."""
        try:
            from app.core.database import async_session_maker
            from app.models.brand import Brand
            from sqlalchemy import select

            async with async_session_maker() as db:
                result = await db.execute(
                    select(Brand.name).where(Brand.id == brand_id)
                )
                name = result.scalar_one_or_none()
                return name or "Restaurant"
        except Exception:
            return "Restaurant"

    async def _get_brand_info(self, brand_id: str) -> dict:
        """Get brand info + voice for prompt building."""
        try:
            from app.core.database import async_session_maker
            from app.models.brand import Brand, BrandVoice
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload

            async with async_session_maker() as db:
                result = await db.execute(
                    select(Brand)
                    .options(joinedload(Brand.voice))
                    .where(Brand.id == brand_id)
                )
                brand = result.scalar_one_or_none()
                if not brand:
                    return {"name": "Entreprise", "brand_type": "other", "description": "", "voice": {}}

                voice_data = {}
                if brand.voice:
                    voice_data = {
                        "tone_formal": brand.voice.tone_formal,
                        "tone_playful": brand.voice.tone_playful,
                        "tone_bold": brand.voice.tone_bold,
                        "tone_emotional": brand.voice.tone_emotional,
                        "custom_instructions": brand.voice.custom_instructions,
                        "words_to_prefer": brand.voice.words_to_prefer,
                        "words_to_avoid": brand.voice.words_to_avoid,
                        "emojis_allowed": brand.voice.emojis_allowed,
                        "max_emojis_per_post": brand.voice.max_emojis_per_post,
                        "example_phrases": brand.voice.example_phrases,
                    }

                return {
                    "name": brand.name,
                    "brand_type": brand.brand_type.value if brand.brand_type else "other",
                    "description": brand.description or "",
                    "voice": voice_data,
                    "target_persona": brand.target_persona,
                    "locations": brand.locations,
                    "constraints": brand.constraints,
                }
        except Exception as e:
            logger.warning("Failed to load brand info", error=str(e))
            return {"name": "Entreprise", "brand_type": "other", "description": "", "voice": {}}

    async def _get_config_platforms(self, config_id: str) -> list[str]:
        """Get default platforms from AutopilotConfig."""
        try:
            from app.core.database import async_session_maker
            from app.models.autopilot import AutopilotConfig
            from sqlalchemy import select

            async with async_session_maker() as db:
                result = await db.execute(
                    select(AutopilotConfig.platforms).where(AutopilotConfig.id == config_id)
                )
                platforms = result.scalar_one_or_none()
                return platforms if platforms else ["instagram"]
        except Exception:
            return ["instagram"]

    def _parse_platforms(self, text: str) -> list[str]:
        """Parse platform names from text."""
        platforms = []
        text = text.lower()

        if "insta" in text:
            platforms.append("instagram")
        if "tiktok" in text or "tik tok" in text:
            platforms.append("tiktok")
        if "linkedin" in text:
            platforms.append("linkedin")
        if "facebook" in text or "fb" in text:
            platforms.append("facebook")
        if "tout" in text or "all" in text or "toutes" in text:
            platforms = ["instagram", "tiktok", "linkedin"]

        return platforms or ["instagram"]
