"""
PresenceOS - WhatsApp Cloud API Service (Sprint 9)

Uses httpx to send interactive button messages via Meta Graph API.
Does NOT use pywa — direct API calls for full control.
"""
import structlog
import httpx

from app.core.config import settings

logger = structlog.get_logger()

GRAPH_BASE = f"https://graph.facebook.com/{settings.whatsapp_api_version}"


class WhatsAppService:
    """Send WhatsApp messages via Meta Cloud API."""

    def __init__(self):
        self.token = settings.whatsapp_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.base_url = f"{GRAPH_BASE}/{self.phone_number_id}/messages"

    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp credentials are set."""
        return bool(self.token and self.phone_number_id)

    async def send_approval_message(
        self,
        to_phone: str,
        pending_post_id: str,
        platform: str,
        caption_preview: str,
    ) -> str | None:
        """
        Send an interactive button message for post approval.

        Returns the WhatsApp message ID (wamid) or None on failure.
        """
        if not self.is_configured:
            logger.warning("WhatsApp not configured, skipping message")
            return None

        # Truncate caption for WhatsApp body (max ~1024 chars)
        body_text = caption_preview[:300] + ("..." if len(caption_preview) > 300 else "")

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": f"Nouveau post {platform.upper()}",
                },
                "body": {
                    "text": body_text,
                },
                "footer": {
                    "text": "PresenceOS Autopilote",
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"approve_{pending_post_id}",
                                "title": "Publier",
                            },
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"reject_{pending_post_id}",
                                "title": "Rejeter",
                            },
                        },
                    ],
                },
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()
                wamid = data.get("messages", [{}])[0].get("id")
                logger.info(
                    "WhatsApp message sent",
                    to=to_phone,
                    wamid=wamid,
                    pending_post_id=pending_post_id,
                )
                return wamid

        except httpx.HTTPStatusError as e:
            logger.error(
                "WhatsApp API error",
                status=e.response.status_code,
                body=e.response.text[:500],
            )
            return None
        except Exception as e:
            logger.error("WhatsApp send failed", error=str(e))
            return None

    async def send_text_message(self, to_phone: str, text: str) -> str | None:
        """Send a simple text message."""
        if not self.is_configured:
            return None

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.replace("+", "").replace(" ", ""),
            "type": "text",
            "text": {"body": text},
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("messages", [{}])[0].get("id")
        except Exception as e:
            logger.error("WhatsApp text send failed", error=str(e))
            return None

    async def send_interactive_buttons(
        self,
        to_phone: str,
        body_text: str,
        buttons: list[dict],
        header_text: str | None = None,
        footer_text: str | None = None,
    ) -> str | None:
        """
        Send an interactive button message.

        Args:
            buttons: List of {"id": "btn_id", "title": "Button Label"} (max 3)
        """
        if not self.is_configured:
            return None

        interactive = {
            "type": "button",
            "body": {"text": body_text[:1024]},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                    for b in buttons[:3]
                ]
            },
        }
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text[:60]}
        if footer_text:
            interactive["footer"] = {"text": footer_text[:60]}

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": interactive,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()
                wamid = data.get("messages", [{}])[0].get("id")
                logger.info("WhatsApp interactive sent", to=to_phone, wamid=wamid)
                return wamid
        except Exception as e:
            logger.error("WhatsApp interactive send failed", error=str(e))
            return None

    async def send_media_message(
        self,
        to_phone: str,
        media_url: str,
        media_type: str = "image",
        caption: str | None = None,
    ) -> str | None:
        """
        Send a media message (image, video, document).

        Args:
            media_type: 'image', 'video', or 'document'
        """
        if not self.is_configured:
            return None

        media_payload = {"link": media_url}
        if caption and media_type in ("image", "video"):
            media_payload["caption"] = caption[:1024]

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.replace("+", "").replace(" ", ""),
            "type": media_type,
            media_type: media_payload,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("messages", [{}])[0].get("id")
        except Exception as e:
            logger.error("WhatsApp media send failed", error=str(e))
            return None

    async def send_reaction(
        self,
        to_phone: str,
        message_id: str,
        emoji: str = "👍",
    ) -> str | None:
        """React to a message with an emoji."""
        if not self.is_configured:
            return None

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone.replace("+", "").replace(" ", ""),
            "type": "reaction",
            "reaction": {"message_id": message_id, "emoji": emoji},
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("messages", [{}])[0].get("id")
        except Exception as e:
            logger.error("WhatsApp reaction failed", error=str(e))
            return None
