"""
Ilyas Intelligence — TikTok Module
Uses TikTokApi + playwright for trending sounds/hashtags.
Falls back to yt-dlp for video metadata extraction.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class TikTokIntel:
    """TikTok intelligence via TikTokApi (playwright-based) and yt-dlp."""

    def __init__(self) -> None:
        self._api = None

    async def _get_api(self):
        if self._api is None:
            try:
                from TikTokApi import TikTokApi
                self._api = TikTokApi()
                await self._api.create_sessions(
                    num_sessions=1,
                    sleep_after=3,
                    headless=True,
                )
            except Exception as e:
                logger.warning("TikTokApi session creation failed: %s", e)
                self._api = None
        return self._api

    async def get_trending_hashtags(self, count: int = 10) -> dict:
        """Get currently trending hashtags on TikTok."""
        try:
            api = await self._get_api()
            if api is None:
                return {"error": "TikTokApi not available", "hashtags": []}

            hashtags = []
            async for tag in api.trending.hashtags(count=count):
                hashtags.append({
                    "name": tag.name,
                    "views": tag.as_dict.get("stats", {}).get("videoCount", 0),
                })

            return {"hashtags": hashtags, "count": len(hashtags)}
        except Exception as e:
            logger.warning("TikTok trending hashtags failed: %s", e)
            return {"error": str(e), "hashtags": []}

    async def search_videos(self, keyword: str, count: int = 10) -> dict:
        """Search TikTok videos by keyword."""
        try:
            api = await self._get_api()
            if api is None:
                return {"keyword": keyword, "error": "TikTokApi not available", "videos": []}

            videos = []
            async for video in api.search.videos(keyword, count=count):
                info = video.as_dict
                stats = info.get("stats", {})
                videos.append({
                    "desc": info.get("desc", "")[:200],
                    "author": info.get("author", {}).get("uniqueId", ""),
                    "plays": stats.get("playCount", 0),
                    "likes": stats.get("diggCount", 0),
                    "comments": stats.get("commentCount", 0),
                    "shares": stats.get("shareCount", 0),
                })

            return {"keyword": keyword, "videos": videos, "count": len(videos)}
        except Exception as e:
            logger.warning("TikTok search failed for '%s': %s", keyword, e)
            return {"keyword": keyword, "error": str(e), "videos": []}

    async def get_video_info(self, url: str) -> dict:
        """Extract metadata from a TikTok video URL using yt-dlp (no API needed)."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._extract_video_info, url)
        except Exception as e:
            logger.warning("TikTok video info extraction failed: %s", e)
            return {"url": url, "error": str(e)}

    def _extract_video_info(self, url: str) -> dict:
        """Sync yt-dlp extraction."""
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "url": url,
                "title": info.get("title", ""),
                "description": info.get("description", "")[:300],
                "uploader": info.get("uploader", ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "comment_count": info.get("comment_count", 0),
                "duration": info.get("duration", 0),
                "upload_date": info.get("upload_date", ""),
                "tags": info.get("tags", [])[:10],
            }
