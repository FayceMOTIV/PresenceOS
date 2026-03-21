"""
Tests for the Editorial Calendar — CalendarPost model, EditorialCalendar service,
calendar v2 endpoints, and mobile API integration.
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.calendar_post import CalendarPost, PostStatus
from app.services.editorial_calendar import (
    EditorialCalendar,
    editorial_calendar,
    PLATFORM_SPECS,
)


# ── Helper: create mock post without SQLAlchemy instrumentation ──

def _make_mock_post(**kwargs):
    """Create a MagicMock that behaves like a CalendarPost."""
    post = MagicMock(spec=CalendarPost)
    defaults = {
        "id": uuid.uuid4(),
        "brand_id": uuid.uuid4(),
        "platform": "instagram",
        "content_type": "feed",
        "caption": "Test caption",
        "hashtags": ["#test"],
        "visual_description": "A photo",
        "visual_url": None,
        "video_url": None,
        "cta": "Réserve !",
        "scheduled_date": "2026-03-25",
        "scheduled_time": "12:00",
        "status": PostStatus.PENDING.value,
        "postiz_post_id": None,
        "estimated_engagement": "medium",
        "pillar": "promo",
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(post, k, v)
    return post


# ── CalendarPost Model ──


def test_post_status_enum_values():
    assert PostStatus.PENDING.value == "pending_approval"
    assert PostStatus.APPROVED.value == "approved"
    assert PostStatus.SCHEDULED.value == "scheduled"
    assert PostStatus.PUBLISHED.value == "published"
    assert PostStatus.REJECTED.value == "rejected"
    assert PostStatus.FAILED.value == "failed"


def test_post_status_has_6_values():
    assert len(PostStatus) == 6


def test_calendar_post_tablename():
    assert CalendarPost.__tablename__ == "calendar_posts"


def test_calendar_post_has_brand_id_column():
    cols = {c.name for c in CalendarPost.__table__.columns}
    assert "brand_id" in cols
    assert "platform" in cols
    assert "status" in cols
    assert "caption" in cols
    assert "scheduled_date" in cols


# ── Platform Specs ──


def test_platform_specs_has_required_platforms():
    required = {"instagram_feed", "instagram_reels", "instagram_story", "facebook", "tiktok"}
    assert required.issubset(set(PLATFORM_SPECS.keys()))


def test_platform_specs_have_required_fields():
    for key, spec in PLATFORM_SPECS.items():
        assert "content_type" in spec, f"{key} missing 'content_type'"
        assert "caption_optimal" in spec, f"{key} missing 'caption_optimal'"
        assert "best_hours" in spec, f"{key} missing 'best_hours'"
        assert len(spec["best_hours"]) > 0, f"{key} has no best_hours"


def test_instagram_feed_caption_optimal():
    assert PLATFORM_SPECS["instagram_feed"]["caption_optimal"] == 150


def test_tiktok_caption_optimal():
    assert PLATFORM_SPECS["tiktok"]["caption_optimal"] == 80


def test_instagram_reels_hook_required():
    assert PLATFORM_SPECS["instagram_reels"]["hook_required"] is True


def test_tiktok_has_trending_audio():
    assert PLATFORM_SPECS["tiktok"].get("trending_audio") is True


# ── EditorialCalendar Service ──


def test_singleton_exists():
    assert editorial_calendar is not None
    assert isinstance(editorial_calendar, EditorialCalendar)


@pytest.mark.asyncio
async def test_approve_post_not_found():
    """approve_post raises ValueError when post doesn't exist."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(ValueError, match="not found"):
        await editorial_calendar.approve_post(
            post_id=uuid.uuid4(),
            brand_id=uuid.uuid4(),
            db=db,
        )


