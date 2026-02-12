"""
PresenceOS - Pexels B-Roll Service (Sprint 9C)

Fetches royalty-free stock footage from Pexels to complement
user-uploaded media for professional video production.
"""
import structlog
import httpx

from app.core.config import settings

logger = structlog.get_logger()

PEXELS_API_BASE = "https://api.pexels.com"


class PexelsService:
    """Service for finding B-roll footage on Pexels."""

    def __init__(self):
        self.api_key = settings.pexels_api_key
        self.headers = {"Authorization": self.api_key}

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search_videos(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "portrait",
        size: str = "medium",
    ) -> list[dict]:
        """
        Search for videos on Pexels.

        Returns list of dicts with keys: id, url, width, height, duration, image (preview)
        """
        if not self.is_configured:
            logger.warning("Pexels API key not configured")
            return []

        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": size,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PEXELS_API_BASE}/videos/search",
                    params=params,
                    headers=self.headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for video in data.get("videos", []):
                    # Pick the best video file (HD, mp4)
                    best_file = self._pick_best_file(video.get("video_files", []))
                    if best_file:
                        results.append({
                            "id": video["id"],
                            "url": best_file["link"],
                            "width": best_file.get("width", 1080),
                            "height": best_file.get("height", 1920),
                            "duration": video.get("duration", 0),
                            "image": video.get("image", ""),
                        })

                logger.info("Pexels search", query=query, results=len(results))
                return results

        except Exception as e:
            logger.error("Pexels search failed", query=query, error=str(e))
            return []

    async def search_photos(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "portrait",
    ) -> list[dict]:
        """
        Search for photos on Pexels.

        Returns list of dicts with keys: id, url, width, height, photographer
        """
        if not self.is_configured:
            return []

        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{PEXELS_API_BASE}/v1/search",
                    params=params,
                    headers=self.headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for photo in data.get("photos", []):
                    results.append({
                        "id": photo["id"],
                        "url": photo["src"].get("large2x", photo["src"]["original"]),
                        "width": photo["width"],
                        "height": photo["height"],
                        "photographer": photo.get("photographer", ""),
                    })

                return results

        except Exception as e:
            logger.error("Pexels photo search failed", query=query, error=str(e))
            return []

    async def download_video(self, url: str) -> bytes | None:
        """Download a video file from Pexels."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=60.0)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error("Pexels download failed", url=url, error=str(e))
            return None

    def _pick_best_file(self, video_files: list[dict]) -> dict | None:
        """Pick the best video file for Instagram Reels (portrait, HD)."""
        if not video_files:
            return None

        # Prefer HD mp4 files
        mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4"]
        if not mp4_files:
            mp4_files = video_files

        # Sort by quality (height closest to 1920)
        mp4_files.sort(
            key=lambda f: abs((f.get("height") or 0) - 1920)
        )

        return mp4_files[0] if mp4_files else None
