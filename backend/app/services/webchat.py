"""
PresenceOS - WebChat Service

Accumulates AI responses instead of sending them to a messaging platform.
Used by the web Content Studio to interact with ConversationEngine.
"""


class WebChatService:
    """Accumulates AI responses for web-based conversation."""

    def __init__(self):
        self.responses: list[dict] = []

    async def send_text_message(self, chat_id: str, text: str):
        self.responses.append({"type": "text", "content": text})
        return f"web-{len(self.responses)}"

    async def send_interactive_buttons(
        self,
        chat_id: str,
        body_text: str,
        buttons: list[dict],
        header_text: str | None = None,
    ):
        self.responses.append({
            "type": "buttons",
            "content": body_text,
            "header": header_text,
            "buttons": [{"id": b["id"], "title": b["title"]} for b in buttons],
        })
        return f"web-{len(self.responses)}"

    async def send_media_message(
        self,
        chat_id: str,
        media_url: str,
        caption: str | None = None,
        media_type: str = "image",
    ):
        self.responses.append({
            "type": "media",
            "content": caption,
            "media_url": media_url,
            "media_type": media_type,
        })
        return f"web-{len(self.responses)}"

    async def send_reaction(self, chat_id: str, message_id: str, emoji: str = ""):
        self.responses.append({"type": "reaction", "emoji": emoji})
        return True

    @property
    def is_configured(self) -> bool:
        return True
