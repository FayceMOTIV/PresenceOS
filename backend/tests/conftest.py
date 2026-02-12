"""
PresenceOS - Test Configuration
"""
import os
import pytest
from typing import AsyncGenerator
from datetime import timedelta

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, Workspace, WorkspaceMember, UserRole
from app.models.brand import Brand, BrandVoice, BrandType

# Use test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://presenceos:presenceos@localhost:5432/presenceos_test"
)


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create engine with NullPool to avoid connection issues
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_user_inactive(db: AsyncSession) -> User:
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Inactive User",
        is_active=False,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_workspace(db: AsyncSession, test_user: User) -> Workspace:
    """Create a test workspace with the test user as owner."""
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
    )
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=test_user.id,
        role=UserRole.OWNER,
    )
    db.add(member)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@pytest.fixture
async def test_brand(db: AsyncSession, test_workspace: Workspace) -> Brand:
    """Create a test brand."""
    brand = Brand(
        workspace_id=test_workspace.id,
        name="Test Brand",
        slug="test-brand",
        brand_type=BrandType.RESTAURANT,
        description="A test restaurant brand",
    )
    db.add(brand)
    await db.flush()

    # Create brand voice
    voice = BrandVoice(
        brand_id=brand.id,
        tone_formal=50,
        tone_playful=60,
        tone_bold=40,
        tone_emotional=50,
    )
    db.add(voice)
    await db.commit()
    await db.refresh(brand)
    return brand


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for a test user."""
    token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_factory():
    """Factory to create auth headers for any user."""
    def _create_headers(user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(hours=1),
        )
        return {"Authorization": f"Bearer {token}"}
    return _create_headers
