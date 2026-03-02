# PresenceOS — Comment & DM models (Sprint 5: Engager)
# Dataclasses stored in Firestore (not PostgreSQL — no migration needed)

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional


class CommentPlatform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    GOOGLE = "google"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    QUESTION = "question"
    SPAM = "spam"
    NEUTRAL = "neutral"
    URGENT = "urgent"


class ReplyStatus(str, Enum):
    PENDING = "pending"          # awaiting classification
    CLASSIFIED = "classified"    # classified, reply drafted
    APPROVED = "approved"        # owner approved reply
    PUBLISHED = "published"      # reply posted
    REJECTED = "rejected"        # owner rejected suggestion
    SKIPPED = "skipped"          # spam or no reply needed


@dataclass
class Comment:
    """A comment or review from any social platform."""

    id: str = ""
    platform: str = "instagram"
    post_id: str = ""
    post_url: str = ""
    author_name: str = ""
    author_id: str = ""
    author_avatar: str = ""
    text: str = ""
    created_at: str = ""                  # ISO 8601
    fetched_at: str = ""                  # ISO 8601

    # Classification (filled by classifier)
    sentiment: str = "neutral"
    urgency_score: float = 0.0            # 0-10
    topics: list[str] = field(default_factory=list)

    # Reply (filled by reply generator)
    suggested_reply: str = ""
    reply_status: str = "pending"
    final_reply: str = ""                 # after human edit
    replied_at: str = ""                  # ISO 8601

    # Metadata
    brand_id: str = ""
    is_dm: bool = False
    parent_comment_id: str = ""           # for threaded replies
    media_url: str = ""                   # post image/video URL

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Comment:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


@dataclass
class DirectMessage:
    """A DM/private message from a social platform."""

    id: str = ""
    platform: str = "instagram"
    conversation_id: str = ""
    author_name: str = ""
    author_id: str = ""
    author_avatar: str = ""
    text: str = ""
    created_at: str = ""
    fetched_at: str = ""

    # Classification
    sentiment: str = "neutral"
    urgency_score: float = 0.0
    topics: list[str] = field(default_factory=list)

    # Reply
    suggested_reply: str = ""
    reply_status: str = "pending"
    final_reply: str = ""
    replied_at: str = ""

    # Metadata
    brand_id: str = ""
    is_dm: bool = True
    media_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> DirectMessage:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
