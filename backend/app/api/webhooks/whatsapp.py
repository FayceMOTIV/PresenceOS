"""
PresenceOS - WhatsApp Webhook (Sprint 9 + 9B + 9C)

Mounted at /webhooks/whatsapp (outside /api/v1 to match Meta's requirements).
Handles:
  - GET  /webhooks/whatsapp  → verification challenge
  - POST /webhooks/whatsapp  → incoming messages routed through ConversationEngine
"""
import hmac
import hashlib
import structlog
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.autopilot import PendingPost, PendingPostStatus, AutopilotConfig
from app.models.media import MediaAsset, VoiceNote, MediaSource, MediaType
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    PostStatus,
    ConnectorStatus,
    SocialPlatform,
)
from app.services.whatsapp import WhatsAppService
from app.services.storage import get_storage_service
from app.services.vision import VisionService
from app.services.transcription import TranscriptionService
from app.services.instruction_parser import InstructionParser
from app.services.conversation_engine import ConversationEngine

logger = structlog.get_logger()

router = APIRouter(tags=["WhatsApp Webhook"])

# Supported media MIME types
IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_MIMES = {"video/mp4", "video/3gpp", "video/quicktime"}
AUDIO_MIMES = {"audio/ogg", "audio/mpeg", "audio/amr", "audio/aac", "audio/opus"}

# Singleton conversation engine
_conversation_engine: ConversationEngine | None = None


def _get_engine() -> ConversationEngine:
    global _conversation_engine
    if _conversation_engine is None:
        _conversation_engine = ConversationEngine()
    return _conversation_engine


