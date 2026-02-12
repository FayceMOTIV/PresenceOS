"""
PresenceOS - Smart Scheduling Service (Feature 1)

Determines optimal posting times per platform using industry benchmarks
(cold start) and learned engagement data (when available).

Phases:
1. Cold start: Restaurant industry benchmarks (Sprout Social / Later 2025)
2. Learning: After 20+ posts, analyze real engagement by time slot
3. Prediction: Weighted blend of benchmarks + own data
"""
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"


# ── Industry Benchmarks (Restaurant vertical, 2025) ──────────

BENCHMARKS: dict[str, list[dict[str, Any]]] = {
    "instagram": [
        {"day": "monday", "hours": [11, 13], "score": 85},
        {"day": "tuesday", "hours": [10, 14], "score": 88},
        {"day": "wednesday", "hours": [11, 13], "score": 87},
        {"day": "thursday", "hours": [10, 12, 19], "score": 90},
        {"day": "friday", "hours": [10, 13], "score": 86},
        {"day": "saturday", "hours": [9, 11], "score": 82},
        {"day": "sunday", "hours": [10, 13], "score": 80},
    ],
    "tiktok": [
        {"day": "monday", "hours": [18, 21], "score": 83},
        {"day": "tuesday", "hours": [19, 21], "score": 85},
        {"day": "wednesday", "hours": [18, 20], "score": 84},
        {"day": "thursday", "hours": [18, 20], "score": 88},
        {"day": "friday", "hours": [17, 19], "score": 90},
        {"day": "saturday", "hours": [11, 14, 20], "score": 92},
        {"day": "sunday", "hours": [12, 15, 19], "score": 89},
    ],
    "facebook": [
        {"day": "monday", "hours": [9, 12, 15], "score": 80},
        {"day": "tuesday", "hours": [9, 12, 15], "score": 80},
        {"day": "wednesday", "hours": [9, 12, 15], "score": 80},
        {"day": "thursday", "hours": [9, 12, 15], "score": 80},
        {"day": "friday", "hours": [9, 12, 15], "score": 80},
        {"day": "saturday", "hours": [10, 13], "score": 78},
        {"day": "sunday", "hours": [10, 13], "score": 78},
    ],
    "linkedin": [
        {"day": "monday", "hours": [8, 10], "score": 85},
        {"day": "tuesday", "hours": [8, 10, 12], "score": 90},
        {"day": "wednesday", "hours": [8, 10, 12], "score": 88},
        {"day": "thursday", "hours": [8, 10], "score": 87},
        {"day": "friday", "hours": [8, 10], "score": 82},
    ],
}

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# ── In-memory scheduled posts store (no DB required) ─────────

_scheduled_posts: dict[str, dict] = {}


