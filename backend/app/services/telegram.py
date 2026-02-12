"""
PresenceOS - Telegram Bot API Service

Mirrors WhatsAppService interface using python-telegram-bot v22.
Uses the Bot class directly (no Application) for standalone async compatibility
with FastAPI.

Methods:
  - send_text_message(chat_id, text) -> message_id | None
  - send_interactive_buttons(chat_id, body_text, buttons, header_text) -> message_id | None
  - send_media_message(chat_id, media_url, media_type, caption) -> message_id | None
  - send_reaction(chat_id, message_id, emoji) -> bool
"""
import structlog
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app.core.config import settings

logger = structlog.get_logger()


class TelegramService:
    """Send Telegram messages via Bot API."""

    def __init__(self):
        self.token = settings.telegram_bot_token
        self._bot: Bot | None = None

    @property
    def is_configured(self) -> bool:
        """Check if Telegram bot token is set."""
        return bool(self.token)

    def _get_bot(self) -> Bot:
        if self._bot is None:
            self._bot = Bot(token=self.token)
        return self._bot

    async def send_text_message(
        self, chat_id: str | int, text: str
    ) -> int | None:
        """
        Send a simple text message.

        Returns the Telegram message_id or None on failure.
        """
        if not self.is_configured:
            logger.warning("Telegram not configured, skipping message")
            return None

        try:
            bot = self._get_bot()
            msg = await bot.send_message(
                chat_id=int(chat_id),
                text=text,
                parse_mode="HTML",
            )
            logger.info("Telegram text sent", chat_id=chat_id, message_id=msg.message_id)
            return msg.message_id
        except Exception as e:
            logger.error("Telegram text send failed", error=str(e), chat_id=chat_id)
            return None

    async def send_interactive_buttons(
        self,
        chat_id: str | int,
        body_text: str,
        buttons: list[dict],
        header_text: str | None = None,
        footer_text: str | None = None,
    ) -> int | None:
        """
        Send a message with inline keyboard buttons.

        Args:
            buttons: List of {"id": "btn_id", "title": "Label"}
                     No 3-button limit (unlike WhatsApp).
        """
        if not self.is_configured:
            return None

        try:
            bot = self._get_bot()

            # Build message text with optional header/footer
            parts = []
            if header_text:
                parts.append(f"<b>{header_text}</b>")
            parts.append(body_text)
            if footer_text:
                parts.append(f"<i>{footer_text}</i>")
            full_text = "\n\n".join(parts)

            # Build inline keyboard (one button per row)
            keyboard = [
                [InlineKeyboardButton(b["title"], callback_data=b["id"])]
                for b in buttons
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            msg = await bot.send_message(
                chat_id=int(chat_id),
                text=full_text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            logger.info("Telegram interactive sent", chat_id=chat_id, message_id=msg.message_id)
            return msg.message_id
        except Exception as e:
            logger.error("Telegram interactive send failed", error=str(e), chat_id=chat_id)
            return None

    async def send_media_message(
        self,
        chat_id: str | int,
        media_url: str,
        media_type: str = "image",
        caption: str | None = None,
    ) -> int | None:
        """
        Send a media message (photo, video, document).

        Args:
            media_type: 'image', 'video', or 'document'
        """
        if not self.is_configured:
            return None

        try:
            bot = self._get_bot()
            kwargs = {"chat_id": int(chat_id), "caption": caption, "parse_mode": "HTML"}

            if media_type == "image":
                msg = await bot.send_photo(photo=media_url, **kwargs)
            elif media_type == "video":
                msg = await bot.send_video(video=media_url, **kwargs)
            else:
                msg = await bot.send_document(document=media_url, **kwargs)

            logger.info(
                "Telegram media sent",
                chat_id=chat_id,
                media_type=media_type,
                message_id=msg.message_id,
            )
            return msg.message_id
        except Exception as e:
            logger.error("Telegram media send failed", error=str(e), chat_id=chat_id)
            return None

    async def send_reaction(
        self,
        chat_id: str | int,
        message_id: int,
        emoji: str = "\U0001f44d",
    ) -> bool:
        """React to a message with an emoji."""
        if not self.is_configured:
            return False

        try:
            bot = self._get_bot()
            from telegram import ReactionTypeEmoji
            await bot.set_message_reaction(
                chat_id=int(chat_id),
                message_id=message_id,
                reaction=[ReactionTypeEmoji(emoji=emoji)],
            )
            logger.info("Telegram reaction sent", chat_id=chat_id, emoji=emoji)
            return True
        except Exception as e:
            logger.error("Telegram reaction failed", error=str(e), chat_id=chat_id)
            return False

    async def download_file(self, file_id: str) -> tuple[bytes, str]:
        """
        Download a file from Telegram servers.

        Args:
            file_id: Telegram file_id

        Returns:
            (file_bytes, mime_type)
        """
        bot = self._get_bot()
        tg_file = await bot.get_file(file_id)

        # Download to bytes
        file_bytes = await tg_file.download_as_bytearray()

        # Infer mime type from file_path
        file_path = tg_file.file_path or ""
        mime_type = "application/octet-stream"
        if file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
            mime_type = "image/jpeg"
        elif file_path.endswith(".png"):
            mime_type = "image/png"
        elif file_path.endswith(".webp"):
            mime_type = "image/webp"
        elif file_path.endswith(".mp4"):
            mime_type = "video/mp4"
        elif file_path.endswith(".oga") or file_path.endswith(".ogg"):
            mime_type = "audio/ogg"
        elif file_path.endswith(".mp3"):
            mime_type = "audio/mpeg"

        return bytes(file_bytes), mime_type
