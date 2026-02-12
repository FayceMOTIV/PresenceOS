"""
PresenceOS - Resilience Tests

Verifies that ALL routes respond correctly when the database is unavailable.
Uses ASGI transport to hit the real app in degraded mode.
"""
import io
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """HTTP client that hits the app directly via ASGI transport."""
    from app.core.resilience import registry, ServiceStatus

    # Force degraded mode
    app.state.degraded = True
    # Ensure services are registered (lifespan doesn't run in ASGI tests)
    registry.register("postgresql", ServiceStatus.UNAVAILABLE)
    registry.register("redis", ServiceStatus.UNAVAILABLE)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Restore
    app.state.degraded = True  # Keep degraded since there's no real DB in tests


# ── Health Probes ────────────────────────────────────────────────

class TestHealthProbes:
    @pytest.mark.asyncio
    async def test_health_live_always_200(self, client):
        """Liveness probe always returns 200."""
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_health_ready_503_without_db(self, client):
        """Readiness probe returns 503 when DB is unavailable."""
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["postgresql"] == "unavailable"

    @pytest.mark.asyncio
    async def test_health_status_shows_degraded(self, client):
        """Status endpoint shows degraded mode."""
        response = await client.get("/health/status")
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "degraded"
        assert "postgresql" in data["services"]
        assert "redis" in data["services"]

    @pytest.mark.asyncio
    async def test_legacy_health_endpoint(self, client):
        """Legacy /health endpoint still works."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ── Degraded Mode GET Endpoints ──────────────────────────────────

class TestGracefulDegradation:
    """Verifies that ALL GET routes respond with mock data when DB is absent."""

    DEGRADED_ROUTES = [
        ("/api/v1/brands/test-brand", dict),
        ("/api/v1/knowledge/brands/test-brand", list),
        ("/api/v1/knowledge/brands/test-brand/categories", dict),
        ("/api/v1/ideas/brands/test-brand", list),
        ("/api/v1/ideas/brands/test-brand/daily", list),
        ("/api/v1/drafts/brands/test-brand", list),
        ("/api/v1/connectors/brands/test-brand", list),
        ("/api/v1/posts/brands/test-brand", list),
        ("/api/v1/posts/brands/test-brand/calendar", dict),
        ("/api/v1/metrics/brands/test-brand/dashboard", dict),
        ("/api/v1/metrics/brands/test-brand/platforms", list),
        ("/api/v1/metrics/brands/test-brand/top-posts", dict),
        ("/api/v1/metrics/brands/test-brand/learning", dict),
        ("/api/v1/autopilot/brands/test-brand/autopilot", dict),
        ("/api/v1/autopilot/brands/test-brand/autopilot/pending", list),
        ("/api/v1/media-library/brands/test-brand/assets", list),
        ("/api/v1/media-library/brands/test-brand/stats", dict),
        ("/api/v1/users/me", dict),
        ("/api/v1/auth/me", dict),
        ("/api/v1/users/me/workspaces", list),
        ("/api/v1/workspaces/test-ws/brands", list),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("route,expected_type", DEGRADED_ROUTES)
    async def test_route_returns_200_without_db(self, client, route, expected_type):
        """Each route must return 200 with correct data type in degraded mode."""
        response = await client.get(route)
        assert response.status_code == 200, f"{route} returned {response.status_code}"
        data = response.json()
        assert isinstance(data, expected_type), f"{route} returned {type(data).__name__}, expected {expected_type.__name__}"

    @pytest.mark.asyncio
    async def test_degraded_flag_present(self, client):
        """Dict responses include degraded: true."""
        routes_with_degraded = [
            "/api/v1/brands/test-brand",
            "/api/v1/metrics/brands/test-brand/dashboard",
            "/api/v1/metrics/brands/test-brand/learning",
            "/api/v1/autopilot/brands/test-brand/autopilot",
            "/api/v1/users/me",
            "/api/v1/auth/me",
            "/api/v1/media-library/brands/test-brand/stats",
        ]
        for route in routes_with_degraded:
            response = await client.get(route)
            data = response.json()
            if isinstance(data, dict):
                assert data.get("degraded") is True, f"{route} missing degraded flag"


# ── Chat & Upload (must work in degraded mode) ──────────────────

class TestChatInDegradedMode:
    @pytest.mark.asyncio
    async def test_chat_upload_works(self, client):
        """Upload endpoint works without DB."""
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        response = await client.post(
            "/api/v1/chat/upload",
            files={"file": ("test.jpg", fake_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "media_id" in data
        assert data["media_id"].endswith(".jpg")

    @pytest.mark.asyncio
    async def test_chat_message_works(self, client):
        """Chat message endpoint works without DB."""
        response = await client.post(
            "/api/v1/chat/message",
            json={"msg_type": "text", "text": "hello"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "session_id" in data


# ── Write Operations Return 503 ─────────────────────────────────

class TestWriteOperationsBlocked:
    @pytest.mark.asyncio
    async def test_post_brands_returns_503(self, client):
        """Write operations that need DB return 503 in degraded mode."""
        response = await client.post(
            "/api/v1/brands",
            json={"name": "test"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data.get("degraded") is True

    @pytest.mark.asyncio
    async def test_delete_returns_503(self, client):
        """DELETE operations return 503 in degraded mode."""
        response = await client.delete("/api/v1/brands/test-brand")
        assert response.status_code == 503


# ── ServiceRegistry Unit Tests ───────────────────────────────────

class TestServiceRegistry:
    def test_singleton(self):
        """ServiceRegistry is a singleton."""
        from app.core.resilience import ServiceRegistry
        a = ServiceRegistry()
        b = ServiceRegistry()
        assert a is b

    def test_register_and_check(self):
        """Can register and check service status."""
        from app.core.resilience import ServiceRegistry, ServiceStatus
        reg = ServiceRegistry()
        reg.register("test_service", ServiceStatus.HEALTHY)
        assert reg.is_available("test_service") is True
        reg.update("test_service", ServiceStatus.UNAVAILABLE)
        assert reg.is_available("test_service") is False

    def test_get_status(self):
        """get_status returns all registered services."""
        from app.core.resilience import ServiceRegistry, ServiceStatus
        reg = ServiceRegistry()
        reg.register("postgresql", ServiceStatus.UNAVAILABLE)
        status = reg.get_status()
        assert "postgresql" in status
        assert status["postgresql"]["status"] == "unavailable"

    def test_is_degraded(self):
        """is_degraded is True when postgresql is unavailable."""
        from app.core.resilience import ServiceRegistry, ServiceStatus
        reg = ServiceRegistry()
        reg.register("postgresql", ServiceStatus.UNAVAILABLE)
        assert reg.is_degraded is True
        reg.update("postgresql", ServiceStatus.HEALTHY)
        assert reg.is_degraded is False
