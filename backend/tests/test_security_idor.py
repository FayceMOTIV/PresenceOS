"""
Tests for IDOR protection — verify_brand_access (Section B Security).

Tests that v2 endpoints reject requests when the user doesn't own the brand.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.api.v2.deps import verify_brand_access


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
