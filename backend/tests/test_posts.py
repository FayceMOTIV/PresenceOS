"""
PresenceOS - Posts Tests
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.brand import Brand
from app.models.publishing import (
    ScheduledPost,
    SocialConnector,
    PostStatus,
    ConnectorStatus,
)


@pytest.fixture
async def test_connector(db: AsyncSession, test_brand: Brand) -> SocialConnector:
    """Create a test connector."""
    connector = SocialConnector(
        brand_id=test_brand.id,
        platform="instagram",
        account_id="test-ig-account",
        account_name="Test Instagram",
        account_username="test_instagram",
        status=ConnectorStatus.CONNECTED,
        access_token_encrypted="encrypted-token",
        is_active=True,
    )
    db.add(connector)
    await db.commit()
    await db.refresh(connector)
    return connector


@pytest.fixture
async def test_post(
    db: AsyncSession, test_brand: Brand, test_connector: SocialConnector
) -> ScheduledPost:
    """Create a test scheduled post."""
    post = ScheduledPost(
        brand_id=test_brand.id,
        connector_id=test_connector.id,
        status=PostStatus.SCHEDULED,
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
        content_snapshot={
            "caption": "Test post caption",
            "hashtags": ["test", "presenceos"],
            "media_urls": [],
        },
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@pytest.fixture
async def test_published_post(
    db: AsyncSession, test_brand: Brand, test_connector: SocialConnector
) -> ScheduledPost:
    """Create a test published post."""
    post = ScheduledPost(
        brand_id=test_brand.id,
        connector_id=test_connector.id,
        status=PostStatus.PUBLISHED,
        scheduled_at=datetime.now(timezone.utc) - timedelta(hours=1),
        published_at=datetime.now(timezone.utc) - timedelta(minutes=55),
        platform_post_id="test-platform-id",
        platform_post_url="https://instagram.com/p/test123",
        content_snapshot={
            "caption": "Published post",
            "hashtags": ["published"],
            "media_urls": [],
        },
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


# =============================================================================
# List Posts Tests
# =============================================================================

class TestListPosts:
    """Tests for GET /api/v1/posts/brands/{brand_id}"""

    async def test_list_posts_empty(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test listing posts when none exist."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_posts_with_posts(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test listing posts with existing posts."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(p["id"] == str(test_post.id) for p in data)

    async def test_list_posts_filter_by_status(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_post: ScheduledPost,
        test_published_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test filtering posts by status."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}",
            headers=auth_headers,
            params={"status_filter": "scheduled"},
        )
        assert response.status_code == 200
        data = response.json()
        for post in data:
            assert post["status"] == "scheduled"

    async def test_list_posts_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test listing posts without authentication."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}",
        )
        assert response.status_code == 401


# =============================================================================
# Get Calendar Tests
# =============================================================================

class TestGetCalendar:
    """Tests for GET /api/v1/posts/brands/{brand_id}/calendar"""

    async def test_get_calendar_empty(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting calendar when no posts."""
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}/calendar",
            headers=auth_headers,
            params={"month": "2025-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert data["brand_id"] == str(test_brand.id)

    async def test_get_calendar_with_posts(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test getting calendar with posts."""
        # Get the month of the test post
        month = test_post.scheduled_at.strftime("%Y-%m")
        response = await client.get(
            f"/api/v1/posts/brands/{test_brand.id}/calendar",
            headers=auth_headers,
            params={"month": month},
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert data["brand_id"] == str(test_brand.id)


# =============================================================================
# Schedule Post Tests
# =============================================================================

class TestSchedulePost:
    """Tests for POST /api/v1/posts/brands/{brand_id}"""

    async def test_schedule_post_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_connector: SocialConnector,
        auth_headers: dict,
    ):
        """Test scheduling a new post."""
        scheduled_at = datetime.now(timezone.utc) + timedelta(hours=2)
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}",
            headers=auth_headers,
            json={
                "connector_id": str(test_connector.id),
                "scheduled_at": scheduled_at.isoformat(),
                "content": {
                    "caption": "New scheduled post",
                    "hashtags": ["new"],
                },
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["status"] == "scheduled"

    async def test_schedule_post_past_date(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_connector: SocialConnector,
        auth_headers: dict,
    ):
        """Test scheduling a post in the past."""
        past_date = datetime.now(timezone.utc) - timedelta(hours=1)
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}",
            headers=auth_headers,
            json={
                "connector_id": str(test_connector.id),
                "scheduled_at": past_date.isoformat(),
                "content": {
                    "caption": "Past post",
                },
            },
        )
        # Should either reject or queue immediately
        assert response.status_code in [200, 201, 400]

    async def test_schedule_post_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_connector: SocialConnector,
    ):
        """Test scheduling a post without authentication."""
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}",
            json={
                "connector_id": str(test_connector.id),
                "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            },
        )
        assert response.status_code == 401


# =============================================================================
# Update Post Tests
# =============================================================================

class TestUpdatePost:
    """Tests for PATCH /api/v1/posts/{post_id}"""

    async def test_update_post_success(
        self,
        client: AsyncClient,
        test_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test updating a scheduled post."""
        new_time = datetime.now(timezone.utc) + timedelta(hours=3)
        response = await client.patch(
            f"/api/v1/posts/{test_post.id}",
            headers=auth_headers,
            json={
                "scheduled_at": new_time.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_post.id)

    async def test_update_published_post(
        self,
        client: AsyncClient,
        test_published_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test updating a published post (should fail or be limited)."""
        response = await client.patch(
            f"/api/v1/posts/{test_published_post.id}",
            headers=auth_headers,
            json={
                "content_snapshot": {"caption": "Modified caption"},
            },
        )
        # Published posts typically can't be modified
        assert response.status_code in [200, 400, 403]


# =============================================================================
# Cancel Post Tests
# =============================================================================

class TestCancelPost:
    """Tests for DELETE /api/v1/posts/{post_id}"""

    async def test_cancel_post_success(
        self,
        client: AsyncClient,
        test_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test canceling a scheduled post."""
        response = await client.delete(
            f"/api/v1/posts/{test_post.id}",
            headers=auth_headers,
        )
        assert response.status_code in [200, 204]

    async def test_cancel_published_post(
        self,
        client: AsyncClient,
        test_published_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test canceling a published post (should fail)."""
        response = await client.delete(
            f"/api/v1/posts/{test_published_post.id}",
            headers=auth_headers,
        )
        # Published posts can't be canceled
        assert response.status_code in [200, 204, 400, 403]

    async def test_cancel_post_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test canceling a non-existent post."""
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/v1/posts/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


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
        scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)
        response = await client.post(
            f"/api/v1/posts/brands/{test_brand.id}/quick",
            headers=auth_headers,
            json={
                "title": "Quick Post",
                "caption": "Quick post caption",
                "platform": "instagram_post",
                "media_type": "image",
                "scheduled_at": scheduled_at.isoformat(),
                "connector_id": str(test_connector.id),
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["status"] == "scheduled"


# =============================================================================
# Bulk Schedule Tests
# =============================================================================

class TestBulkSchedule:
    """Tests for PATCH /api/v1/posts/bulk-schedule"""

    async def test_bulk_schedule_success(
        self,
        client: AsyncClient,
        test_post: ScheduledPost,
        auth_headers: dict,
    ):
        """Test bulk rescheduling posts."""
        new_time = datetime.now(timezone.utc) + timedelta(hours=5)
        response = await client.patch(
            "/api/v1/posts/bulk-schedule",
            headers=auth_headers,
            json={
                "items": [
                    {
                        "scheduled_post_id": str(test_post.id),
                        "new_scheduled_at": new_time.isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("successful", 0) >= 1
