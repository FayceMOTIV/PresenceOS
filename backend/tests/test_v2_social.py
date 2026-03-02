"""
PresenceOS - Tests for Social v2 Endpoints

Tests covering GET /accounts, GET /accounts/{id}/subaccounts,
POST /publish, Blotato-first with Upload-Post fallback.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v2.endpoints.social import (
    AccountsResponse,
    PublishRequest,
    PublishResponse,
    SocialAccount,
    SubaccountResponse,
    get_accounts,
    get_subaccounts,
    publish_post,
)
from app.services.blotato_client import BlotatoAuthError, BlotatoError


# ── Helpers ──────────────────────────────────────────────────────────────


def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@presenceos.dev"
    return user


def _mock_db():
    return AsyncMock()


# ── GET /accounts Tests ──────────────────────────────────────────────────


class TestGetAccounts:
    @pytest.mark.asyncio
    async def test_blotato_accounts_returned(self):
        user = _mock_user()
        db = _mock_db()

        blotato_data = [
            {"id": "acc-1", "platform": "instagram", "username": "bistrot", "display_name": "Le Bistrot"},
            {"id": "acc-2", "platform": "facebook", "name": "Bistrot FB", "picture": "https://pic.jpg"},
        ]

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.get_accounts = AsyncMock(return_value=blotato_data)

            result = await get_accounts(current_user=user, db=db, platform=None)

        assert isinstance(result, AccountsResponse)
        assert result.provider == "blotato"
        assert len(result.accounts) == 2
        assert result.accounts[0].id == "acc-1"
        assert result.accounts[0].platform == "instagram"

    @pytest.mark.asyncio
    async def test_blotato_accounts_with_platform_filter(self):
        user = _mock_user()
        db = _mock_db()

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.get_accounts = AsyncMock(return_value=[
                {"id": "acc-1", "platform": "instagram", "username": "bistrot"},
            ])

            result = await get_accounts(current_user=user, db=db, platform="instagram")

        instance.get_accounts.assert_called_once_with("instagram")
        assert len(result.accounts) == 1

    @pytest.mark.asyncio
    async def test_fallback_to_upload_post_when_blotato_not_configured(self):
        user = _mock_user()
        db = _mock_db()

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = False

            result = await get_accounts(current_user=user, db=db, platform=None)

        assert result.provider == "upload_post"
        assert result.accounts == []

    @pytest.mark.asyncio
    async def test_fallback_to_upload_post_on_blotato_error(self):
        user = _mock_user()
        db = _mock_db()

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.get_accounts = AsyncMock(side_effect=BlotatoError("API error"))

            result = await get_accounts(current_user=user, db=db, platform=None)

        assert result.provider == "upload_post"
        assert result.accounts == []


# ── GET /accounts/{id}/subaccounts Tests ─────────────────────────────────


class TestGetSubaccounts:
    @pytest.mark.asyncio
    async def test_subaccounts_returned(self):
        user = _mock_user()
        db = _mock_db()

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.get_subaccounts = AsyncMock(return_value=[
                {"id": "page-1", "name": "Mon Resto"},
            ])

            result = await get_subaccounts(
                account_id="acc-1", current_user=user, db=db
            )

        assert isinstance(result, SubaccountResponse)
        assert len(result.subaccounts) == 1

    @pytest.mark.asyncio
    async def test_subaccounts_not_configured_raises_404(self):
        user = _mock_user()
        db = _mock_db()

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = False

            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await get_subaccounts(account_id="acc-1", current_user=user, db=db)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_subaccounts_blotato_error_raises_502(self):
        user = _mock_user()
        db = _mock_db()

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.get_subaccounts = AsyncMock(
                side_effect=BlotatoError("Blotato API error 500")
            )

            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await get_subaccounts(account_id="acc-1", current_user=user, db=db)

            assert exc_info.value.status_code == 502


# ── POST /publish Tests ──────────────────────────────────────────────────


class TestPublishPost:
    @pytest.mark.asyncio
    async def test_publish_via_blotato_success(self):
        user = _mock_user()
        db = _mock_db()
        body = PublishRequest(
            account_id="acc-1",
            platform="instagram",
            text="Plat du jour !",
            media_urls=["https://example.com/photo.jpg"],
        )

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.publish_post = AsyncMock(return_value={
                "id": "post-123",
                "url": "https://instagram.com/p/abc",
            })

            result = await publish_post(body=body, current_user=user, db=db)

        assert isinstance(result, PublishResponse)
        assert result.success is True
        assert result.provider == "blotato"
        assert result.post_id == "post-123"

    @pytest.mark.asyncio
    async def test_publish_fallback_to_upload_post(self):
        user = _mock_user()
        db = _mock_db()
        body = PublishRequest(
            account_id="acc-1",
            platform="instagram",
            text="Plat du jour !",
        )

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = True
            instance.publish_post = AsyncMock(side_effect=BlotatoError("Blotato down"))

            with patch("app.api.v2.endpoints.social.settings") as mock_settings:
                mock_settings.upload_post_api_key = "up-key-123"

                with patch("app.connectors.upload_post.UploadPostConnector") as MockUP:
                    mock_connector = MockUP.return_value
                    mock_connector.publish = AsyncMock(return_value={
                        "post_id": "up-post-456",
                        "post_url": "https://ig.com/p/xyz",
                    })

                    result = await publish_post(body=body, current_user=user, db=db)

        assert result.success is True
        assert result.provider == "upload_post"
        assert result.post_id == "up-post-456"

    @pytest.mark.asyncio
    async def test_publish_no_provider_raises_503(self):
        user = _mock_user()
        db = _mock_db()
        body = PublishRequest(
            account_id="acc-1",
            platform="instagram",
            text="Test",
        )

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = False

            with patch("app.api.v2.endpoints.social.settings") as mock_settings:
                mock_settings.upload_post_api_key = ""

                from fastapi import HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await publish_post(body=body, current_user=user, db=db)

                assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_publish_upload_post_failure_returns_error(self):
        user = _mock_user()
        db = _mock_db()
        body = PublishRequest(
            account_id="acc-1",
            platform="instagram",
            text="Test",
        )

        with patch("app.api.v2.endpoints.social.BlotatoClient") as MockClient:
            instance = MockClient.return_value
            instance.is_configured = False

            with patch("app.api.v2.endpoints.social.settings") as mock_settings:
                mock_settings.upload_post_api_key = "up-key"

                with patch("app.connectors.upload_post.UploadPostConnector") as MockUP:
                    mock_connector = MockUP.return_value
                    mock_connector.publish = AsyncMock(
                        side_effect=Exception("Upload-Post API error")
                    )

                    result = await publish_post(body=body, current_user=user, db=db)

        assert result.success is False
        assert result.provider == "upload_post"
        assert "Upload-Post API error" in result.error


# ── Pydantic Model Tests ────────────────────────────────────────────────


class TestModels:
    def test_publish_request_validation(self):
        req = PublishRequest(
            account_id="acc-1",
            platform="instagram",
            text="Hello world",
        )
        assert req.account_id == "acc-1"
        assert req.media_urls is None
        assert req.page_id is None

    def test_publish_request_rejects_empty_text(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PublishRequest(
                account_id="acc-1",
                platform="instagram",
                text="",
            )

    def test_social_account_defaults(self):
        account = SocialAccount(id="1", platform="instagram")
        assert account.connected is True
        assert account.username is None
