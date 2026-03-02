"""
Ilyas Intelligence — Instagram Module
Uses instaloader (free, no API key) to analyze competitor profiles and hashtags.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class InstagramIntel:
    """Instagram intelligence via instaloader (scraping-based)."""

    def __init__(self) -> None:
        self._loader = None

    def _get_loader(self):
        if self._loader is None:
            import instaloader
            self._loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                quiet=True,
            )
            settings = get_settings()
            if settings.instagram_username and settings.instagram_password:
                try:
                    self._loader.login(settings.instagram_username, settings.instagram_password)
                except Exception as e:
                    logger.warning("Instagram login failed (continuing anonymous): %s", e)
        return self._loader

    def _analyze_profile(self, username: str) -> dict:
        """Scrape public profile info for a competitor."""
        try:
            import instaloader
            loader = self._get_loader()
            profile = instaloader.Profile.from_username(loader.context, username)

            recent_posts = []
            for i, post in enumerate(profile.get_posts()):
                if i >= 12:
                    break
                recent_posts.append({
                    "date": post.date_utc.isoformat(),
                    "likes": post.likes,
                    "comments": post.comments,
                    "caption": (post.caption or "")[:200],
                    "is_video": post.is_video,
                    "hashtags": list(post.caption_hashtags) if post.caption_hashtags else [],
                })

            avg_likes = sum(p["likes"] for p in recent_posts) / max(len(recent_posts), 1)
            avg_comments = sum(p["comments"] for p in recent_posts) / max(len(recent_posts), 1)

            return {
                "username": username,
                "full_name": profile.full_name,
                "followers": profile.followers,
                "following": profile.followees,
                "posts_count": profile.mediacount,
                "bio": profile.biography,
                "is_verified": profile.is_verified,
                "recent_posts": recent_posts,
                "avg_likes": round(avg_likes),
                "avg_comments": round(avg_comments),
                "engagement_rate": round(
                    (avg_likes + avg_comments) / max(profile.followers, 1) * 100, 2
                ),
            }
        except Exception as e:
            logger.warning("Instagram profile analysis failed for @%s: %s", username, e)
            return {"username": username, "error": str(e)}

    def _analyze_hashtag(self, tag: str) -> dict:
        """Get recent top posts for a hashtag."""
        try:
            import instaloader
            loader = self._get_loader()
            hashtag = instaloader.Hashtag.from_name(loader.context, tag)

            top_posts = []
            for i, post in enumerate(hashtag.get_top_posts()):
                if i >= 9:
                    break
                top_posts.append({
                    "owner": post.owner_username,
                    "likes": post.likes,
                    "comments": post.comments,
                    "caption": (post.caption or "")[:200],
                    "date": post.date_utc.isoformat(),
                })

            return {
                "hashtag": tag,
                "post_count": hashtag.mediacount,
                "top_posts": top_posts,
            }
        except Exception as e:
            logger.warning("Instagram hashtag analysis failed for #%s: %s", tag, e)
            return {"hashtag": tag, "error": str(e)}

    async def analyze_competitor(self, username: str) -> dict:
        """Analyze a competitor's Instagram profile (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._analyze_profile, username)

    async def analyze_hashtag(self, tag: str) -> dict:
        """Analyze a hashtag's top posts (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._analyze_hashtag, tag)
