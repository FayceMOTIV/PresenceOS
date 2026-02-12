"""
PresenceOS — Google Business Profile Autopublish (Feature 7)

Service for managing GBP autopublish configuration and publishing posts
to Google Business Profile via the GBP API.

In dev/degraded mode, operates without actual Google API calls, storing
configurations and simulating publish operations in-memory.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class GBPPostType(str, Enum):
    WHATS_NEW = "WHATS_NEW"
    EVENT = "EVENT"
    OFFER = "OFFER"


class GBPPublishStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"


# In-memory stores
_configs: dict[str, dict] = {}
_published_posts: dict[str, dict] = {}


class GBPPublisherService:
    """Manage GBP autopublish configuration and post publishing."""

    def get_config(self, brand_id: str) -> dict[str, Any]:
        """Get the GBP autopublish config for a brand."""
        if brand_id not in _configs:
            # Return default config
            return {
                "brand_id": brand_id,
                "enabled": False,
                "location_id": None,
                "auto_sync": False,
                "default_post_type": GBPPostType.WHATS_NEW.value,
                "default_cta": "LEARN_MORE",
                "include_photos": True,
                "include_offers": False,
                "publish_frequency": "daily",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        return _configs[brand_id]

    def update_config(self, brand_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update GBP autopublish configuration."""
        config = self.get_config(brand_id)
        config.update(updates)
        config["brand_id"] = brand_id
        config["updated_at"] = datetime.now(timezone.utc).isoformat()
        _configs[brand_id] = config
        logger.info("gbp_config_updated", brand_id=brand_id)
        return config

    def toggle(self, brand_id: str) -> dict[str, Any]:
        """Toggle GBP autopublish on/off."""
        config = self.get_config(brand_id)
        config["enabled"] = not config.get("enabled", False)
        config["updated_at"] = datetime.now(timezone.utc).isoformat()
        _configs[brand_id] = config
        logger.info("gbp_toggled", brand_id=brand_id, enabled=config["enabled"])
        return config

    def publish_post(
        self,
        brand_id: str,
        caption: str,
        media_urls: list[str] | None = None,
        post_type: str = "WHATS_NEW",
        cta_type: str | None = None,
        cta_url: str | None = None,
        event_title: str | None = None,
        event_start: str | None = None,
        event_end: str | None = None,
        offer_coupon: str | None = None,
        offer_terms: str | None = None,
    ) -> dict[str, Any]:
        """Publish a post to GBP.

        In dev mode this simulates the GBP API call and stores the post
        in memory. In production, this would use the Google My Business API.
        """
        post_id = str(uuid.uuid4())

        post = {
            "id": post_id,
            "brand_id": brand_id,
            "post_type": post_type,
            "caption": caption,
            "media_urls": media_urls or [],
            "cta_type": cta_type,
            "cta_url": cta_url,
            "event_title": event_title,
            "event_start": event_start,
            "event_end": event_end,
            "offer_coupon": offer_coupon,
            "offer_terms": offer_terms,
            "status": GBPPublishStatus.PUBLISHED.value,
            "gbp_post_id": f"gbp-sim-{post_id[:8]}",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        _published_posts[post_id] = post
        logger.info("gbp_post_published", post_id=post_id, brand_id=brand_id)
        return post

    def get_published(self, brand_id: str) -> list[dict[str, Any]]:
        """List all published GBP posts for a brand."""
        return [
            p for p in _published_posts.values()
            if p["brand_id"] == brand_id
        ]

    def get_post(self, post_id: str) -> dict[str, Any] | None:
        """Get a specific published GBP post."""
        return _published_posts.get(post_id)

    def delete_post(self, post_id: str) -> bool:
        """Delete a GBP post (remove from GBP and local store)."""
        if post_id in _published_posts:
            del _published_posts[post_id]
            logger.info("gbp_post_deleted", post_id=post_id)
            return True
        return False

    def get_stats(self, brand_id: str) -> dict[str, Any]:
        """Get GBP publishing stats for a brand."""
        posts = self.get_published(brand_id)
        return {
            "brand_id": brand_id,
            "total_published": len(posts),
            "this_month": sum(
                1 for p in posts
                if p["published_at"][:7] == datetime.now(timezone.utc).strftime("%Y-%m")
            ),
            "post_types": {
                pt.value: sum(1 for p in posts if p["post_type"] == pt.value)
                for pt in GBPPostType
            },
            "last_published": posts[-1]["published_at"] if posts else None,
        }
