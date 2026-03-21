"""
Timeouts RS3 — centralized timeout configuration.

Video Kling 2.6 Pro = 45-90s actual generation time -> timeout 120s.
Fast routes (text, image lookups) keep 30s.
Image generation/enhancement gets 45s.

Usage:
    from app.core.timeouts import get_http_timeout, TIMEOUT_VIDEO

    async with httpx.AsyncClient(timeout=get_http_timeout("video")) as client:
        ...
"""

import httpx

# ── Timeout constants (seconds) ─────────────────────────────────────

TIMEOUT_FAST = 30          # Text APIs, metadata lookups, social APIs
TIMEOUT_IMAGE = 45         # Image generation/enhancement
TIMEOUT_VIDEO = 120        # Video generation (Kling 2.6 Pro: 45-90s typical)
TIMEOUT_VIDEO_DOWNLOAD = 120  # Downloading generated video from fal.ai

# Celery task limits for video tasks
TIMEOUT_CELERY_SOFT = 110  # Soft limit: allows graceful cleanup
TIMEOUT_CELERY_HARD = 130  # Hard limit: SIGKILL after this

# Server-level (Uvicorn/Gunicorn)
TIMEOUT_SERVER = 140       # Must exceed TIMEOUT_CELERY_HARD


def get_http_timeout(operation: str = "fast") -> httpx.Timeout:
    """Return an httpx.Timeout for the given operation type.

    Args:
        operation: "fast" (30s), "image" (45s), or "video" (120s, connect=10s).

    Returns:
        httpx.Timeout configured for the operation.
    """
    mapping = {
        "fast": httpx.Timeout(TIMEOUT_FAST),
        "image": httpx.Timeout(TIMEOUT_IMAGE),
        "video": httpx.Timeout(TIMEOUT_VIDEO, connect=10.0),
        "video_download": httpx.Timeout(TIMEOUT_VIDEO_DOWNLOAD, connect=10.0),
    }
    return mapping.get(operation, httpx.Timeout(TIMEOUT_FAST))
