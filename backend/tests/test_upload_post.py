"""
PresenceOS - Upload-Post Connector Tests

Tests the Upload-Post connector (Instagram, Facebook, TikTok)
and factory routing.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import httpx

from app.connectors.upload_post import (
    UploadPostConnector,
    RateLimitError,
    AuthenticationError,
    ContentRejectedError,
    PublishError,
    UPLOAD_POST_API_URL,
)
from app.connectors.factory import get_connector_handler
from app.connectors.linkedin import LinkedInConnector
from app.models.publishing import SocialPlatform


# =============================================================================
# Factory Routing Tests
# =============================================================================

class TestConnectorFactory:
    """Verify factory routes platforms to the correct connector."""

    def test_linkedin_returns_linkedin_connector(self):
        handler = get_connector_handler(SocialPlatform.LINKEDIN)
        assert isinstance(handler, LinkedInConnector)

    def test_instagram_returns_upload_post_connector(self):
        handler = get_connector_handler(SocialPlatform.INSTAGRAM)
        assert isinstance(handler, UploadPostConnector)
        assert handler.platform == "instagram"

    def test_facebook_returns_upload_post_connector(self):
        handler = get_connector_handler(SocialPlatform.FACEBOOK)
        assert isinstance(handler, UploadPostConnector)
        assert handler.platform == "facebook"

    def test_tiktok_returns_upload_post_connector(self):
        handler = get_connector_handler(SocialPlatform.TIKTOK)
        assert isinstance(handler, UploadPostConnector)
        assert handler.platform == "tiktok"

    def test_unsupported_platform_raises(self):
        with pytest.raises(ValueError, match="Unsupported platform"):
            get_connector_handler("twitter")


# =============================================================================
# UploadPostConnector Unit Tests
# =============================================================================

class TestUploadPostConnector:
    """Unit tests for the UploadPostConnector."""

    def test_init_default_platform(self):
        connector = UploadPostConnector()
        assert connector.platform == "instagram"
        assert connector.platform_name == "upload_post"

    def test_init_custom_platform(self):
        connector = UploadPostConnector(platform="tiktok")
        assert connector.platform == "tiktok"

    def test_oauth_url_raises(self):
        connector = UploadPostConnector()
        with pytest.raises(NotImplementedError):
            connector.get_oauth_url("state")

    @pytest.mark.asyncio
    async def test_exchange_code_raises(self):
        connector = UploadPostConnector()
        with pytest.raises(NotImplementedError):
            await connector.exchange_code("code", "uri")

    @pytest.mark.asyncio
    async def test_refresh_token_returns_api_key(self):
        connector = UploadPostConnector()
        result = await connector.refresh_token("old_token")
        assert result["access_token"] == connector.api_key
        assert result["refresh_token"] is None
        assert result["expires_at"] is None

    @pytest.mark.asyncio
    async def test_revoke_token_returns_true(self):
        connector = UploadPostConnector()
        result = await connector.revoke_token("token")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_account_info(self):
        connector = UploadPostConnector(platform="facebook")
        result = await connector.get_account_info("key")
        assert result["account_id"] == "upload-post-facebook"
        assert "Facebook" in result["account_name"]
        assert result["platform_data"]["provider"] == "upload-post"
        assert result["platform_data"]["platform"] == "facebook"


# =============================================================================
# Publish Tests (mocked HTTP)
# =============================================================================

class TestUploadPostPublish:
    """Test the publish method with mocked Upload-Post API."""

    @pytest.mark.asyncio
    async def test_publish_success(self):
        """Test successful publish via Upload-Post API."""
        connector = UploadPostConnector(platform="instagram")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "post-123",
            "platforms": [
                {"name": "instagram", "url": "https://instagram.com/p/abc123"}
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await connector.publish(
                access_token="test-api-key",
                content={
                    "caption": "Test post",
                    "hashtags": ["test", "presenceos"],
                    "account_username": "testuser",
                },
                media_urls=None,
            )

            assert result["post_id"] == "post-123"
            assert result["post_url"] == "https://instagram.com/p/abc123"
            assert result["published_at"] is not None

            # Verify the API was called correctly
            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args
            assert call_kwargs.args[0] == UPLOAD_POST_API_URL
            assert call_kwargs.kwargs["headers"]["Authorization"] == "Apikey test-api-key"

    @pytest.mark.asyncio
    async def test_publish_with_hashtags(self):
        """Test that hashtags are appended to caption."""
        connector = UploadPostConnector(platform="instagram")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "post-456"}
        mock_response.raise_for_status = MagicMock()

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            await connector.publish(
                access_token="key",
                content={
                    "caption": "Hello",
                    "hashtags": ["food", "paris"],
                },
            )

            call_kwargs = mock_client.post.call_args
            data = call_kwargs.kwargs["data"]
            assert "#food" in data["title"]
            assert "#paris" in data["title"]

    @pytest.mark.asyncio
    async def test_publish_rate_limit(self):
        """Test 429 response raises RateLimitError."""
        connector = UploadPostConnector(platform="tiktok")

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            with pytest.raises(RateLimitError):
                await connector.publish(
                    access_token="key",
                    content={"caption": "Test"},
                )

    @pytest.mark.asyncio
    async def test_publish_auth_error(self):
        """Test 401 response raises AuthenticationError."""
        connector = UploadPostConnector(platform="facebook")

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            with pytest.raises(AuthenticationError):
                await connector.publish(
                    access_token="bad-key",
                    content={"caption": "Test"},
                )

    @pytest.mark.asyncio
    async def test_publish_content_rejected(self):
        """Test 422 response raises ContentRejectedError."""
        connector = UploadPostConnector(platform="instagram")

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "Image too small"}
        mock_response.text = "Image too small"

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            with pytest.raises(ContentRejectedError, match="Image too small"):
                await connector.publish(
                    access_token="key",
                    content={"caption": "Test"},
                )

    @pytest.mark.asyncio
    async def test_publish_timeout(self):
        """Test timeout raises PublishError."""
        connector = UploadPostConnector(platform="instagram")

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("timeout")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            with pytest.raises(PublishError, match="Timeout"):
                await connector.publish(
                    access_token="key",
                    content={"caption": "Test"},
                )

    @pytest.mark.asyncio
    async def test_publish_no_api_key(self):
        """Test missing API key raises ValueError."""
        connector = UploadPostConnector(platform="instagram")
        connector.api_key = ""

        with pytest.raises(ValueError, match="Cle API"):
            await connector.publish(
                access_token="",
                content={"caption": "Test"},
            )

    @pytest.mark.asyncio
    async def test_publish_fallback_url_extraction(self):
        """Test URL extraction from dict-style platforms response."""
        connector = UploadPostConnector(platform="facebook")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "post-789",
            "platforms": {
                "facebook": {"url": "https://facebook.com/posts/789"},
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.connectors.upload_post.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await connector.publish(
                access_token="key",
                content={"caption": "Test"},
            )

            assert result["post_url"] == "https://facebook.com/posts/789"


# =============================================================================
# Post Status & Metrics Tests
# =============================================================================

class TestUploadPostMetrics:
    """Test post status and metrics methods."""

    @pytest.mark.asyncio
    async def test_get_post_status(self):
        connector = UploadPostConnector()
        result = await connector.get_post_status("token", "post-id")
        assert result["status"] == "published"

    @pytest.mark.asyncio
    async def test_get_post_metrics(self):
        connector = UploadPostConnector()
        result = await connector.get_post_metrics("token", "post-id")
        assert result["likes"] == 0
        assert result["comments"] == 0

    @pytest.mark.asyncio
    async def test_get_account_metrics(self):
        connector = UploadPostConnector()
        result = await connector.get_account_metrics("token")
        assert result["followers_count"] == 0
