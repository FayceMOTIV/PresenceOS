"""Tests for PostizService (headless multi-tenant) and social_publish endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

import httpx


# ── Unit Tests: PostizService ────────────────────────────────────────────


class TestPostizServiceHeadless:
    """Unit tests for headless multi-tenant PostizService."""

    def test_get_customer_id_deterministic(self):
        from app.services.postiz_service import PostizService
        cid1 = PostizService.get_customer_id("brand-abc")
        cid2 = PostizService.get_customer_id("brand-abc")
        assert cid1 == cid2
        assert cid1 == "presenceos-brand-brand-abc"

    def test_get_customer_id_different_brands(self):
        from app.services.postiz_service import PostizService
        cid1 = PostizService.get_customer_id("brand-1")
        cid2 = PostizService.get_customer_id("brand-2")
        assert cid1 != cid2

    def test_get_connect_url_format(self):
        with patch("app.services.postiz_service.settings") as mock_settings:
            mock_settings.postiz_url = "https://postiz.example.com"
            from app.services.postiz_service import PostizService
            url = PostizService.get_connect_url(
                platform="instagram",
                brand_id="test-brand-123",
                callback_url="rs3://social-callback?success=true",
            )

        assert "postiz.example.com/integrations/instagram" in url
        assert "customer=presenceos-brand-test-brand-123" in url
        assert "redirect=" in url
        # Callback URL should be URL-encoded
        assert quote("rs3://social-callback?success=true", safe="") in url

    def test_get_connect_url_all_platforms(self):
        from app.services.postiz_service import PostizService, SUPPORTED_PLATFORMS
        with patch("app.services.postiz_service.settings") as mock_settings:
            mock_settings.postiz_url = "https://postiz.test"
            for platform in SUPPORTED_PLATFORMS:
                url = PostizService.get_connect_url(
                    platform=platform,
                    brand_id="brand-1",
                    callback_url="rs3://cb",
                )
                assert f"/integrations/{platform}" in url

    def test_supported_platforms(self):
        from app.services.postiz_service import SUPPORTED_PLATFORMS
        assert "instagram" in SUPPORTED_PLATFORMS
        assert "facebook" in SUPPORTED_PLATFORMS
        assert "tiktok" in SUPPORTED_PLATFORMS
        assert "linkedin" in SUPPORTED_PLATFORMS
        assert "x" in SUPPORTED_PLATFORMS
        assert "youtube" in SUPPORTED_PLATFORMS

    @pytest.mark.asyncio
    async def test_list_integrations(self):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "abc123", "identifier": "instagram", "name": "Mon Resto", "disabled": False},
            {"id": "def456", "identifier": "facebook", "name": "Page FB", "disabled": False},
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.list_integrations()

        assert len(result) == 2
        assert result[0]["identifier"] == "instagram"

    @pytest.mark.asyncio
    async def test_list_brand_integrations_filters_by_customer(self):
        """list_brand_integrations returns only integrations matching the brand's customer ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "int-1", "identifier": "instagram", "name": "Brand A Insta",
                "customer": {"id": "presenceos-brand-brand-a"}, "disabled": False,
            },
            {
                "id": "int-2", "identifier": "facebook", "name": "Brand B FB",
                "customer": {"id": "presenceos-brand-brand-b"}, "disabled": False,
            },
            {
                "id": "int-3", "identifier": "tiktok", "name": "Brand A TikTok",
                "customer": {"id": "presenceos-brand-brand-a"}, "disabled": False,
            },
            {
                "id": "int-4", "identifier": "linkedin", "name": "Brand A Disabled",
                "customer": {"id": "presenceos-brand-brand-a"}, "disabled": True,
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.list_brand_integrations("brand-a")

        # Should get int-1 (insta) + int-3 (tiktok), NOT int-2 (brand-b) or int-4 (disabled)
        assert len(result) == 2
        ids = [i["id"] for i in result]
        assert "int-1" in ids
        assert "int-3" in ids
        assert "int-2" not in ids
        assert "int-4" not in ids

    @pytest.mark.asyncio
    async def test_list_brand_integrations_empty_for_unknown_brand(self):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "int-1", "identifier": "instagram",
                "customer": {"id": "presenceos-brand-brand-a"}, "disabled": False,
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.list_brand_integrations("unknown-brand")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_integration_by_platform_found(self):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "abc123", "identifier": "instagram", "name": "Mon Resto",
                "customer": {"id": "presenceos-brand-brand-1"}, "disabled": False,
            },
            {
                "id": "def456", "identifier": "tiktok", "name": "TikTok",
                "customer": {"id": "presenceos-brand-brand-1"}, "disabled": False,
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.get_integration_by_platform("brand-1", "tiktok")

        assert result is not None
        assert result["id"] == "def456"

    @pytest.mark.asyncio
    async def test_get_integration_by_platform_not_found(self):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "abc123", "identifier": "instagram",
                "customer": {"id": "presenceos-brand-brand-1"}, "disabled": False,
            },
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.get_integration_by_platform("brand-1", "linkedin")

        assert result is None

    @pytest.mark.asyncio
    async def test_disconnect_integration(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.disconnect_integration("int-123")

        assert result["ok"] is True
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_now_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "post_123", "status": "published"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.publish_now(
                integration_ids=["abc123"],
                content="Nouvelle pizza margherita !",
            )

        assert result["status"] == "published"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_post_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "post_456", "status": "scheduled"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        future = datetime.now(timezone.utc) + timedelta(days=1)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.schedule_post(
                integration_ids=["abc123", "def456"],
                content="Brunch dimanche !",
                publish_at=future,
            )

        assert result["status"] == "scheduled"
        call_kwargs = mock_client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert len(payload["posts"]) == 2
        assert payload["type"] == "schedule"

    @pytest.mark.asyncio
    async def test_delete_post_success(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"deleted": True}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.delete_post("post_123")

        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_health_check_ok(self):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client),
            patch("app.services.postiz_service.settings") as mock_settings,
        ):
            mock_settings.postiz_url = "http://postiz.test"
            mock_settings.postiz_api_key = "test-key"
            from app.services.postiz_service import PostizService
            result = await PostizService.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_no_url(self):
        with patch("app.services.postiz_service.settings") as mock_settings:
            mock_settings.postiz_url = ""
            from app.services.postiz_service import PostizService
            result = await PostizService.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_upload_from_url(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "media_789", "path": "/uploads/test.jpg"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.services.postiz_service.httpx.AsyncClient", return_value=mock_client):
            from app.services.postiz_service import PostizService
            result = await PostizService.upload_from_url("https://s3.example.com/photo.jpg")

        assert result["id"] == "media_789"
        assert result["path"] == "/uploads/test.jpg"


# ── Endpoint Tests (auth + validation) ──────────────────────────────────


class TestSocialPublishEndpoints:
    """Integration tests for social_publish endpoints (V2 auth)."""

    def test_connect_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/api/v2/publish/brands/test-brand/connect/instagram")
        assert resp.status_code in (401, 403)

    def test_integrations_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/api/v2/publish/brands/test-brand/integrations")
        assert resp.status_code in (401, 403)

    def test_disconnect_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.delete("/api/v2/publish/brands/test-brand/integrations/int-123")
        assert resp.status_code in (401, 403)

    def test_publish_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.post("/api/v2/publish/brands/test-brand/publish", json={
            "integration_ids": ["abc"],
            "content": "test",
        })
        assert resp.status_code in (401, 403)

    def test_schedule_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.post("/api/v2/publish/brands/test-brand/schedule", json={
            "integration_ids": ["abc"],
            "content": "test",
            "publish_at": "2020-01-01T00:00:00Z",
        })
        assert resp.status_code in (401, 403)

    def test_posts_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/api/v2/publish/brands/test-brand/posts")
        assert resp.status_code in (401, 403)

    def test_analytics_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        resp = client.get("/api/v2/publish/brands/test-brand/analytics/int-123")
        assert resp.status_code in (401, 403)

    def test_health_endpoint_no_auth_needed(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        with patch("app.services.postiz_service.PostizService.health_check", new_callable=AsyncMock, return_value=False):
            resp = client.get("/api/v2/publish/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "postiz" in data

    def test_callback_redirect_success(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/api/v2/publish/callback?brand_id=b1&platform=instagram")
        assert resp.status_code in (307, 302)
        assert "rs3://social-callback" in resp.headers.get("location", "")
        assert "success=true" in resp.headers.get("location", "")

    def test_callback_redirect_error(self):
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app, follow_redirects=False)
        resp = client.get("/api/v2/publish/callback?platform=instagram&error=access_denied")
        assert resp.status_code in (307, 302)
        location = resp.headers.get("location", "")
        assert "success=false" in location
        assert "access_denied" in location
