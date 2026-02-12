"""
PresenceOS - Ideas Tests
"""
import pytest
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.brand import Brand
from app.models.content import ContentIdea, IdeaSource, IdeaStatus


@pytest.fixture
async def test_idea(db: AsyncSession, test_brand: Brand) -> ContentIdea:
    """Create a test idea."""
    idea = ContentIdea(
        brand_id=test_brand.id,
        title="Test Idea",
        description="A test idea description",
        source=IdeaSource.USER_CREATED,
        status=IdeaStatus.NEW,
        content_pillar="education",
        target_platforms=["instagram_post", "linkedin"],
    )
    db.add(idea)
    await db.commit()
    await db.refresh(idea)
    return idea


@pytest.fixture
async def test_approved_idea(db: AsyncSession, test_brand: Brand) -> ContentIdea:
    """Create a test approved idea."""
    idea = ContentIdea(
        brand_id=test_brand.id,
        title="Approved Idea",
        description="An approved idea",
        source=IdeaSource.AI_GENERATED,
        status=IdeaStatus.APPROVED,
        content_pillar="engagement",
        target_platforms=["instagram_post"],
    )
    db.add(idea)
    await db.commit()
    await db.refresh(idea)
    return idea


# =============================================================================
# List Ideas Tests
# =============================================================================

class TestListIdeas:
    """Tests for GET /api/v1/ideas/brands/{brand_id}"""

    async def test_list_ideas_empty(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test listing ideas when none exist."""
        response = await client.get(
            f"/api/v1/ideas/brands/{test_brand.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_ideas_with_ideas(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test listing ideas with existing ideas."""
        response = await client.get(
            f"/api/v1/ideas/brands/{test_brand.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(i["id"] == str(test_idea.id) for i in data)

    async def test_list_ideas_filter_by_status(
        self,
        client: AsyncClient,
        test_brand: Brand,
        test_idea: ContentIdea,
        test_approved_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test filtering ideas by status."""
        response = await client.get(
            f"/api/v1/ideas/brands/{test_brand.id}",
            headers=auth_headers,
            params={"status_filter": "new"},
        )
        assert response.status_code == 200
        data = response.json()
        for idea in data:
            assert idea["status"] == "new"

    async def test_list_ideas_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test listing ideas without authentication."""
        response = await client.get(
            f"/api/v1/ideas/brands/{test_brand.id}",
        )
        assert response.status_code == 401


# =============================================================================
# Create Idea Tests
# =============================================================================

class TestCreateIdea:
    """Tests for POST /api/v1/ideas/brands/{brand_id}"""

    async def test_create_idea_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test creating an idea."""
        response = await client.post(
            f"/api/v1/ideas/brands/{test_brand.id}",
            headers=auth_headers,
            json={
                "title": "New Test Idea",
                "description": "A brand new idea",
                "source": "user_created",
                "content_pillar": "promotion",
                "target_platforms": ["instagram_post"],
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == "New Test Idea"
        assert data["status"] == "new"

    async def test_create_idea_minimal(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test creating an idea with minimal data."""
        response = await client.post(
            f"/api/v1/ideas/brands/{test_brand.id}",
            headers=auth_headers,
            json={
                "title": "Minimal Idea",
            },
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == "Minimal Idea"

    async def test_create_idea_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test creating an idea without authentication."""
        response = await client.post(
            f"/api/v1/ideas/brands/{test_brand.id}",
            json={"title": "Should Fail"},
        )
        assert response.status_code == 401


# =============================================================================
# Get Idea Tests
# =============================================================================

class TestGetIdea:
    """Tests for GET /api/v1/ideas/{idea_id}"""

    async def test_get_idea_success(
        self,
        client: AsyncClient,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test getting an idea by ID."""
        response = await client.get(
            f"/api/v1/ideas/{test_idea.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_idea.id)
        assert data["title"] == test_idea.title

    async def test_get_idea_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a non-existent idea."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/v1/ideas/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# =============================================================================
# Update Idea Tests
# =============================================================================

class TestUpdateIdea:
    """Tests for PATCH /api/v1/ideas/{idea_id}"""

    async def test_update_idea_success(
        self,
        client: AsyncClient,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test updating an idea."""
        response = await client.patch(
            f"/api/v1/ideas/{test_idea.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "description": "Updated description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"

    async def test_update_idea_partial(
        self,
        client: AsyncClient,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test partial update of an idea."""
        response = await client.patch(
            f"/api/v1/ideas/{test_idea.id}",
            headers=auth_headers,
            json={"content_pillar": "entertainment"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content_pillar"] == "entertainment"
        # Original title should be preserved
        assert data["title"] == test_idea.title


# =============================================================================
# Approve/Reject Idea Tests
# =============================================================================

class TestIdeaApproval:
    """Tests for POST /api/v1/ideas/{idea_id}/approve and reject"""

    async def test_approve_idea_success(
        self,
        client: AsyncClient,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test approving an idea."""
        response = await client.post(
            f"/api/v1/ideas/{test_idea.id}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    async def test_approve_already_approved(
        self,
        client: AsyncClient,
        test_approved_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test approving an already approved idea."""
        response = await client.post(
            f"/api/v1/ideas/{test_approved_idea.id}/approve",
            headers=auth_headers,
        )
        # Should either succeed idempotently or return an error
        assert response.status_code in [200, 400]

    async def test_reject_idea_success(
        self,
        client: AsyncClient,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test rejecting an idea."""
        response = await client.post(
            f"/api/v1/ideas/{test_idea.id}/reject",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    async def test_reject_approved_idea(
        self,
        client: AsyncClient,
        test_approved_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test rejecting an approved idea."""
        response = await client.post(
            f"/api/v1/ideas/{test_approved_idea.id}/reject",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    async def test_approve_idea_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test approving a non-existent idea."""
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/ideas/{fake_id}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 404


# =============================================================================
# Delete Idea Tests
# =============================================================================

class TestDeleteIdea:
    """Tests for DELETE /api/v1/ideas/{idea_id}"""

    async def test_delete_idea_success(
        self,
        client: AsyncClient,
        test_idea: ContentIdea,
        auth_headers: dict,
    ):
        """Test deleting (archiving) an idea."""
        response = await client.delete(
            f"/api/v1/ideas/{test_idea.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Idea archived"

        # Verify it's archived (soft delete - still accessible)
        get_response = await client.get(
            f"/api/v1/ideas/{test_idea.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "archived"

    async def test_delete_idea_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting a non-existent idea."""
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/v1/ideas/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
