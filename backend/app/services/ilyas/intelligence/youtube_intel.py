"""
Ilyas Intelligence — YouTube Module
Uses YouTube Data API v3 (free quota: 10,000 units/day) for food content analysis.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class YouTubeIntel:
    """YouTube intelligence via Data API v3 for food/restaurant video trends."""

    def __init__(self) -> None:
        self._service = None

    def _get_service(self):
        if self._service is None:
            settings = get_settings()
            if not settings.youtube_api_key:
                return None

            from googleapiclient.discovery import build
            self._service = build("youtube", "v3", developerKey=settings.youtube_api_key)
        return self._service

    def _search_videos(self, query: str, max_results: int) -> dict:
        """Search YouTube for food/restaurant videos."""
        try:
            service = self._get_service()
            if service is None:
                return {"query": query, "error": "YouTube API key not configured", "videos": []}

            request = service.search().list(
                part="snippet",
                q=query,
                type="video",
                order="relevance",
                regionCode="FR",
                relevanceLanguage="fr",
                maxResults=max_results,
            )
            response = request.execute()

            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
            if not video_ids:
                return {"query": query, "videos": [], "count": 0}

            stats_request = service.videos().list(
                part="statistics,contentDetails",
                id=",".join(video_ids),
            )
            stats_response = stats_request.execute()

            stats_map = {}
            for item in stats_response.get("items", []):
                stats_map[item["id"]] = item.get("statistics", {})

            videos = []
            for item in response.get("items", []):
                vid_id = item["id"]["videoId"]
                snippet = item["snippet"]
                stats = stats_map.get(vid_id, {})
                videos.append({
                    "video_id": vid_id,
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "description": snippet.get("description", "")[:300],
                    "published_at": snippet.get("publishedAt", ""),
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "url": f"https://youtube.com/watch?v={vid_id}",
                })

            return {"query": query, "videos": videos, "count": len(videos)}
        except Exception as e:
            logger.warning("YouTube search failed: %s", e)
            return {"query": query, "error": str(e), "videos": []}

    def _get_channel_info(self, channel_id: str) -> dict:
        """Get channel info and recent uploads."""
        try:
            service = self._get_service()
            if service is None:
                return {"channel_id": channel_id, "error": "YouTube API key not configured"}

            ch_request = service.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id,
            )
            ch_response = ch_request.execute()

            items = ch_response.get("items", [])
            if not items:
                return {"channel_id": channel_id, "error": "Channel not found"}

            channel = items[0]
            snippet = channel["snippet"]
            stats = channel.get("statistics", {})

            uploads_id = channel.get("contentDetails", {}).get(
                "relatedPlaylists", {}
            ).get("uploads")

            recent_videos = []
            if uploads_id:
                pl_request = service.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_id,
                    maxResults=10,
                )
                pl_response = pl_request.execute()
                for pl_item in pl_response.get("items", []):
                    pl_snippet = pl_item["snippet"]
                    recent_videos.append({
                        "title": pl_snippet.get("title", ""),
                        "published_at": pl_snippet.get("publishedAt", ""),
                        "video_id": pl_snippet.get("resourceId", {}).get("videoId", ""),
                    })

            return {
                "channel_id": channel_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:300],
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "recent_videos": recent_videos,
            }
        except Exception as e:
            logger.warning("YouTube channel info failed: %s", e)
            return {"channel_id": channel_id, "error": str(e)}

    async def search_food_videos(self, query: str, max_results: int = 10) -> dict:
        """Search food/restaurant YouTube videos (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._search_videos, query, max_results)

    async def analyze_channel(self, channel_id: str) -> dict:
        """Analyze a YouTube channel (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._get_channel_info, channel_id)