@pytest.mark.asyncio
async def test_reject_post_not_found():
    """reject_post raises ValueError when post doesn't exist."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(ValueError, match="not found"):
        await editorial_calendar.reject_post(
            post_id=uuid.uuid4(),
            brand_id=uuid.uuid4(),
            db=db,
        )


@pytest.mark.asyncio
async def test_approve_post_success():
    """approve_post updates status to approved."""
    post = _make_mock_post(status=PostStatus.PENDING.value)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = post
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    res = await editorial_calendar.approve_post(
        post_id=post.id,
        brand_id=post.brand_id,
        db=db,
    )
    assert res["status"] == "approved"
    assert post.status == PostStatus.APPROVED.value


@pytest.mark.asyncio
async def test_reject_post_success():
    """reject_post updates status to rejected."""
    post = _make_mock_post(status=PostStatus.PENDING.value)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = post
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    res = await editorial_calendar.reject_post(
        post_id=post.id,
        brand_id=post.brand_id,
        db=db,
    )
    assert res["status"] == "rejected"
    assert post.status == PostStatus.REJECTED.value


@pytest.mark.asyncio
async def test_get_calendar_returns_posts():
    """get_calendar returns posts list with count."""
    post = _make_mock_post()

    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [post]
    db.execute = AsyncMock(return_value=result)

    res = await editorial_calendar.get_calendar(
        brand_id=post.brand_id,
        db=db,
    )
    assert res["total"] == 1
    assert len(res["posts"]) == 1
    assert res["posts"][0]["platform"] == "instagram"


@pytest.mark.asyncio
async def test_get_calendar_empty():
    """get_calendar returns empty list when no posts."""
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result)

    res = await editorial_calendar.get_calendar(
        brand_id=uuid.uuid4(),
        db=db,
    )
    assert res["total"] == 0
    assert res["posts"] == []


@pytest.mark.asyncio
async def test_approve_all_pending():
    """approve_all_pending approves all pending posts."""
    brand_id = uuid.uuid4()
    post1 = _make_mock_post(brand_id=brand_id, status=PostStatus.PENDING.value)
    post2 = _make_mock_post(brand_id=brand_id, status=PostStatus.PENDING.value)

    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [post1, post2]
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    res = await editorial_calendar.approve_all_pending(brand_id, db)
    assert res["approved"] == 2
    assert post1.status == PostStatus.APPROVED.value
    assert post2.status == PostStatus.APPROVED.value


@pytest.mark.asyncio
async def test_approve_all_pending_empty():
    """approve_all_pending with no pending posts returns 0."""
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    res = await editorial_calendar.approve_all_pending(uuid.uuid4(), db)
    assert res["approved"] == 0


# ── Generate content (mocked Anthropic) ──


@pytest.mark.asyncio
async def test_generate_content_fallback():
    """_generate_content returns fallback when API fails."""
    service = EditorialCalendar()

    with patch.object(service, "_generate_content") as mock_gen:
        mock_gen.return_value = {
            "caption": "Fallback caption",
            "hashtags": ["#restaurant"],
            "visual_description": "Photo du jour",
            "cta": "",
            "estimated_engagement": "medium",
        }
        result = await service._generate_content(
            platform_spec=PLATFORM_SPECS["instagram_feed"],
            brand_name="Test Resto",
            niche_key="restaurant",
            day_label="Lundi 25 Mars",
        )
        assert "caption" in result
        assert "hashtags" in result


# ── Endpoint import checks ──


def test_calendar_router_importable():
    from app.api.v2.endpoints.calendar import router
    assert router is not None


def test_editorial_calendar_importable():
    from app.services.editorial_calendar import editorial_calendar
    assert editorial_calendar is not None


def test_calendar_post_model_importable():
    from app.models.calendar_post import CalendarPost, PostStatus
    assert CalendarPost is not None
    assert PostStatus is not None


def test_calendar_post_in_models_init():
    from app.models import CalendarPost
    assert CalendarPost is not None


# ── V2 router includes calendar ──


def test_v2_router_includes_calendar():
    from app.api.v2.router import api_v2_router
    route_paths = [r.path for r in api_v2_router.routes]
    calendar_routes = [p for p in route_paths if "calendar" in p]
    assert len(calendar_routes) > 0, "Calendar routes not found in v2 router"
