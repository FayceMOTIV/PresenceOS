"""
PresenceOS - Tests for Blotato Social Publishing Client

Tests covering account fetching, publishing, error handling (401, 429),
timeout handling, and unconfigured API key scenarios.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.blotato_client import (
    BlotatoClient,
    BlotatoAuthError,
    BlotatoError,
    BlotatoRateLimitError,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _mock_response(status_code: int = 200, json_data=None, text: str = "", headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text
    resp.headers = headers or {}
    return resp


# ── Constructor & Config Tests ───────────────────────────────────────────


class TestBlotatoClientConfig:
    def test_is_configured_with_key(self):
        client = BlotatoClient(api_key="test-key-123")
        assert client.is_configured is True

    def test_is_not_configured_without_key(self):
        with patch("app.services.blotato_client.settings") as mock_settings:
            mock_settings.blotato_api_key = ""
            client = BlotatoClient(api_key="")
            assert client.is_configured is False

    def test_headers_include_api_key(self):
        client = BlotatoClient(api_key="my-api-key")
        headers = client._headers
        assert headers["blotato-api-key"] == "my-api-key"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_request_without_key_raises_auth_error(self):
        with patch("app.services.blotato_client.settings") as mock_settings:
            mock_settings.blotato_api_key = ""
            client = BlotatoClient(api_key="")
            with pytest.raises(BlotatoAuthError, match="not configured"):
                await client.get_accounts()


# ── Get Accounts Tests ───────────────────────────────────────────────────


class TestGetAccounts:
    @pytest.mark.asyncio
    async def test_get_accounts_success_list_response(self):
        accounts_data = [
            {"id": "acc-1", "platform": "instagram", "username": "bistrot"},
            {"id": "acc-2", "platform": "facebook", "username": "bistrot_fb"},
        ]
        mock_resp = _mock_response(200, json_data=accounts_data)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.get_accounts()

        assert len(result) == 2
        assert result[0]["id"] == "acc-1"

    @pytest.mark.asyncio
    async def test_get_accounts_success_dict_response(self):
        accounts_data = {
            "accounts": [{"id": "acc-1", "platform": "instagram"}]
        }
        mock_resp = _mock_response(200, json_data=accounts_data)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.get_accounts()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_accounts_with_platform_filter(self):
        mock_resp = _mock_response(200, json_data=[])

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.get_accounts(platform="instagram")

        assert result == []
        call_args = mock_instance.request.call_args
        assert call_args.kwargs.get("params") == {"platform": "instagram"}


# ── Get Subaccounts Tests ────────────────────────────────────────────────


class TestGetSubaccounts:
    @pytest.mark.asyncio
    async def test_get_subaccounts_success(self):
        subs_data = [
            {"id": "page-1", "name": "Mon Resto"},
            {"id": "page-2", "name": "Mon Resto 2"},
        ]
        mock_resp = _mock_response(200, json_data=subs_data)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.get_subaccounts("acc-1")

        assert len(result) == 2
        assert result[0]["name"] == "Mon Resto"


# ── Publish Post Tests ───────────────────────────────────────────────────


class TestPublishPost:
    @pytest.mark.asyncio
    async def test_publish_post_success(self):
        publish_data = {"id": "post-123", "url": "https://instagram.com/p/abc"}
        mock_resp = _mock_response(200, json_data=publish_data)

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.publish_post(
                account_id="acc-1",
                platform="instagram",
                text="Plat du jour !",
                media_urls=["https://example.com/photo.jpg"],
            )

        assert result["id"] == "post-123"
        assert result["url"] == "https://instagram.com/p/abc"

        # Verify the body sent
        call_args = mock_instance.request.call_args
        body = call_args.kwargs.get("json")
        assert body["account_id"] == "acc-1"
        assert body["platform"] == "instagram"
        assert body["text"] == "Plat du jour !"
        assert body["media_urls"] == ["https://example.com/photo.jpg"]

    @pytest.mark.asyncio
    async def test_publish_post_with_schedule(self):
        mock_resp = _mock_response(200, json_data={"id": "post-456"})

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.publish_post(
                account_id="acc-1",
                platform="facebook",
                text="Post programmé",
                scheduled_at="2026-03-15T10:00:00Z",
            )

        assert result["id"] == "post-456"
        call_args = mock_instance.request.call_args
        body = call_args.kwargs.get("json")
        assert body["scheduled_at"] == "2026-03-15T10:00:00Z"

    @pytest.mark.asyncio
    async def test_publish_post_minimal_params(self):
        mock_resp = _mock_response(200, json_data={"id": "post-789"})

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            result = await client.publish_post(
                account_id="acc-1",
                platform="tiktok",
                text="Video virale !",
            )

        call_args = mock_instance.request.call_args
        body = call_args.kwargs.get("json")
        assert "media_urls" not in body
        assert "page_id" not in body
        assert "scheduled_at" not in body


# ── Error Handling Tests ─────────────────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self):
        mock_resp = _mock_response(401, json_data={"message": "Invalid API key"})

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="bad-key")
            with pytest.raises(BlotatoAuthError, match="invalid or expired"):
                await client.get_accounts()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self):
        mock_resp = _mock_response(
            429,
            json_data={"message": "Too many requests"},
            headers={"Retry-After": "30"},
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            with pytest.raises(BlotatoRateLimitError, match="Retry after 30s"):
                await client.publish_post("acc-1", "instagram", "test")

    @pytest.mark.asyncio
    async def test_500_raises_generic_error(self):
        mock_resp = _mock_response(
            500,
            json_data={"message": "Internal server error"},
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            with pytest.raises(BlotatoError, match="500"):
                await client.get_accounts()

    @pytest.mark.asyncio
    async def test_timeout_raises_error(self):
        import httpx as httpx_mod

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=httpx_mod.TimeoutException("timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            with pytest.raises(BlotatoError, match="timeout"):
                await client.get_accounts()

    @pytest.mark.asyncio
    async def test_error_with_non_json_body(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.json.side_effect = Exception("not json")
        mock_resp.text = "Bad Gateway"
        mock_resp.headers = {}

        with patch("httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_resp)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            client = BlotatoClient(api_key="test-key")
            with pytest.raises(BlotatoError, match="502"):
                await client.get_accounts()
