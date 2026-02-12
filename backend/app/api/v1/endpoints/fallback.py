"""
PresenceOS - Degraded Mode Fallback Endpoints

When the database is unavailable, these endpoints return mock data
instead of crashing with 500 errors. They are registered with the
same paths as the real endpoints but with LOWER priority via a
separate router.

The approach: a FastAPI middleware checks `app.state.degraded`.
If True and the request would hit an auth-protected endpoint,
we intercept it here and return mock data with `degraded: true`.
"""
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.resilience import registry
from app.core import mock_data

router = APIRouter(tags=["Fallback (Degraded Mode)"])


# ── Brands ───────────────────────────────────────────────────────

@router.get("/brands/{brand_id}")
async def get_brand_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_BRAND)


# ── Knowledge ────────────────────────────────────────────────────

@router.get("/knowledge/brands/{brand_id}")
async def list_knowledge_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_KNOWLEDGE_LIST)


@router.get("/knowledge/brands/{brand_id}/categories")
async def knowledge_categories_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_KNOWLEDGE_CATEGORIES)


# ── Ideas ────────────────────────────────────────────────────────

@router.get("/ideas/brands/{brand_id}")
async def list_ideas_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_IDEAS_LIST)


@router.get("/ideas/brands/{brand_id}/daily")
async def daily_ideas_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_IDEAS_LIST[:1])


# ── Drafts ───────────────────────────────────────────────────────

@router.get("/drafts/brands/{brand_id}")
async def list_drafts_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_DRAFTS_LIST)


# ── Connectors ───────────────────────────────────────────────────

@router.get("/connectors/brands/{brand_id}")
async def list_connectors_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_CONNECTORS_LIST)


# ── Posts ────────────────────────────────────────────────────────

@router.get("/posts/brands/{brand_id}")
async def list_posts_fallback(brand_id: str):
    return JSONResponse(content=[])


@router.get("/posts/brands/{brand_id}/calendar")
async def calendar_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_CALENDAR)


# ── Metrics ──────────────────────────────────────────────────────

@router.get("/metrics/brands/{brand_id}/dashboard")
async def dashboard_metrics_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_DASHBOARD_METRICS)


@router.get("/metrics/brands/{brand_id}/platforms")
async def platform_breakdown_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_PLATFORM_BREAKDOWN)


@router.get("/metrics/brands/{brand_id}/top-posts")
async def top_posts_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_TOP_POSTS)


@router.get("/metrics/brands/{brand_id}/learning")
async def learning_insights_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_LEARNING_INSIGHTS)


# ── Autopilot ────────────────────────────────────────────────────

@router.get("/autopilot/brands/{brand_id}/autopilot")
async def autopilot_config_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_AUTOPILOT_CONFIG)


@router.get("/autopilot/brands/{brand_id}/autopilot/pending")
async def autopilot_pending_fallback(brand_id: str):
    return JSONResponse(content=[])


# ── Media Library ────────────────────────────────────────────────

@router.get("/media-library/brands/{brand_id}/assets")
async def media_assets_fallback(brand_id: str):
    return JSONResponse(content=[])


@router.get("/media-library/brands/{brand_id}/voice-notes")
async def voice_notes_fallback(brand_id: str):
    return JSONResponse(content=[])


@router.get("/media-library/brands/{brand_id}/stats")
async def media_stats_fallback(brand_id: str):
    return JSONResponse(content=mock_data.MOCK_MEDIA_STATS)


# ── Users / Workspaces ──────────────────────────────────────────

@router.get("/users/me")
async def get_me_fallback():
    return JSONResponse(content={
        "id": "demo-user-001",
        "email": "dev@presenceos.local",
        "full_name": "Dev User",
        "is_active": True,
        "degraded": True,
    })


@router.get("/users/me/workspaces")
async def my_workspaces_fallback():
    return JSONResponse(content=[mock_data.MOCK_WORKSPACE])


@router.get("/workspaces/{workspace_id}/brands")
async def workspace_brands_fallback(workspace_id: str):
    return JSONResponse(content=mock_data.MOCK_BRANDS_LIST)


# ── Auth (degraded mode just returns a stub) ─────────────────────

@router.get("/auth/me")
async def auth_me_fallback():
    return JSONResponse(content={
        "id": "demo-user-001",
        "email": "dev@presenceos.local",
        "full_name": "Dev User",
        "is_active": True,
        "degraded": True,
    })
