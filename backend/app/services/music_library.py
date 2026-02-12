"""
PresenceOS - Music Library Service (Sprint 9C)

Manages a collection of CC0/royalty-free music tracks
for use in generated videos. Tracks are organized by mood
and selected to match content themes.
"""
import os
import random
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Mood categories for music tracks
MOODS = [
    "energetic",      # Upbeat, high-energy
    "chill",          # Relaxed, calm
    "inspiring",      # Motivational, uplifting
    "dramatic",       # Cinematic, intense
    "happy",          # Fun, cheerful
    "corporate",      # Professional, neutral
    "ambient",        # Background, subtle
    "trendy",         # Modern, TikTok-style
]

# Default embedded tracks (short loops, CC0)
DEFAULT_TRACKS = {
    "energetic": "energetic_loop.mp3",
    "chill": "chill_loop.mp3",
    "inspiring": "inspiring_loop.mp3",
    "dramatic": "dramatic_loop.mp3",
    "happy": "happy_loop.mp3",
    "corporate": "corporate_loop.mp3",
    "ambient": "ambient_loop.mp3",
    "trendy": "trendy_loop.mp3",
}


class MusicLibrary:
    """Service for managing and selecting background music."""

    def __init__(self):
        self.music_path = settings.music_library_path
        self._tracks_cache: dict[str, list[str]] | None = None

    def _scan_tracks(self) -> dict[str, list[str]]:
        """Scan the music directory for tracks organized by mood."""
        if self._tracks_cache is not None:
            return self._tracks_cache

        tracks: dict[str, list[str]] = {mood: [] for mood in MOODS}

        if not os.path.exists(self.music_path):
            logger.warning("Music library path does not exist", path=self.music_path)
            self._tracks_cache = tracks
            return tracks

        for mood in MOODS:
            mood_dir = os.path.join(self.music_path, mood)
            if os.path.isdir(mood_dir):
                for f in os.listdir(mood_dir):
                    if f.endswith((".mp3", ".wav", ".ogg", ".aac")):
                        tracks[mood].append(os.path.join(mood_dir, f))

        total = sum(len(v) for v in tracks.values())
        logger.info("Music library scanned", total_tracks=total)
        self._tracks_cache = tracks
        return tracks

    def get_track(self, mood: str = "chill") -> str | None:
        """
        Get a random track for the specified mood.

        Falls back to any available track if the mood has no tracks.
        Returns the file path or None if no music available.
        """
        tracks = self._scan_tracks()

        # Try exact mood
        if tracks.get(mood):
            return random.choice(tracks[mood])

        # Fallback: any available mood
        all_tracks = [t for ts in tracks.values() for t in ts]
        if all_tracks:
            return random.choice(all_tracks)

        logger.warning("No music tracks available", requested_mood=mood)
        return None

    def suggest_mood(self, tags: list[str], description: str = "") -> str:
        """
        Suggest a music mood based on content tags and description.

        Uses simple keyword matching.
        """
        text = " ".join(tags).lower() + " " + description.lower()

        mood_keywords = {
            "energetic": ["sport", "fitness", "dance", "action", "fast", "gym"],
            "chill": ["relax", "calm", "zen", "peaceful", "sunset", "coffee"],
            "inspiring": ["motivation", "success", "growth", "inspire", "dream"],
            "dramatic": ["cinema", "film", "epic", "dramatic", "reveal"],
            "happy": ["fun", "smile", "joy", "happy", "celebration", "party"],
            "corporate": ["business", "corporate", "office", "professional"],
            "ambient": ["nature", "landscape", "minimal", "abstract"],
            "trendy": ["trend", "viral", "tiktok", "reel", "fashion", "style"],
        }

        best_mood = "chill"
        best_score = 0

        for mood, keywords in mood_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_mood = mood

        return best_mood

    def list_moods(self) -> list[dict]:
        """List all moods with their track counts."""
        tracks = self._scan_tracks()
        return [
            {"mood": mood, "track_count": len(tracks.get(mood, []))}
            for mood in MOODS
        ]
