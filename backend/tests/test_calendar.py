"""
PresenceOS - Calendar & Scheduling Tests
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.brand import Brand
from app.models.content import ContentDraft, DraftStatus, Platform
from app.models.publishing import ScheduledPost, PostStatus, SocialConnector, ConnectorStatus


@pytest.fixture
async def test_connector(db: AsyncSession, test_brand: Brand) -> SocialConnector:
    """Create a test social connector."""
    connector = SocialConnector(
        brand_id=test_brand.id,
        platform="instagram",
        account_id="123456789",
        account_name="testaccount",
        account_username="testaccount",
        status=ConnectorStatus.CONNECTED,
        access_token_encrypted="test_token_encrypted",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    return connector


@pytest.fixture
async def test_draft(db: AsyncSession, test_brand: Brand) -> ContentDraft:
    """Create a test draft."""
    draft = ContentDraft(
        brand_id=test_brand.id,
        platform=Platform.INSTAGRAM_POST,
        caption="Test caption for the post",
        hashtags=["test", "presenceos"],
        status=DraftStatus.DRAFT,
    )
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return draft


@pytest.fixture
async def test_scheduled_post(
    db: AsyncSession,
    test_brand: Brand,
    test_draft: ContentDraft,
    test_connector: SocialConnector,
) -> ScheduledPost:
    """Create a test scheduled post."""
    scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
    post = ScheduledPost(
        brand_id=test_brand.id,
        draft_id=test_draft.id,
        connector_id=test_connector.id,
        scheduled_at=scheduled_at,
        timezone="Europe/Paris",
        status=PostStatus.SCHEDULED,
        content_snapshot={
            "caption": test_draft.caption,
            "hashtags": test_draft.hashtags,
            "media_urls": [],
        },
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


# =============================================================================
# GET Calendar Tests
# =============================================================================

class TestGetCalendar:
    """Tests for GET /api/v1/posts/brands/{brand_id}/calendar"""

    async def test_get_calendar_empty(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting calendar with no posts."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}/calendar",
            headers=auth_headers,
            params={"month": "2026-02"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert data["brand_id"] == str(test_brand.id)

    async def test_get_calendar_with_posts(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_scheduled_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test getting calendar with existing posts."""
        month = test_scheduled_post.scheduled_at.strftime("%Y-%m")
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}/calendar",
            headers=auth_headers,
            params={"month": month},
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        # Find the day with our post
        post_date = test_scheduled_post.scheduled_at.strftime("%Y-%m-%d")
        day_with_post = next(
            (d for d in data["days"] if d["date"].startswith(post_date)),
            None
        )
        assert day_with_post is not None
        assert len(day_with_post["scheduled_posts"]) >= 1

    async def test_get_calendar_invalid_month(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting calendar with invalid month format."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}/calendar",
            headers=auth_headers,
            params={"month": "invalid"},
        )
        assert response.status_code == 422  # Validation error

    async def test_get_calendar_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test getting calendar without authentication."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}/calendar",
            params={"month": "2026-02"},
        )
        assert response.status_code == 401


# =============================================================================
# Bulk Schedule Tests
# =============================================================================

class TestBulkSchedule:
    """Tests for PATCH /api/v1/posts/bulk-schedule"""

    async def test_bulk_schedule_success(
        self,
        client: AsyncClient,
        test_scheduled_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test bulk scheduling a post to a new date."""
        new_date = datetime.now(timezone.utc) + timedelta(days=5)
        response = await client.patch(
            "/api/v1/posts/bulk-schedule",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "scheduled_post_id": str(test_scheduled_post.id),
                        "new_scheduled_at": new_date.isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["successful"] == 1
        assert data["failed"] == 0

    async def test_bulk_schedule_past_date(
        self,
        client: AsyncClient,
        test_scheduled_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test bulk scheduling to a past date fails."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        response = await client.patch(
            "/api/v1/posts/bulk-schedule",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "scheduled_post_id": str(test_scheduled_post.id),
                        "new_scheduled_at": past_date.isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] >= 1

    async def test_bulk_schedule_nonexistent_post(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test bulk scheduling a non-existent post."""
        new_date = datetime.now(timezone.utc) + timedelta(days=5)
        fake_id = str(uuid4())
        response = await client.patch(
            "/api/v1/posts/bulk-schedule",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "scheduled_post_id": fake_id,
                        "new_scheduled_at": new_date.isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] >= 1

    async def test_bulk_schedule_unauthorized(
        self,
        client: AsyncClient,
        test_scheduled_post: ScheduledPost,
    ):
        """Test bulk scheduling without authentication."""
        new_date = datetime.now(timezone.utc) + timedelta(days=5)
        response = await client.patch(
            "/api/v1/posts/bulk-schedule",
            json={
                "items": [
                    {
                        "scheduled_post_id": str(test_scheduled_post.id),
                        "new_scheduled_at": new_date.isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 401


# =============================================================================
# Quick Create Tests
# =============================================================================

class TestQuickCreate:
    """Tests for POST /api/v1/posts/brands/{brand_id}/quick"""

    async def test_quick_create_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_connector: SocialConnector,
        auth_headers: dict,
    ):
        """Test quick creating a post."""
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}/quick",
            headers=auth_headers,
            json={
                "title": "Quick Post Test",
                "caption": "This is a quick test post",
                "platform": "instagram_post",
                "media_type": "image",
                "scheduled_at": scheduled_at.isoformat(),
                "connector_id": str(test_connector.id),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["caption"] == "This is a quick test post"
        assert data["status"] == "scheduled"

    async def test_quick_create_past_date(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_connector: SocialConnector,
        auth_headers: dict,
    ):
        """Test quick creating with past date fails."""
        past_date = datetime.now(timezone.utc) - timedelta(hours=1)
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}/quick",
            headers=auth_headers,
            json={
                "title": "Past Post",
                "caption": "This should fail",
                "platform": "instagram_post",
                "media_type": "image",
                "scheduled_at": past_date.isoformat(),
                "connector_id": str(test_connector.id),
            },
        )
        assert response.status_code == 400

    async def test_quick_create_invalid_connector(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test quick creating with invalid connector fails."""
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}/quick",
            headers=auth_headers,
            json={
                "title": "Invalid Connector",
                "caption": "This should fail",
                "platform": "instagram_post",
                "media_type": "image",
                "scheduled_at": scheduled_at.isoformat(),
                "connector_id": fake_id,
            },
        )
        assert response.status_code == 404

    async def test_quick_create_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_connector: SocialConnector,
    ):
        """Test quick creating without authentication."""
        scheduled_at = datetime.now(timezone.utc) + timedelta(days=1)
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}/quick",
            json={
                "title": "No Auth",
                "caption": "Should fail",
                "platform": "instagram_post",
                "media_type": "image",
                "scheduled_at": scheduled_at.isoformat(),
                "connector_id": str(test_connector.id),
            },
        )
        assert response.status_code == 401
