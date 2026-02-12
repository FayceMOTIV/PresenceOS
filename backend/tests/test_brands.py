"""
PresenceOS - Brands Tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, Workspace
from app.models.brand import Brand, BrandVoice


class TestCreateBrand:
    """Tests for brand creation."""

    async def test_create_brand_success(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        auth_headers: dict,
    ):
        """Test successful brand creation."""
        response = await client.post(
            f"/api/v1/brands?workspace_id={test_workspace.id}",
            json={
                "name": "New Brand",
                "slug": "new-brand",
                "brand_type": "restaurant",
                "description": "A new restaurant brand",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Brand"
        assert data["slug"] == "new-brand"
        assert data["brand_type"] == "restaurant"
        assert data["workspace_id"] == str(test_workspace.id)
        assert data["is_active"] is True

    async def test_create_brand_with_voice(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        auth_headers: dict,
    ):
        """Test brand creation with voice configuration."""
        response = await client.post(
            f"/api/v1/brands?workspace_id={test_workspace.id}",
            json={
                "name": "Brand With Voice",
                "slug": "brand-with-voice",
                "brand_type": "saas",
                "voice": {
                    "tone_formal": 70,
                    "tone_playful": 30,
                    "tone_bold": 60,
                    "words_to_avoid": ["cheap", "discount"],
                    "words_to_prefer": ["premium", "innovative"],
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["voice"] is not None
        assert data["voice"]["tone_formal"] == 70
        assert data["voice"]["tone_playful"] == 30

    async def test_create_brand_duplicate_slug(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test brand creation with duplicate slug in same workspace."""
        response = await client.post(
            f"/api/v1/brands?workspace_id={test_workspace.id}",
            json={
                "name": "Another Brand",
                "slug": test_brand.slug,  # Same slug
                "brand_type": "other",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_create_brand_unauthorized(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
    ):
        """Test brand creation without auth."""
        response = await client.post(
            f"/api/v1/brands?workspace_id={test_workspace.id}",
            json={
                "name": "Unauthorized Brand",
                "slug": "unauthorized-brand",
                "brand_type": "other",
            },
        )
        assert response.status_code == 401

    async def test_create_brand_invalid_slug(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        auth_headers: dict,
    ):
        """Test brand creation with invalid slug format."""
        response = await client.post(
            f"/api/v1/brands?workspace_id={test_workspace.id}",
            json={
                "name": "Invalid Slug Brand",
                "slug": "Invalid Slug!",  # Contains spaces and special chars
                "brand_type": "other",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetBrand:
    """Tests for getting brand details."""

    async def test_get_brand_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting brand details."""
        response = await client.get(
            f"/api/v1/brands/{test_brand.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_brand.id)
        assert data["name"] == test_brand.name
        assert data["slug"] == test_brand.slug

    async def test_get_brand_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent brand."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/brands/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_brand_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test getting brand without auth."""
        response = await client.get(f"/api/v1/brands/{test_brand.id}")
        assert response.status_code == 401


class TestUpdateBrand:
    """Tests for updating brand."""

    async def test_update_brand_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test successful brand update."""
        response = await client.patch(
            f"/api/v1/brands/{test_brand.id}",
            json={
                "name": "Updated Brand Name",
                "description": "Updated description",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Brand Name"
        assert data["description"] == "Updated description"
        # Slug should remain unchanged
        assert data["slug"] == test_brand.slug

    async def test_update_brand_partial(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test partial brand update (only some fields)."""
        original_name = test_brand.name
        response = await client.patch(
            f"/api/v1/brands/{test_brand.id}",
            json={
                "website_url": "https://example.com",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name  # Unchanged
        assert data["website_url"] == "https://example.com"

    async def test_update_brand_content_pillars(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test updating brand content pillars."""
        response = await client.patch(
            f"/api/v1/brands/{test_brand.id}",
            json={
                "content_pillars": {
                    "education": 30,
                    "entertainment": 25,
                    "engagement": 20,
                    "promotion": 15,
                    "behind_scenes": 10,
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content_pillars"]["education"] == 30


class TestBrandVoice:
    """Tests for brand voice configuration."""

    async def test_get_brand_voice(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting brand voice."""
        response = await client.get(
            f"/api/v1/brands/{test_brand.id}/voice",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "tone_formal" in data
        assert "tone_playful" in data

    async def test_update_brand_voice(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test updating brand voice."""
        response = await client.patch(
            f"/api/v1/brands/{test_brand.id}/voice",
            json={
                "tone_formal": 80,
                "tone_playful": 20,
                "words_to_avoid": ["test", "example"],
                "custom_instructions": "Always be professional",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tone_formal"] == 80
        assert data["tone_playful"] == 20
        assert data["words_to_avoid"] == ["test", "example"]
        assert data["custom_instructions"] == "Always be professional"


class TestWorkspaceBrands:
    """Tests for workspace brands listing."""

    async def test_list_workspace_brands(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test listing brands in a workspace."""
        response = await client.get(
            f"/api/v1/workspaces/{test_workspace.id}/brands",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(b["id"] == str(test_brand.id) for b in data)

    async def test_list_workspace_brands_empty(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        test_user: User,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """Test listing brands in workspace with no brands."""
        # Create a new workspace without brands
        from app.models.user import WorkspaceMember, UserRole

        new_workspace = Workspace(name="Empty Workspace", slug="empty-workspace")
        db.add(new_workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=new_workspace.id,
            user_id=test_user.id,
            role=UserRole.OWNER,
        )
        db.add(member)
        await db.commit()

        response = await client.get(
            f"/api/v1/workspaces/{new_workspace.id}/brands",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestDeleteBrand:
    """Tests for brand deletion (soft delete)."""

    async def test_delete_brand_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
        db: AsyncSession,
    ):
        """Test successful brand deletion (soft delete)."""
        response = await client.delete(
            f"/api/v1/brands/{test_brand.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"]

        # Verify brand is deactivated
        await db.refresh(test_brand)
        assert test_brand.is_active is False

    async def test_delete_brand_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent brand."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/v1/brands/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestWorkspacePermissions:
    """Tests for workspace access permissions."""

    async def test_access_brand_from_different_workspace(
        self,
        client: AsyncClient,
        test_brand: Brand,
        db: AsyncSession,
        auth_headers_factory,
    ):
        """Test that a user cannot access a brand from a workspace they're not a member of."""
        from app.core.security import get_password_hash
        from app.models.user import Workspace, WorkspaceMember, UserRole

        # Create another user who is NOT a member of test_brand's workspace
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Other User",
            is_active=True,
            is_verified=True,
        )
        db.add(other_user)

        # Create a different workspace for the other user
        other_workspace = Workspace(
            name="Other Workspace",
            slug="other-workspace",
        )
        db.add(other_workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=other_workspace.id,
            user_id=other_user.id,
            role=UserRole.OWNER,
        )
        db.add(member)
        await db.commit()
        await db.refresh(other_user)

        # Try to access the brand with other user's token
        other_headers = auth_headers_factory(other_user)
        response = await client.get(
            f"/api/v1/brands/{test_brand.id}",
            headers=other_headers,
        )
        assert response.status_code == 403
        assert "access" in response.json()["detail"].lower()

    async def test_create_brand_in_non_member_workspace(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        db: AsyncSession,
        auth_headers_factory,
    ):
        """Test that a user cannot create a brand in a workspace they're not a member of."""
        from app.core.security import get_password_hash

        # Create another user who is NOT a member of test_workspace
        other_user = User(
            email="outsider@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Outsider User",
            is_active=True,
            is_verified=True,
        )
        db.add(other_user)
        await db.commit()
        await db.refresh(other_user)

        other_headers = auth_headers_factory(other_user)
        response = await client.post(
            f"/api/v1/brands?workspace_id={test_workspace.id}",
            json={
                "name": "Unauthorized Brand",
                "slug": "unauthorized-brand",
                "brand_type": "other",
            },
            headers=other_headers,
        )
        assert response.status_code == 403

    async def test_update_brand_from_different_workspace(
        self,
        client: AsyncClient,
        test_brand: Brand,
        db: AsyncSession,
        auth_headers_factory,
    ):
        """Test that a user cannot update a brand from a workspace they're not a member of."""
        from app.core.security import get_password_hash

        # Create another user
        other_user = User(
            email="noaccess@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="No Access User",
            is_active=True,
            is_verified=True,
        )
        db.add(other_user)
        await db.commit()
        await db.refresh(other_user)

        other_headers = auth_headers_factory(other_user)
        response = await client.patch(
            f"/api/v1/brands/{test_brand.id}",
            json={"name": "Hacked Brand"},
            headers=other_headers,
        )
        assert response.status_code == 403

    async def test_delete_brand_from_different_workspace(
        self,
        client: AsyncClient,
        test_brand: Brand,
        db: AsyncSession,
        auth_headers_factory,
    ):
        """Test that a user cannot delete a brand from a workspace they're not a member of."""
        from app.core.security import get_password_hash

        # Create another user
        other_user = User(
            email="attacker@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Attacker User",
            is_active=True,
            is_verified=True,
        )
        db.add(other_user)
        await db.commit()
        await db.refresh(other_user)

        other_headers = auth_headers_factory(other_user)
        response = await client.delete(
            f"/api/v1/brands/{test_brand.id}",
            headers=other_headers,
        )
        assert response.status_code == 403

    async def test_member_roles_access(
        self,
        client: AsyncClient,
        test_workspace: Workspace,
        test_brand: Brand,
        db: AsyncSession,
        auth_headers_factory,
    ):
        """Test that workspace members with different roles can access brands."""
        from app.core.security import get_password_hash
        from app.models.user import WorkspaceMember, UserRole

        # Create a member user (not owner/admin)
        member_user = User(
            email="member@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Member User",
            is_active=True,
            is_verified=True,
        )
        db.add(member_user)
        await db.flush()

        # Add as member (lowest role)
        membership = WorkspaceMember(
            workspace_id=test_workspace.id,
            user_id=member_user.id,
            role=UserRole.MEMBER,
        )
        db.add(membership)
        await db.commit()
        await db.refresh(member_user)

        # Member should be able to read brands
        member_headers = auth_headers_factory(member_user)
        response = await client.get(
            f"/api/v1/brands/{test_brand.id}",
            headers=member_headers,
        )
        assert response.status_code == 200

        # Member should be able to update brands
        response = await client.patch(
            f"/api/v1/brands/{test_brand.id}",
            json={"description": "Updated by member"},
            headers=member_headers,
        )
        assert response.status_code == 200
