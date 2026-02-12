"""
PresenceOS - Telegram Adapter

Translates Telegram Update objects into the normalized message format
expected by ConversationEngine.handle_message().

Telegram -> Normalized:
  - Message text     -> {"text": {"body": "..."}}
  - Photo            -> {"image": {"id": file_id, "caption": "..."}}
  - Video            -> {"video": {"id": file_id, "caption": "..."}}
  - Voice/Audio      -> {"audio": {"id": file_id}}
  - CallbackQuery    -> {"interactive": {"type": "button_reply", "button_reply": {"id": data}}}

Uses TelegramService for sending responses and downloading media.
"""
import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.autopilot import AutopilotConfig
from app.models.brand import Brand
from app.services.telegram import TelegramService
from app.services.conversation_engine import ConversationEngine

logger = structlog.get_logger()

# Singleton engine
_conversation_engine: ConversationEngine | None = None


def _get_engine() -> ConversationEngine:
    global _conversation_engine
    if _conversation_engine is None:
        _conversation_engine = ConversationEngine()
    return _conversation_engine


class TelegramAdapter:
    """
    Adapts Telegram updates into ConversationEngine-compatible format.

    Main entry point: handle_telegram_update(update_dict)
    """

    def __init__(self):
        self.tg = TelegramService()

    async def handle_telegram_update(self, update: dict) -> None:
        """
        Process a raw Telegram Update dict.

        Handles:
          - message (text, photo, video, voice, audio)
          - callback_query (inline button clicks)
        """
        # Handle callback query (button click)
        callback_query = update.get("callback_query")
        if callback_query:
            await self._handle_callback_query(callback_query)
            return

        # Handle regular message
        message = update.get("message")
        if not message:
            return

        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        if not chat_id:
            return

        # Determine message type and build normalized message
        msg_type, normalized = self._normalize_message(message)
        if not msg_type:
            return

        # Resolve brand for this chat_id
        brand_id, config_id = await self._find_brand_for_telegram(chat_id)

        if not brand_id:
            # No brand — send help message
            await self.tg.send_text_message(
                chat_id,
                "Aucune marque configuree pour ce chat Telegram. "
                "Activez l'autopilote Telegram dans PresenceOS.",
            )
            return

        # Route through ConversationEngine with TelegramService as messaging
        engine = _get_engine()

        # Build a media downloader that uses Telegram's file API
        async def telegram_media_downloader(file_id: str):
            return await self.tg.download_file(file_id)

        await engine.handle_message(
            sender_phone=chat_id,  # Use chat_id as sender identifier
            msg_type=msg_type,
            message=normalized,
            brand_id=str(brand_id),
            config_id=str(config_id),
            messaging_service=self.tg,
            media_downloader=telegram_media_downloader,
        )

    def _normalize_message(self, message: dict) -> tuple[str | None, dict]:
        """
        Convert Telegram message into ConversationEngine-compatible format.

        Returns (msg_type, normalized_message) or (None, {}) if unsupported.
        """
        # Text message
        text = message.get("text")
        if text:
            return "text", {"text": {"body": text}}

        # Photo (take largest resolution)
        photo = message.get("photo")
        if photo:
            # photo is an array of PhotoSize, last = largest
            best = photo[-1]
            file_id = best.get("file_id", "")
            caption = message.get("caption", "")
            return "image", {"image": {"id": file_id, "caption": caption}}

        # Video
        video = message.get("video")
        if video:
            file_id = video.get("file_id", "")
            caption = message.get("caption", "")
            return "video", {"video": {"id": file_id, "caption": caption}}

        # Voice note
        voice = message.get("voice")
        if voice:
            file_id = voice.get("file_id", "")
            return "audio", {"audio": {"id": file_id}}

        # Audio file
        audio = message.get("audio")
        if audio:
            file_id = audio.get("file_id", "")
            return "audio", {"audio": {"id": file_id}}

        # Document (treat as unsupported for now)
        return None, {}

    async def _handle_callback_query(self, callback_query: dict) -> None:
        """
        Handle a Telegram callback_query (inline button click).

        Translates to ConversationEngine interactive button format.
        """
        chat = callback_query.get("message", {}).get("chat", {})
        chat_id = str(chat.get("id", ""))
        button_data = callback_query.get("data", "")

        if not chat_id or not button_data:
            return

        # Answer the callback query to remove loading indicator
        callback_query_id = callback_query.get("id")
        if callback_query_id:
            try:
                bot = self.tg._get_bot()
                await bot.answer_callback_query(callback_query_id)
            except Exception as e:
                logger.warning("Failed to answer callback query", error=str(e))

        # Resolve brand
        brand_id, config_id = await self._find_brand_for_telegram(chat_id)
        if not brand_id:
            return

        # Build normalized interactive message
        normalized = {
            "interactive": {
                "type": "button_reply",
                "button_reply": {"id": button_data},
            }
        }

        engine = _get_engine()
        await engine.handle_message(
            sender_phone=chat_id,
            msg_type="interactive",
            message=normalized,
            brand_id=str(brand_id),
            config_id=str(config_id),
            messaging_service=self.tg,
        )

    async def _find_brand_for_telegram(self, chat_id: str):
        """
        Find the brand associated with a Telegram chat_id via autopilot config.

        Lookup order:
          1. AutopilotConfig with telegram_chat_id matching
          2. AutopilotConfig with whatsapp_phone matching chat_id
          3. Single active AutopilotConfig (dev convenience)
          4. First active Brand in DB (dev/test fallback — creates config on the fly)
        """
        async with async_session_maker() as db:
            # First try AutopilotConfig matches
            result = await db.execute(
                select(AutopilotConfig).where(
                    AutopilotConfig.is_enabled == True,
                )
            )
            configs = result.scalars().all()

            for config in configs:
                # Check if config has telegram_chat_id matching
                tg_chat = getattr(config, "telegram_chat_id", None)
                if tg_chat and str(tg_chat) == chat_id:
                    return config.brand_id, config.id

            # Fallback: also check whatsapp_phone field (user may store chat_id there)
            for config in configs:
                if config.whatsapp_phone:
                    phone_normalized = config.whatsapp_phone.lstrip("+").replace(" ", "")
                    if phone_normalized == chat_id:
                        return config.brand_id, config.id

            # If only one active config exists, use it (dev convenience)
            if len(configs) == 1:
                return configs[0].brand_id, configs[0].id

            # Any config at all (even disabled)
            if configs:
                return configs[0].brand_id, configs[0].id

            # Final fallback: find the first active Brand and use its config
            brand_result = await db.execute(
                select(Brand).where(Brand.is_active == True).limit(1)
            )
            brand = brand_result.scalar_one_or_none()

            if brand:
                # Check if brand already has an autopilot config
                config_result = await db.execute(
                    select(AutopilotConfig).where(
                        AutopilotConfig.brand_id == brand.id
                    )
                )
                existing_config = config_result.scalar_one_or_none()

                if existing_config:
                    logger.info(
                        "Telegram fallback: using existing config for brand",
                        brand=brand.name,
                        config_id=str(existing_config.id),
                    )
                    return brand.id, existing_config.id

                # Create a minimal AutopilotConfig for this brand
                from app.models.autopilot import AutopilotFrequency
                new_config = AutopilotConfig(
                    brand_id=brand.id,
                    is_enabled=True,
                    platforms=["instagram"],
                    frequency=AutopilotFrequency.DAILY,
                    auto_publish=False,
                )
                db.add(new_config)
                await db.commit()
                await db.refresh(new_config)

                logger.info(
                    "Telegram fallback: created config for brand",
                    brand=brand.name,
                    config_id=str(new_config.id),
                )
                return brand.id, new_config.id

            return None, None
