"""
PresenceOS - Degraded Mode Middleware

When app.state.degraded is True, this middleware intercepts GET requests
to auth-protected API endpoints and returns mock data instead of letting
them crash with 401/500 errors.

POST/PATCH/DELETE requests in degraded mode return a clear error message
explaining the DB is unavailable.

Endpoints that don't require auth (chat, upload, health) are passed through.
"""
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core import mock_data

logger = logging.getLogger(__name__)

# Paths that work without DB (passthrough even in degraded mode)
PASSTHROUGH_PREFIXES = (
    "/health",
    "/api/v1/chat/",
    "/api/v1/photos/",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/onboarding/",
    "/api/v1/scheduling/",
    "/api/v1/repurpose/",
    "/api/v1/gbp/",
    "/api/v1/analytics/",
    "/api/v1/reputation/",
    "/api/v1/trends/",
    "/api/v1/competitor/",
    "/api/v1/hyperlocal/",
    "/uploads/",
    "/webhook/",
)

# GET fallback map: path pattern -> mock data
# Uses simple prefix matching with {brand_id} wildcard handling
_FALLBACK_MAP = {
    # Brands
    ("GET", "/api/v1/brands/"): mock_data.MOCK_BRAND,
    # Knowledge
    ("GET", "/api/v1/knowledge/brands/", "/categories"): mock_data.MOCK_KNOWLEDGE_CATEGORIES,
    ("GET", "/api/v1/knowledge/brands/"): mock_data.MOCK_KNOWLEDGE_LIST,
    # Ideas
    ("GET", "/api/v1/ideas/brands/", "/daily"): mock_data.MOCK_IDEAS_LIST[:1],
    ("GET", "/api/v1/ideas/brands/"): mock_data.MOCK_IDEAS_LIST,
    # Drafts
    ("GET", "/api/v1/drafts/brands/"): mock_data.MOCK_DRAFTS_LIST,
    # Connectors
    ("GET", "/api/v1/connectors/brands/"): mock_data.MOCK_CONNECTORS_LIST,
    # Posts
    ("GET", "/api/v1/posts/brands/", "/calendar"): mock_data.MOCK_CALENDAR,
    ("GET", "/api/v1/posts/brands/"): [],
    # Metrics
    ("GET", "/api/v1/metrics/brands/", "/dashboard"): mock_data.MOCK_DASHBOARD_METRICS,
    ("GET", "/api/v1/metrics/brands/", "/platforms"): mock_data.MOCK_PLATFORM_BREAKDOWN,
    ("GET", "/api/v1/metrics/brands/", "/top-posts"): mock_data.MOCK_TOP_POSTS,
    ("GET", "/api/v1/metrics/brands/", "/learning"): mock_data.MOCK_LEARNING_INSIGHTS,
    # Autopilot
    ("GET", "/api/v1/autopilot/brands/", "/autopilot/pending"): [],
    ("GET", "/api/v1/autopilot/brands/", "/autopilot"): mock_data.MOCK_AUTOPILOT_CONFIG,
    # Media Library
    ("GET", "/api/v1/media-library/brands/", "/stats"): mock_data.MOCK_MEDIA_STATS,
    ("GET", "/api/v1/media-library/brands/", "/assets"): [],
    ("GET", "/api/v1/media-library/brands/", "/voice-notes"): [],
    # Users
    ("GET", "/api/v1/users/me/workspaces"): [mock_data.MOCK_WORKSPACE],
    ("GET", "/api/v1/users/me"): {
        "id": "demo-user-001",
        "email": "dev@presenceos.local",
        "full_name": "Dev User",
        "is_active": True,
        "degraded": True,
    },
    # Auth
    ("GET", "/api/v1/auth/me"): {
        "id": "demo-user-001",
        "email": "dev@presenceos.local",
        "full_name": "Dev User",
        "is_active": True,
        "degraded": True,
    },
    # Workspaces
    ("GET", "/api/v1/workspaces/", "/brands"): mock_data.MOCK_BRANDS_LIST,
}


def _match_fallback(method: str, path: str):
    """Match a request against the fallback map.

    Supports two key formats:
    - (METHOD, prefix): matches any path starting with prefix
    - (METHOD, prefix, suffix): matches paths starting with prefix AND ending with suffix
    """
    for key, data in _FALLBACK_MAP.items():
        if len(key) == 3:
            m, prefix, suffix = key
            if method == m and path.startswith(prefix) and path.endswith(suffix):
                return data
        elif len(key) == 2:
            m, prefix = key
            if method == m and path.startswith(prefix):
                return data
    return None


class DegradedModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Always pass through non-degraded mode
        if not getattr(request.app.state, "degraded", False):
            return await call_next(request)

        # Always pass through certain paths (chat, health, uploads, etc.)
        for prefix in PASSTHROUGH_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # In degraded mode, try to serve mock data for GET requests
        if method == "GET":
            fallback = _match_fallback(method, path)
            if fallback is not None:
                return JSONResponse(content=fallback)

        # For write operations in degraded mode, return a clear error
        if method in ("POST", "PATCH", "PUT", "DELETE") and path.startswith("/api/v1/"):
            # But allow chat and upload to pass through
            if "/chat/" not in path and "/upload" not in path and "/onboarding/" not in path:
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Base de donnees indisponible. Cette operation necessite la DB.",
                        "degraded": True,
                    },
                )

        # Fall through to normal processing
        return await call_next(request)