class SmartSchedulerService:
    """Determines optimal posting times and manages scheduled posts."""

    def get_optimal_times(
        self,
        brand_id: str,
        platform: str = "instagram",
        timezone_offset: int = 1,  # Europe/Paris = UTC+1
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the top N optimal time slots for the next 7 days.

        Args:
            brand_id: Brand identifier (for future learned data)
            platform: Target social platform
            timezone_offset: Hours from UTC (e.g. 1 for CET)
            count: Number of slots to return

        Returns:
            List of {datetime, day, hour, score, platform} sorted by score desc
        """
        benchmarks = BENCHMARKS.get(platform, BENCHMARKS["instagram"])
        now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)
        slots = []

        for day_offset in range(7):
            target_date = now + timedelta(days=day_offset)
            day_name = DAY_NAMES[target_date.weekday()]

            for entry in benchmarks:
                if entry["day"] != day_name:
                    continue
                for hour in entry["hours"]:
                    slot_dt = target_date.replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    )
                    # Skip past times
                    if slot_dt <= now:
                        continue
                    slots.append({
                        "datetime": slot_dt.isoformat(),
                        "day": day_name,
                        "day_label": _day_label_fr(day_name),
                        "hour": hour,
                        "hour_label": f"{hour:02d}:00",
                        "score": entry["score"],
                        "platform": platform,
                    })

        # Sort by score descending, then by datetime ascending
        slots.sort(key=lambda s: (-s["score"], s["datetime"]))
        return slots[:count]

    def get_next_optimal(
        self,
        brand_id: str,
        platform: str = "instagram",
        timezone_offset: int = 1,
    ) -> dict[str, Any]:
        """Return the single next best time slot."""
        slots = self.get_optimal_times(brand_id, platform, timezone_offset, count=1)
        if slots:
            return slots[0]
        # Fallback: next day at noon
        now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)
        tomorrow = now + timedelta(days=1)
        return {
            "datetime": tomorrow.replace(hour=12, minute=0, second=0).isoformat(),
            "day": DAY_NAMES[tomorrow.weekday()],
            "day_label": _day_label_fr(DAY_NAMES[tomorrow.weekday()]),
            "hour": 12,
            "hour_label": "12:00",
            "score": 70,
            "platform": platform,
        }

    def schedule_post(
        self,
        brand_id: str,
        platform: str,
        content: dict[str, Any],
        scheduled_at: Optional[str] = None,
        use_optimal: bool = True,
    ) -> dict[str, Any]:
        """Schedule a post for publishing at the optimal time.

        Args:
            brand_id: Target brand
            platform: Target platform
            content: Post content {caption, media_urls, hashtags}
            scheduled_at: ISO datetime (if manual), or None for optimal
            use_optimal: Auto-pick the best slot if scheduled_at is None

        Returns:
            Scheduled post record
        """
        if scheduled_at:
            publish_at = scheduled_at
            score = self._score_for_time(platform, scheduled_at)
        elif use_optimal:
            optimal = self.get_next_optimal(brand_id, platform)
            publish_at = optimal["datetime"]
            score = optimal["score"]
        else:
            # Immediate
            publish_at = datetime.now(timezone.utc).isoformat()
            score = 50  # No optimization

        post_id = str(uuid.uuid4())
        record = {
            "id": post_id,
            "brand_id": brand_id,
            "platform": platform,
            "caption": content.get("caption", ""),
            "media_urls": content.get("media_urls", []),
            "hashtags": content.get("hashtags", []),
            "scheduled_at": publish_at,
            "score": score,
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _scheduled_posts[post_id] = record
        logger.info("Post scheduled", post_id=post_id, platform=platform, at=publish_at, score=score)
        return record

    def get_scheduled(self, brand_id: str) -> list[dict[str, Any]]:
        """Get all scheduled posts for a brand."""
        return [
            p for p in _scheduled_posts.values()
            if p["brand_id"] == brand_id
        ]

    def get_calendar(
        self,
        brand_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get calendar view of scheduled posts with optimal time hints."""
        posts = self.get_scheduled(brand_id)

        # Generate optimal slots for each platform for the next 7 days
        hints = {}
        for platform in ["instagram", "tiktok", "facebook", "linkedin"]:
            hints[platform] = self.get_optimal_times(brand_id, platform, count=3)

        return {
            "posts": posts,
            "optimal_hints": hints,
            "total": len(posts),
        }

    def reschedule(self, post_id: str, new_datetime: str) -> Optional[dict[str, Any]]:
        """Move a scheduled post to a different time."""
        post = _scheduled_posts.get(post_id)
        if not post:
            return None
        post["scheduled_at"] = new_datetime
        post["score"] = self._score_for_time(post["platform"], new_datetime)
        return post

    def cancel(self, post_id: str) -> bool:
        """Cancel a scheduled post."""
        if post_id in _scheduled_posts:
            _scheduled_posts[post_id]["status"] = "cancelled"
            return True
        return False

    def _score_for_time(self, platform: str, iso_datetime: str) -> int:
        """Calculate engagement score for a specific time."""
        try:
            dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
            day_name = DAY_NAMES[dt.weekday()]
            hour = dt.hour
            benchmarks = BENCHMARKS.get(platform, [])
            for entry in benchmarks:
                if entry["day"] == day_name and hour in entry["hours"]:
                    return entry["score"]
            # Off-peak
            return 50
        except Exception:
            return 50


def _day_label_fr(day: str) -> str:
    """Convert English day name to French label."""
    mapping = {
        "monday": "Lundi",
        "tuesday": "Mardi",
        "wednesday": "Mercredi",
        "thursday": "Jeudi",
        "friday": "Vendredi",
        "saturday": "Samedi",
        "sunday": "Dimanche",
    }
    return mapping.get(day, day.capitalize())
