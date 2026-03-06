# PresenceOS — Comment Fetcher (Sprint 5: Engager)
# Fetches comments from Meta Graph API (Instagram/Facebook)
# MockCommentFetcher provides realistic test data for dev

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from random import choice, randint

import httpx

from app.models.comment import Comment

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class BaseCommentFetcher(ABC):
    """Abstract base for comment fetching."""

    @abstractmethod
    async def fetch_comments(
        self, brand_id: str, access_token: str, since_hours: int = 24
    ) -> list[Comment]:
        ...


class MetaCommentFetcher(BaseCommentFetcher):
    """Fetches comments from Instagram/Facebook via Meta Graph API."""

    def __init__(self, instagram_account_id: str = "") -> None:
        self.instagram_account_id = instagram_account_id

    async def fetch_comments(
        self, brand_id: str, access_token: str, since_hours: int = 24
    ) -> list[Comment]:
        comments: list[Comment] = []
        if not access_token:
            logger.warning("MetaCommentFetcher: no access_token, returning empty")
            return comments

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Use Instagram Business Account ID if available, else /me/media
                media_endpoint = (
                    f"{GRAPH_API_BASE}/{self.instagram_account_id}/media"
                    if self.instagram_account_id
                    else f"{GRAPH_API_BASE}/me/media"
                )
                media_resp = await client.get(
                    media_endpoint,
                    params={
                        "fields": "id,caption,permalink,timestamp,media_url",
                        "limit": 25,
                        "access_token": access_token,
                    },
                )
                media_resp.raise_for_status()
                media_data = media_resp.json().get("data", [])

                logger.info(
                    "Meta media fetched",
                    extra={"brand_id": brand_id, "media_count": len(media_data)},
                )

                for post in media_data:
                    post_comments = await self._fetch_post_comments(
                        client, post, brand_id, access_token, since_hours
                    )
                    comments.extend(post_comments)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Meta API error",
                extra={
                    "status": exc.response.status_code,
                    "body": exc.response.text[:500],
                    "brand_id": brand_id,
                },
            )
        except Exception as exc:
            logger.error(
                "Comment fetch failed",
                extra={"error": str(exc), "brand_id": brand_id},
            )

        return comments

    async def _fetch_post_comments(
        self,
        client: httpx.AsyncClient,
        post: dict,
        brand_id: str,
        access_token: str,
        since_hours: int,
    ) -> list[Comment]:
        comments: list[Comment] = []
        since = datetime.utcnow() - timedelta(hours=since_hours)

        try:
            resp = await client.get(
                f"{GRAPH_API_BASE}/{post['id']}/comments",
                params={
                    "fields": "id,text,username,timestamp,from",
                    "limit": 50,
                    "access_token": access_token,
                },
            )
            resp.raise_for_status()

            for c in resp.json().get("data", []):
                created = datetime.fromisoformat(
                    c.get("timestamp", "").replace("Z", "+00:00")
                )
                if created.replace(tzinfo=None) < since:
                    continue

                author = c.get("from", {})
                comments.append(
                    Comment(
                        id=c.get("id", ""),
                        platform="instagram",
                        post_id=post.get("id", ""),
                        post_url=post.get("permalink", ""),
                        author_name=author.get("username", c.get("username", "")),
                        author_id=author.get("id", ""),
                        text=c.get("text", ""),
                        created_at=c.get("timestamp", ""),
                        fetched_at=datetime.utcnow().isoformat(),
                        brand_id=brand_id,
                        media_url=post.get("media_url", ""),
                    )
                )
        except Exception as exc:
            logger.warning(
                "Failed to fetch comments for post",
                extra={"post_id": post.get("id"), "error": str(exc)},
            )

        return comments


# ── Mock Fetcher for development / testing ──

_MOCK_COMMENTS_FR = [
    ("Marie L.", "Wow ce plat a l'air incroyable ! Vous utilisez quels produits ?"),
    ("Thomas D.", "J'ai attendu 45 minutes pour ma commande, c'est inadmissible."),
    ("Sophie M.", "Vous faites des options végétariennes ?"),
    ("Lucas R.", "Franchement top, j'y retourne ce weekend !"),
    ("Emma B.", "C'est quoi vos horaires le dimanche ?"),
    ("Hugo P.", "Prix excessifs pour la qualité. Tres decu."),
    ("Lea V.", "Meilleur restaurant du quartier, bravo !!"),
    ("Nathan C.", "Est-ce que vous livrez dans le 15eme ?"),
    ("Camille F.", "Je recommande le burger, un delice !"),
    ("Julie A.", "Alerte : j'ai trouve un cheveu dans mon assiette."),
    ("Pierre G.", "Super ambiance, le personnel est tres sympa."),
    ("Manon H.", "Vous acceptez les tickets resto ?"),
    ("Antoine K.", "Spam spam spam visit my profile for free followers!!!"),
    ("Clara Z.", "Urgent : ma reservation de ce soir est toujours pas confirmee !"),
    ("Maxime W.", "Photo magnifique ! C'est quel plat exactement ?"),
]

_MOCK_PLATFORMS = ["instagram", "facebook"]


class MockCommentFetcher(BaseCommentFetcher):
    """Generates realistic mock comments for development."""

    async def fetch_comments(
        self, brand_id: str, access_token: str = "", since_hours: int = 24
    ) -> list[Comment]:
        count = randint(5, 10)
        comments: list[Comment] = []

        for _ in range(count):
            author_name, text = choice(_MOCK_COMMENTS_FR)
            now = datetime.utcnow()
            created = now - timedelta(hours=randint(1, since_hours))

            comments.append(
                Comment(
                    id=f"mock_{uuid.uuid4().hex[:12]}",
                    platform=choice(_MOCK_PLATFORMS),
                    post_id=f"post_{uuid.uuid4().hex[:8]}",
                    post_url=f"https://instagram.com/p/{uuid.uuid4().hex[:8]}",
                    author_name=author_name,
                    author_id=f"user_{uuid.uuid4().hex[:8]}",
                    text=text,
                    created_at=created.isoformat(),
                    fetched_at=now.isoformat(),
                    brand_id=brand_id,
                )
            )

        return comments
