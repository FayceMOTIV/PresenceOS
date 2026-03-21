"""
PresenceOS - Brain API Endpoints
"""
import uuid

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.brain import BrainMemory, UGCPost
from app.services.brand_brain import BrandBrain
from app.services.visual_brain import VisualBrain
from app.services.brand_dna import extract_brand_dna
from app.services.analytics_service import get_analytics_overview
from app.services.calendar_service import get_upcoming_events
from app.services.ugc_service import add_ugc_manual, list_ugc, generate_permission_request_dm

logger = structlog.get_logger()
router = APIRouter()


# ── Request models ───────────────────────────────────────────

class RememberRequest(BaseModel):
    content: str = Field(..., min_length=3)
    memory_type: str = Field(default="episodic")
    source: str | None = None


class RecallRequest(BaseModel):
    query: str = Field(..., min_length=1)
    memory_type: str | None = None


class ExtractDNARequest(BaseModel):
    image_urls: list[str] = Field(..., min_items=1, max_items=5)
    niche: str = Field(default="restaurant")


class RegisterPushTokenRequest(BaseModel):
    expo_push_token: str = Field(..., min_length=1)


class AddUGCRequest(BaseModel):
    source_platform: str
    author_username: str
    media_url: str | None = None
    caption: str | None = None
    source_url: str | None = None


# ── Brain Status ─────────────────────────────────────────────

@router.get("/{brand_id}/status")
async def get_brain_status(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    await get_brand(brand_id, current_user, db)
    brain = BrandBrain(brand_id, db)
    return await brain.get_brain_status()


# ── Memories ─────────────────────────────────────────────────

@router.post("/{brand_id}/remember")
async def remember(
    brand_id: uuid.UUID,
    body: RememberRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    await get_brand(brand_id, current_user, db)
    brain = BrandBrain(brand_id, db)
    memory = await brain.remember(body.content, body.memory_type, body.source)
    return {"id": str(memory.id), "memory_type": memory.memory_type, "content": memory.content}


@router.post("/{brand_id}/recall")
async def recall(
    brand_id: uuid.UUID,
    body: RecallRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    await get_brand(brand_id, current_user, db)
    brain = BrandBrain(brand_id, db)
    return await brain.recall(body.query, memory_type=body.memory_type)


@router.post("/{brand_id}/reflection")
async def trigger_reflection(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    await get_brand(brand_id, current_user, db)
    brain = BrandBrain(brand_id, db)
    result = await brain.weekly_reflection()
    return {"result": result}


# ── Visual Brain ─────────────────────────────────────────────

@router.get("/{brand_id}/visual/status")
async def get_visual_brain_status(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    await get_brand(brand_id, current_user, db)
    vb = VisualBrain(brand_id, db)
    return await vb.get_visual_brain_status()


# ── BrandDNA ─────────────────────────────────────────────────

@router.post("/{brand_id}/extract-dna")
async def extract_dna(
    brand_id: uuid.UUID,
    body: ExtractDNARequest,
    current_user: CurrentUser,
    db: DBSession,
):
    brand = await get_brand(brand_id, current_user, db)
    dna = await extract_brand_dna(body.image_urls, brand.name, body.niche)

    # Store DNA on brand
    from sqlalchemy import update
    from app.models.brand import Brand
    await db.execute(
        update(Brand).where(Brand.id == brand_id).values(brand_dna=dna, niche=body.niche)
    )
    await db.commit()

    return {"brand_dna": dna}


# ── Analytics ────────────────────────────────────────────────

@router.get("/{brand_id}/analytics")
async def get_analytics(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    days: int = 30,
):
    await get_brand(brand_id, current_user, db)
    return await get_analytics_overview(brand_id, db, days)


# ── Calendar ─────────────────────────────────────────────────

@router.get("/{brand_id}/calendar/upcoming")
async def get_calendar_events(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    days_ahead: int = 14,
):
    await get_brand(brand_id, current_user, db)
    return {"events": get_upcoming_events(days_ahead)}


# ── UGC ──────────────────────────────────────────────────────

@router.post("/{brand_id}/ugc")
async def add_ugc(
    brand_id: uuid.UUID,
    body: AddUGCRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    await get_brand(brand_id, current_user, db)
    post = await add_ugc_manual(
        brand_id, db,
        body.source_platform, body.author_username,
        body.media_url, body.caption, body.source_url,
    )
    return {"id": str(post.id), "status": post.permission_status}


@router.get("/{brand_id}/ugc")
async def get_ugc_list(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    permission_status: str | None = None,
):
    await get_brand(brand_id, current_user, db)
    posts = await list_ugc(brand_id, db, permission_status)
    return {
        "ugc_posts": [
            {
                "id": str(p.id),
                "author": p.author_username,
                "platform": p.source_platform,
                "media_url": p.media_url,
                "caption": p.caption,
                "status": p.permission_status,
                "created_at": p.created_at.isoformat(),
            }
            for p in posts
        ]
    }


@router.get("/{brand_id}/ugc/dm-template")
async def get_ugc_dm_template(
    brand_id: uuid.UUID,
    author_username: str,
    current_user: CurrentUser,
    db: DBSession,
):
    brand = await get_brand(brand_id, current_user, db)
    dm = await generate_permission_request_dm(author_username, brand.name)
    return {"dm_text": dm}


# ── Push Token Registration ──────────────────────────────────

@router.post("/{brand_id}/push-token")
async def register_push_token(
    brand_id: uuid.UUID,
    body: RegisterPushTokenRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    brand = await get_brand(brand_id, current_user, db)
    from sqlalchemy import update
    from app.models.brand import Brand
    await db.execute(
        update(Brand).where(Brand.id == brand_id).values(expo_push_token=body.expo_push_token)
    )
    await db.commit()
    return {"status": "registered", "brand_id": str(brand_id)}
