"""
Tests for IDOR protection — verify_brand_access (Sprint B1 Security).

Unit tests for the verify_brand_access function + integration tests
that all brand-scoped endpoints reject cross-tenant access.
"""
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.deps import verify_brand_access
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, Workspace, WorkspaceMember, UserRole
from app.models.brand import Brand, BrandVoice, BrandType


# ── Helpers ──


def _mock_user(user_id: uuid.UUID | None = None):
    """Create a mock User object."""
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = "test@presenceos.dev"
    return user


def _mock_brand(brand_id: uuid.UUID, workspace_id: uuid.UUID):
    """Create a mock Brand object."""
    brand = MagicMock()
    brand.id = brand_id
    brand.workspace_id = workspace_id
    return brand


def _mock_db(brand=None, membership=None):
    """Create a mock AsyncSession that returns brand and membership results."""
    db = AsyncMock()
    call_count = 0

    async def mock_execute(stmt):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            # First call: Brand lookup
            result.scalar_one_or_none.return_value = brand
        else:
            # Second call: Workspace membership check
            result.scalar_one_or_none.return_value = membership
        call_count += 1
        return result

    db.execute = mock_execute
    return db


# ── Tests ──


@pytest.mark.asyncio
async def test_verify_brand_access_invalid_uuid():
    """Should return 400 for a non-UUID brand_id."""
    user = _mock_user()
    db = _mock_db()

    with pytest.raises(HTTPException) as exc_info:
        await verify_brand_access("not-a-uuid", user, db)

    assert exc_info.value.status_code == 400
    assert "Invalid brand_id format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_brand_access_brand_not_found():
    """Should return 404 when brand doesn't exist in DB."""
    user = _mock_user()
    db = _mock_db(brand=None)

    brand_id = str(uuid.uuid4())
    with pytest.raises(HTTPException) as exc_info:
        await verify_brand_access(brand_id, user, db)

    assert exc_info.value.status_code == 404
    assert "Brand not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_brand_access_no_membership():
    """Should return 403 when user is not a member of the brand's workspace (IDOR)."""
    brand_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    user = _mock_user()
    brand = _mock_brand(brand_id, workspace_id)
    db = _mock_db(brand=brand, membership=None)

    with pytest.raises(HTTPException) as exc_info:
        await verify_brand_access(str(brand_id), user, db)

    assert exc_info.value.status_code == 403
    assert "don't have access" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_brand_access_valid():
    """Should return the Brand when user has workspace membership."""
    brand_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    user = _mock_user()
    brand = _mock_brand(brand_id, workspace_id)
    membership = MagicMock()  # truthy = membership exists
    db = _mock_db(brand=brand, membership=membership)

    result = await verify_brand_access(str(brand_id), user, db)
    assert result is brand


@pytest.mark.asyncio
async def test_verify_brand_access_different_user():
    """Two users with different IDs — only the one with membership passes."""
    brand_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    brand = _mock_brand(brand_id, workspace_id)

    # User with no membership
    attacker = _mock_user(uuid.uuid4())
    db_no_access = _mock_db(brand=brand, membership=None)
    with pytest.raises(HTTPException) as exc_info:
        await verify_brand_access(str(brand_id), attacker, db_no_access)
    assert exc_info.value.status_code == 403

    # User with membership
    owner = _mock_user(uuid.uuid4())
    membership = MagicMock()
    db_with_access = _mock_db(brand=brand, membership=membership)
    result = await verify_brand_access(str(brand_id), owner, db_with_access)
    assert result is brand


# ── Integration Test Fixtures ───────────────────────────────


@pytest.fixture
async def attacker_user(db: AsyncSession) -> User:
    """A second user with NO access to test_brand."""
    user = User(
        email="attacker@example.com",
        hashed_password=get_password_hash("attackerpass123"),
        full_name="Attacker User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def attacker_workspace(db: AsyncSession, attacker_user: User) -> Workspace:
    """Attacker's own workspace."""
    ws = Workspace(name="Attacker WS", slug="attacker-ws")
    db.add(ws)
    await db.flush()
    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=attacker_user.id,
        role=UserRole.OWNER,
    )
    db.add(member)
    await db.commit()
    await db.refresh(ws)
    return ws


@pytest.fixture
async def attacker_brand(db: AsyncSession, attacker_workspace: Workspace) -> Brand:
    """Attacker's own brand."""
    brand = Brand(
        workspace_id=attacker_workspace.id,
        name="Attacker Brand",
        slug="attacker-brand",
        brand_type=BrandType.RESTAURANT,
        description="Attacker restaurant",
    )
    db.add(brand)
    await db.flush()
    voice = BrandVoice(
        brand_id=brand.id,
        tone_formal=50, tone_playful=50,
        tone_bold=50, tone_emotional=50,
    )
    db.add(voice)
    await db.commit()
    await db.refresh(brand)
    return brand


