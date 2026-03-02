"""
Ilyas Intelligence — Reddit Module
Uses PRAW (free API, requires Reddit app credentials) for food/restaurant discussions.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class RedditIntel:
    """Reddit intelligence via PRAW for food/restaurant community insights."""

    def __init__(self) -> None:
        self._reddit = None

    def _get_client(self):
        if self._reddit is None:
            settings = get_settings()
            if not settings.reddit_client_id or not settings.reddit_client_secret:
                return None

            import praw
            self._reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
            )
        return self._reddit

    def _search_posts(self, query: str, subreddits: list[str], limit: int) -> dict:
        """Search Reddit posts across food/restaurant subreddits."""
        try:
            reddit = self._get_client()
            if reddit is None:
                return {"query": query, "error": "Reddit credentials not configured", "posts": []}

            posts = []
            for sub_name in subreddits:
                try:
                    subreddit = reddit.subreddit(sub_name)
                    for post in subreddit.search(query, sort="relevance", time_filter="month", limit=limit):
                        posts.append({
                            "subreddit": sub_name,
                            "title": post.title,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "url": f"https://reddit.com{post.permalink}",
                            "selftext": (post.selftext or "")[:300],
                            "created_utc": post.created_utc,
                            "upvote_ratio": post.upvote_ratio,
                        })
                except Exception as e:
                    logger.warning("Reddit search failed for r/%s: %s", sub_name, e)

            posts.sort(key=lambda p: p["score"], reverse=True)
            return {"query": query, "posts": posts[:limit], "count": len(posts)}
        except Exception as e:
            logger.warning("Reddit search failed: %s", e)
            return {"query": query, "error": str(e), "posts": []}

    def _get_hot_posts(self, subreddit_name: str, limit: int) -> dict:
        """Get hot posts from a specific subreddit."""
        try:
            reddit = self._get_client()
            if reddit is None:
                return {"subreddit": subreddit_name, "error": "Reddit credentials not configured", "posts": []}

            subreddit = reddit.subreddit(subreddit_name)
            posts = []
            for post in subreddit.hot(limit=limit):
                if post.stickied:
                    continue
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": f"https://reddit.com{post.permalink}",
                    "selftext": (post.selftext or "")[:300],
                    "upvote_ratio": post.upvote_ratio,
                })

            return {"subreddit": subreddit_name, "posts": posts, "count": len(posts)}
        except Exception as e:
            logger.warning("Reddit hot posts failed for r/%s: %s", subreddit_name, e)
            return {"subreddit": subreddit_name, "error": str(e), "posts": []}

    async def search_food_discussions(
        self,
        query: str,
        subreddits: list[str] | None = None,
        limit: int = 10,
    ) -> dict:
        """Search food/restaurant discussions on Reddit (async wrapper)."""
        subs = subreddits or ["france", "AskFrance", "FrenchFood", "restauration", "Cooking"]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._search_posts, query, subs, limit)

    async def get_trending_discussions(
        self,
        subreddit: str = "france",
        limit: int = 10,
    ) -> dict:
        """Get trending discussions from a subreddit (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_hot_posts, subreddit, limit)