@router.get("/webhooks/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Meta webhook verification (subscribe handshake)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("WhatsApp webhook verified")
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp")
async def handle_webhook(request: Request):
    """Process incoming WhatsApp webhook events via ConversationEngine."""
    body = await request.body()

    # Optionally verify signature
    if settings.whatsapp_webhook_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            settings.whatsapp_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning("WhatsApp webhook signature mismatch")
            raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()

    # Parse the webhook payload and route through ConversationEngine
    try:
        engine = _get_engine()
        entry = data.get("entry", [])
        for e in entry:
            for change in e.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    sender = message.get("from", "")
                    msg_type = message.get("type", "")

                    if not sender or not msg_type:
                        continue

                    # Resolve brand for this phone number
                    brand_id, config_id = await _find_brand_for_phone(sender)

                    if not brand_id:
                        # No brand configured — send help message
                        wa = WhatsAppService()
                        await wa.send_text_message(
                            sender,
                            "Aucune marque configuree pour ce numero. "
                            "Activez l'autopilote WhatsApp dans PresenceOS.",
                        )
                        continue

                    # Route through ConversationEngine
                    await engine.handle_message(
                        sender_phone=sender,
                        msg_type=msg_type,
                        message=message,
                        brand_id=str(brand_id),
                        config_id=str(config_id),
                    )

    except Exception as e:
        logger.error("WhatsApp webhook processing error", error=str(e))

    # Always return 200 to Meta
    return {"status": "ok"}


# ── Media Download Helper ─────────────────────────────────────────


async def _download_whatsapp_media(media_id: str) -> tuple[bytes, str]:
    """
    Download media from WhatsApp Cloud API.

    Returns (file_bytes, mime_type).
    """
    graph_base = f"https://graph.facebook.com/{settings.whatsapp_api_version}"
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Get media URL
        meta_resp = await client.get(f"{graph_base}/{media_id}", headers=headers)
        meta_resp.raise_for_status()
        meta_data = meta_resp.json()
        download_url = meta_data["url"]
        mime_type = meta_data.get("mime_type", "application/octet-stream")

        # Step 2: Download the actual file
        file_resp = await client.get(download_url, headers=headers)
        file_resp.raise_for_status()

        return file_resp.content, mime_type


async def _find_brand_for_phone(sender_phone: str):
    """Find the brand associated with a WhatsApp phone number via autopilot config."""
    async with async_session_maker() as db:
        # Look for an autopilot config with this phone
        normalized = sender_phone.lstrip("+").replace(" ", "")
        result = await db.execute(
            select(AutopilotConfig).where(
                AutopilotConfig.whatsapp_enabled == True,
                AutopilotConfig.is_enabled == True,
            )
        )
        configs = result.scalars().all()

        for config in configs:
            if config.whatsapp_phone:
                config_phone = config.whatsapp_phone.lstrip("+").replace(" ", "")
                if config_phone == normalized:
                    return config.brand_id, config.id

        # If only one active config exists, use it
        if len(configs) == 1:
            return configs[0].brand_id, configs[0].id

        return None, None


# ── Image Handler ──────────────────────────────────────────────────


async def _handle_image_message(message: dict, sender_phone: str):
    """Process an incoming image: download, store, analyze with Vision AI."""
    wa = WhatsAppService()
    media_info = message.get("image", {})
    media_id = media_info.get("id")
    caption_text = media_info.get("caption", "")

    if not media_id:
        return

    brand_id, config_id = await _find_brand_for_phone(sender_phone)
    if not brand_id:
        await wa.send_text_message(
            sender_phone,
            "Aucune marque configuree pour ce numero. Activez l'autopilote dans PresenceOS.",
        )
        return

    try:
        # Download image
        file_bytes, mime_type = await _download_whatsapp_media(media_id)
        if mime_type.split(";")[0] not in IMAGE_MIMES:
            mime_type = "image/jpeg"

        # Store in S3
        storage = get_storage_service()
        key = storage.generate_key(str(brand_id), "image", f"wa_{media_id}.jpg")
        upload_result = await storage.upload_bytes(
            file_bytes, key, content_type=mime_type
        )

        # Save MediaAsset in DB
        async with async_session_maker() as db:
            asset = MediaAsset(
                brand_id=brand_id,
                storage_key=upload_result["key"],
                public_url=upload_result["url"],
                media_type=MediaType.IMAGE,
                mime_type=mime_type,
                file_size=upload_result["size"],
                source=MediaSource.WHATSAPP,
                whatsapp_media_id=media_id,
            )
            db.add(asset)
            await db.commit()
            await db.refresh(asset)
            asset_id = str(asset.id)

        # Analyze with Vision AI (fire and forget, update DB after)
        try:
            vision = VisionService()
            analysis = await vision.analyze_image(file_bytes, mime_type)

            async with async_session_maker() as db:
                result = await db.execute(
                    select(MediaAsset).where(MediaAsset.id == asset_id)
                )
                asset = result.scalar_one_or_none()
                if asset:
                    asset.ai_description = analysis.get("description", "")
                    asset.ai_tags = analysis.get("tags", [])
                    asset.ai_analyzed = True
                    await db.commit()
        except Exception as vision_err:
            logger.warning("Vision analysis failed", error=str(vision_err))

        # Parse instructions from caption if present
        if caption_text:
            parser = InstructionParser()
            instructions = await parser.parse(caption_text)
        else:
            instructions = {
                "platforms": ["instagram"],
                "caption_directive": None,
                "is_ready_to_publish": False,
            }

        # Create a PendingPost with the image
        suggested_caption = ""
        if caption_text:
            suggested_caption = caption_text
        elif analysis and analysis.get("suggested_caption"):
            suggested_caption = analysis["suggested_caption"]

        if config_id and suggested_caption:
            async with async_session_maker() as db:
                for platform in instructions.get("platforms", ["instagram"]):
                    pending = PendingPost(
                        config_id=config_id,
                        brand_id=brand_id,
                        platform=platform,
                        caption=suggested_caption,
                        media_urls=[upload_result["url"]],
                        ai_reasoning="Contenu recu via WhatsApp",
                        status=PendingPostStatus.PENDING,
                    )
                    db.add(pending)
                await db.commit()

        # Confirm to user
        msg = "Image recue et sauvegardee !"
        if suggested_caption:
            msg += f"\n\nCaption suggeree:\n{suggested_caption[:200]}"
            msg += "\n\nRepondez 'ok' pour publier ou envoyez une nouvelle caption."
        else:
            msg += "\nEnvoyez une caption pour creer un post."

        await wa.send_text_message(sender_phone, msg)

        logger.info("WhatsApp image processed", brand_id=str(brand_id), asset_id=asset_id)

    except Exception as e:
        logger.error("Image processing failed", error=str(e))
        await wa.send_text_message(
            sender_phone, "Erreur lors du traitement de l'image. Reessayez."
        )


# ── Video Handler ──────────────────────────────────────────────────


async def _handle_video_message(message: dict, sender_phone: str):
    """Process an incoming video: download and store."""
    wa = WhatsAppService()
    media_info = message.get("video", {})
    media_id = media_info.get("id")
    caption_text = media_info.get("caption", "")

    if not media_id:
        return

    brand_id, config_id = await _find_brand_for_phone(sender_phone)
    if not brand_id:
        await wa.send_text_message(
            sender_phone,
            "Aucune marque configuree pour ce numero.",
        )
        return

    try:
        # Download video
        file_bytes, mime_type = await _download_whatsapp_media(media_id)
        if mime_type.split(";")[0] not in VIDEO_MIMES:
            mime_type = "video/mp4"

        # Store in S3
        storage = get_storage_service()
        key = storage.generate_key(str(brand_id), "video", f"wa_{media_id}.mp4")
        upload_result = await storage.upload_bytes(
            file_bytes, key, content_type=mime_type
        )

        # Save MediaAsset in DB
        async with async_session_maker() as db:
            asset = MediaAsset(
                brand_id=brand_id,
                storage_key=upload_result["key"],
                public_url=upload_result["url"],
                media_type=MediaType.VIDEO,
                mime_type=mime_type,
                file_size=upload_result["size"],
                source=MediaSource.WHATSAPP,
                whatsapp_media_id=media_id,
            )
            db.add(asset)
            await db.commit()

        # Create PendingPost if caption present
        if caption_text and config_id:
            async with async_session_maker() as db:
                pending = PendingPost(
                    config_id=config_id,
                    brand_id=brand_id,
                    platform="instagram",
                    caption=caption_text,
                    media_urls=[upload_result["url"]],
                    ai_reasoning="Video recue via WhatsApp",
                    status=PendingPostStatus.PENDING,
                )
                db.add(pending)
                await db.commit()

        msg = "Video recue et sauvegardee !"
        if caption_text:
            msg += f"\n\nCaption: {caption_text[:200]}"
        else:
            msg += "\nEnvoyez une caption pour creer un post."

        await wa.send_text_message(sender_phone, msg)

        logger.info("WhatsApp video processed", brand_id=str(brand_id))

    except Exception as e:
        logger.error("Video processing failed", error=str(e))
        await wa.send_text_message(
            sender_phone, "Erreur lors du traitement de la video. Reessayez."
        )


# ── Audio/Voice Handler ───────────────────────────────────────────


async def _handle_audio_message(message: dict, sender_phone: str):
    """Process a voice note: download, store, transcribe, parse instructions."""
    wa = WhatsAppService()
    audio_info = message.get("audio", {})
    media_id = audio_info.get("id")

    if not media_id:
        return

    brand_id, config_id = await _find_brand_for_phone(sender_phone)
    if not brand_id:
        await wa.send_text_message(
            sender_phone,
            "Aucune marque configuree pour ce numero.",
        )
        return

    try:
        # Download audio
        file_bytes, mime_type = await _download_whatsapp_media(media_id)

        # Store in S3
        storage = get_storage_service()
        ext = "ogg" if "ogg" in mime_type else "mp3"
        key = storage.generate_key(str(brand_id), "audio", f"wa_{media_id}.{ext}")
        upload_result = await storage.upload_bytes(
            file_bytes, key, content_type=mime_type
        )

        # Transcribe with Whisper
        transcription_text = ""
        try:
            transcriber = TranscriptionService()
            transcription_text = await transcriber.transcribe(
                file_bytes, filename=f"voice.{ext}"
            )
        except Exception as t_err:
            logger.warning("Transcription failed", error=str(t_err))

        # Parse instructions from transcription
        parsed = {}
        if transcription_text:
            try:
                parser = InstructionParser()
                parsed = await parser.parse(transcription_text)
            except Exception as p_err:
                logger.warning("Instruction parsing failed", error=str(p_err))

        # Save VoiceNote in DB
        async with async_session_maker() as db:
            voice_note = VoiceNote(
                brand_id=brand_id,
                storage_key=upload_result["key"],
                public_url=upload_result["url"],
                mime_type=mime_type,
                file_size=upload_result["size"],
                transcription=transcription_text or None,
                is_transcribed=bool(transcription_text),
                whatsapp_media_id=media_id,
                sender_phone=sender_phone,
                parsed_instructions=parsed or None,
            )
            db.add(voice_note)
            await db.commit()

        # Send back the transcription
        msg = "Message vocal recu !"
        if transcription_text:
            msg += f"\n\nTranscription:\n\"{transcription_text[:500]}\""
            if parsed.get("caption_directive"):
                msg += f"\n\nJ'ai compris: {parsed['caption_directive'][:200]}"
                msg += f"\nPlateforme(s): {', '.join(parsed.get('platforms', ['instagram']))}"
        else:
            msg += "\nTranscription non disponible."

        await wa.send_text_message(sender_phone, msg)

        logger.info(
            "WhatsApp voice note processed",
            brand_id=str(brand_id),
            transcribed=bool(transcription_text),
        )

    except Exception as e:
        logger.error("Audio processing failed", error=str(e))
        await wa.send_text_message(
            sender_phone, "Erreur lors du traitement du message vocal. Reessayez."
        )


# ── Text Handler ───────────────────────────────────────────────────


async def _handle_text_message(message: dict, sender_phone: str):
    """Process a text message: parse instructions, generate content."""
    wa = WhatsAppService()
    text_body = message.get("text", {}).get("body", "").strip()

    if not text_body:
        return

    brand_id, config_id = await _find_brand_for_phone(sender_phone)
    if not brand_id:
        await wa.send_text_message(
            sender_phone,
            "Aucune marque configuree pour ce numero. Activez l'autopilote dans PresenceOS.",
        )
        return

    try:
        # Parse instructions
        parser = InstructionParser()
        instructions = await parser.parse(text_body)

        platforms = instructions.get("platforms", ["instagram"])
        caption_directive = instructions.get("caption_directive", text_body)

        if config_id and caption_directive:
            # Create PendingPost(s)
            async with async_session_maker() as db:
                for platform in platforms:
                    pending = PendingPost(
                        config_id=config_id,
                        brand_id=brand_id,
                        platform=platform,
                        caption=caption_directive,
                        ai_reasoning=f"Instructions WhatsApp: {text_body[:200]}",
                        status=PendingPostStatus.PENDING,
                    )
                    db.add(pending)
                await db.commit()

            msg = f"Post cree pour {', '.join(platforms)} !"
            msg += f"\n\nCaption:\n{caption_directive[:300]}"
            msg += "\n\nConsultez PresenceOS pour valider et publier."
        else:
            msg = "Message recu. Envoyez une photo/video avec une caption pour creer un post."

        await wa.send_text_message(sender_phone, msg)

        logger.info(
            "WhatsApp text processed",
            brand_id=str(brand_id),
            platforms=platforms,
        )

    except Exception as e:
        logger.error("Text processing failed", error=str(e))
        await wa.send_text_message(
            sender_phone, "Erreur lors du traitement. Reessayez."
        )


# ── Button Reply Handlers (Sprint 9) ──────────────────────────────


async def _handle_button_reply(button_id: str, sender_phone: str):
    """Process approve/reject button clicks."""
    if button_id.startswith("approve_"):
        pending_post_id = button_id.replace("approve_", "")
        await _handle_approve(pending_post_id, sender_phone)
    elif button_id.startswith("reject_"):
        pending_post_id = button_id.replace("reject_", "")
        await _handle_reject(pending_post_id, sender_phone)
    else:
        logger.warning("Unknown button_id", button_id=button_id)


async def _handle_approve(pending_post_id: str, sender_phone: str):
    """Approve a pending post and schedule it for publishing."""
    wa = WhatsAppService()

    async with async_session_maker() as db:
        result = await db.execute(
            select(PendingPost)
            .options(selectinload(PendingPost.config))
            .where(PendingPost.id == pending_post_id)
        )
        pending = result.scalar_one_or_none()

        if not pending:
            logger.warning("Pending post not found", id=pending_post_id)
            return

        if pending.status != PendingPostStatus.PENDING:
            await wa.send_text_message(
                sender_phone, f"Ce post a deja ete traite ({pending.status.value})."
            )
            return

        # Find an active connector for the target platform
        platform_enum = _str_to_platform(pending.platform)
        connector_result = await db.execute(
            select(SocialConnector).where(
                SocialConnector.brand_id == pending.brand_id,
                SocialConnector.platform == platform_enum,
                SocialConnector.status == ConnectorStatus.CONNECTED,
                SocialConnector.is_active == True,
            )
        )
        connector = connector_result.scalar_one_or_none()

        if not connector:
            pending.status = PendingPostStatus.REJECTED
            pending.reviewed_at = datetime.now(timezone.utc)
            await db.commit()
            await wa.send_text_message(
                sender_phone,
                f"Aucun connecteur actif pour {pending.platform}. Post rejete.",
            )
            return

        # Determine posting time
        posting_time = datetime.now(timezone.utc)
        if pending.config and pending.config.preferred_posting_time:
            try:
                h, m = pending.config.preferred_posting_time.split(":")
                posting_time = posting_time.replace(
                    hour=int(h), minute=int(m), second=0
                )
                # If the time already passed today, schedule for tomorrow
                if posting_time < datetime.now(timezone.utc):
                    from datetime import timedelta
                    posting_time += timedelta(days=1)
            except ValueError:
                pass

        # Create ScheduledPost
        scheduled = ScheduledPost(
            brand_id=pending.brand_id,
            connector_id=connector.id,
            scheduled_at=posting_time,
            status=PostStatus.SCHEDULED,
            content_snapshot={
                "caption": pending.caption,
                "hashtags": pending.hashtags or [],
                "media_urls": pending.media_urls or [],
            },
        )
        db.add(scheduled)

        # Update pending post
        pending.status = PendingPostStatus.APPROVED
        pending.reviewed_at = datetime.now(timezone.utc)
        pending.scheduled_post_id = scheduled.id

        # Update stats
        if pending.config:
            pending.config.total_published += 1

        await db.commit()

        logger.info("Post approved via WhatsApp", pending_id=pending_post_id)
        await wa.send_text_message(
            sender_phone, "Post approuve et programme pour publication !"
        )


async def _handle_reject(pending_post_id: str, sender_phone: str):
    """Reject a pending post."""
    wa = WhatsAppService()

    async with async_session_maker() as db:
        result = await db.execute(
            select(PendingPost).where(PendingPost.id == pending_post_id)
        )
        pending = result.scalar_one_or_none()

        if not pending:
            return

        if pending.status != PendingPostStatus.PENDING:
            await wa.send_text_message(
                sender_phone, f"Ce post a deja ete traite ({pending.status.value})."
            )
            return

        pending.status = PendingPostStatus.REJECTED
        pending.reviewed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info("Post rejected via WhatsApp", pending_id=pending_post_id)
        await wa.send_text_message(sender_phone, "Post rejete.")


def _str_to_platform(platform_str: str) -> SocialPlatform:
    """Convert platform string to SocialPlatform enum."""
    mapping = {
        "instagram": SocialPlatform.INSTAGRAM,
        "tiktok": SocialPlatform.TIKTOK,
        "linkedin": SocialPlatform.LINKEDIN,
        "facebook": SocialPlatform.FACEBOOK,
    }
    return mapping.get(platform_str.lower(), SocialPlatform.INSTAGRAM)