@pytest.fixture
def attacker_headers(attacker_user: User) -> dict:
    """JWT headers for the attacker user."""
    token = create_access_token(
        subject=str(attacker_user.id),
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


FAKE_UUID = str(uuid.uuid4())


# ── V2 Ilyas IDOR Integration Tests ────────────────────────


class TestIlyasIDOR:
    """Attacker tries to access victim's brand via Ilyas endpoints."""

    @pytest.mark.asyncio
    async def test_chat_idor_returns_403(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.post(
            f"/api/v2/ilyas/{test_brand.id}/chat",
            json={"message": "Hello"},
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_list_sessions_idor_returns_403(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v2/ilyas/{test_brand.id}/sessions",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_get_messages_idor_returns_403(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v2/ilyas/{test_brand.id}/sessions/{FAKE_UUID}/messages",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_session_idor_returns_403(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.delete(
            f"/api/v2/ilyas/{test_brand.id}/sessions/{FAKE_UUID}",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_context_idor_returns_403(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v2/ilyas/{test_brand.id}/context",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── V1 Analytics IDOR Integration Tests ─────────────────────


class TestAnalyticsIDOR:

    @pytest.mark.asyncio
    async def test_overview_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/analytics/overview/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_kpis_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/analytics/kpis/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── V1 Competitor IDOR Integration Tests ────────────────────


class TestCompetitorIDOR:

    @pytest.mark.asyncio
    async def test_list_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/competitor/list/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_benchmark_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/competitor/benchmark/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── V1 GBP IDOR Integration Tests ──────────────────────────


class TestGBPIDOR:

    @pytest.mark.asyncio
    async def test_config_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/gbp/config/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_publish_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.post(
            "/api/v1/gbp/publish",
            json={"brand_id": str(test_brand.id), "caption": "test"},
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── V1 Hyperlocal IDOR Integration Tests ───────────────────


class TestHyperlocalIDOR:

    @pytest.mark.asyncio
    async def test_context_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/hyperlocal/context/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── V1 Trends IDOR Integration Tests ───────────────────────


class TestTrendsIDOR:

    @pytest.mark.asyncio
    async def test_trends_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/trends/trends/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── V1 Reputation IDOR Integration Tests ───────────────────


class TestReputationIDOR:

    @pytest.mark.asyncio
    async def test_reviews_idor(
        self, client: AsyncClient, attacker_headers: dict,
        test_brand: Brand, attacker_brand: Brand,
    ):
        res = await client.get(
            f"/api/v1/reputation/reviews/{test_brand.id}",
            headers=attacker_headers,
        )
        assert res.status_code == 403


# ── Unauthenticated Access Tests ────────────────────────────


class TestUnauthenticatedAccess:
    """All brand-scoped endpoints must reject unauthenticated requests."""

    @pytest.mark.asyncio
    async def test_ilyas_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.post(
            f"/api/v2/ilyas/{test_brand.id}/chat",
            json={"message": "Hello"},
        )
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_analytics_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.get(f"/api/v1/analytics/overview/{test_brand.id}")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_competitor_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.get(f"/api/v1/competitor/list/{test_brand.id}")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_gbp_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.get(f"/api/v1/gbp/config/{test_brand.id}")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_hyperlocal_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.get(f"/api/v1/hyperlocal/context/{test_brand.id}")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_trends_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.get(f"/api/v1/trends/trends/{test_brand.id}")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_reputation_no_auth(self, client: AsyncClient, test_brand: Brand):
        res = await client.get(f"/api/v1/reputation/reviews/{test_brand.id}")
        assert res.status_code in (401, 403)


# ── Nonexistent Brand Tests ─────────────────────────────────


class TestNonexistentBrand:
    """Accessing a brand that doesn't exist should return 404."""

    @pytest.mark.asyncio
    async def test_ilyas_nonexistent(self, client: AsyncClient, auth_headers: dict):
        fake_id = str(uuid.uuid4())
        res = await client.post(
            f"/api/v2/ilyas/{fake_id}/chat",
            json={"message": "Hello"},
            headers=auth_headers,
        )
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_analytics_nonexistent(self, client: AsyncClient, auth_headers: dict):
        fake_id = str(uuid.uuid4())
        res = await client.get(
            f"/api/v1/analytics/overview/{fake_id}",
            headers=auth_headers,
        )
        assert res.status_code == 404
