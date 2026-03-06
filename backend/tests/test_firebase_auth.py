"""
Tests for Firebase Auth integration (Sprint 2).
Tests the firebase_auth module in isolation using mocks.
"""
import json
from unittest.mock import MagicMock, patch

import pytest


# ── init_firebase tests ──


def test_init_firebase_no_project_id():
    """init_firebase returns None when project_id is empty."""
    with patch("app.core.firebase_auth.settings") as mock_settings:
        mock_settings.firebase_project_id = ""
        mock_settings.firebase_service_account_json = ""

        # Reset the module-level state
        import app.core.firebase_auth as fb_mod
        fb_mod._firebase_app = None

        result = fb_mod.init_firebase()
        assert result is None


def test_init_firebase_already_initialized():
    """init_firebase returns existing app if already initialized."""
    import app.core.firebase_auth as fb_mod

    mock_app = MagicMock()
    fb_mod._firebase_app = mock_app

    result = fb_mod.init_firebase()
    assert result is mock_app

    # Clean up
    fb_mod._firebase_app = None


def test_init_firebase_with_service_account_json():
    """init_firebase initializes with service account JSON."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = None

    fake_sa = json.dumps({
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    })

    with (
        patch("app.core.firebase_auth.settings") as mock_settings,
        patch("app.core.firebase_auth.firebase_admin") as mock_admin,
        patch("app.core.firebase_auth.credentials") as mock_creds,
    ):
        mock_settings.firebase_project_id = "test-project"
        mock_settings.firebase_service_account_json = fake_sa

        mock_cert = MagicMock()
        mock_creds.Certificate.return_value = mock_cert
        mock_admin.initialize_app.return_value = MagicMock()

        result = fb_mod.init_firebase()

        mock_creds.Certificate.assert_called_once()
        mock_admin.initialize_app.assert_called_once_with(
            mock_cert,
            {"projectId": "test-project"},
        )
        assert result is not None

    # Clean up
    fb_mod._firebase_app = None


def test_init_firebase_with_adc():
    """init_firebase falls back to ADC when no service account JSON."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = None

    with (
        patch("app.core.firebase_auth.settings") as mock_settings,
        patch("app.core.firebase_auth.firebase_admin") as mock_admin,
        patch("app.core.firebase_auth.credentials") as mock_creds,
    ):
        mock_settings.firebase_project_id = "test-project"
        mock_settings.firebase_service_account_json = ""

        mock_adc = MagicMock()
        mock_creds.ApplicationDefault.return_value = mock_adc
        mock_admin.initialize_app.return_value = MagicMock()

        result = fb_mod.init_firebase()

        mock_creds.ApplicationDefault.assert_called_once()
        mock_admin.initialize_app.assert_called_once_with(
            mock_adc,
            {"projectId": "test-project"},
        )
        assert result is not None

    # Clean up
    fb_mod._firebase_app = None


# ── verify_firebase_token tests ──


def test_verify_token_no_firebase_app():
    """verify_firebase_token returns None when Firebase is not initialized."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = None

    result = fb_mod.verify_firebase_token("some-token")
    assert result is None


def test_verify_token_valid():
    """verify_firebase_token returns decoded claims for a valid token."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = MagicMock()

    decoded = {"uid": "abc123", "email": "user@test.com", "name": "Test User"}

    with patch("app.core.firebase_auth.firebase_auth") as mock_fb_auth:
        mock_fb_auth.verify_id_token.return_value = decoded

        result = fb_mod.verify_firebase_token("valid-token")

        mock_fb_auth.verify_id_token.assert_called_once_with(
            "valid-token", check_revoked=True
        )
        assert result == decoded

    fb_mod._firebase_app = None


def test_verify_token_invalid():
    """verify_firebase_token returns None for an invalid token."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = MagicMock()

    InvalidError = type("InvalidIdTokenError", (Exception,), {})
    ExpiredError = type("ExpiredIdTokenError", (Exception,), {})
    RevokedError = type("RevokedIdTokenError", (Exception,), {})

    with patch("app.core.firebase_auth.firebase_auth") as mock_fb_auth:
        mock_fb_auth.InvalidIdTokenError = InvalidError
        mock_fb_auth.ExpiredIdTokenError = ExpiredError
        mock_fb_auth.RevokedIdTokenError = RevokedError
        mock_fb_auth.verify_id_token.side_effect = InvalidError("bad")

        result = fb_mod.verify_firebase_token("bad-token")
        assert result is None

    fb_mod._firebase_app = None


def test_verify_token_expired():
    """verify_firebase_token returns None for an expired token."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = MagicMock()

    # Must define all exception classes so the except chain doesn't fail
    InvalidError = type("InvalidIdTokenError", (Exception,), {})
    ExpiredError = type("ExpiredIdTokenError", (Exception,), {})
    RevokedError = type("RevokedIdTokenError", (Exception,), {})

    with patch("app.core.firebase_auth.firebase_auth") as mock_fb_auth:
        mock_fb_auth.InvalidIdTokenError = InvalidError
        mock_fb_auth.ExpiredIdTokenError = ExpiredError
        mock_fb_auth.RevokedIdTokenError = RevokedError
        mock_fb_auth.verify_id_token.side_effect = ExpiredError("expired")

        from app.core.firebase_auth import TokenExpiredError
        with pytest.raises(TokenExpiredError):
            fb_mod.verify_firebase_token("expired-token")

    fb_mod._firebase_app = None


def test_verify_token_revoked():
    """verify_firebase_token returns None for a revoked token."""
    import app.core.firebase_auth as fb_mod
    fb_mod._firebase_app = MagicMock()

    InvalidError = type("InvalidIdTokenError", (Exception,), {})
    ExpiredError = type("ExpiredIdTokenError", (Exception,), {})
    RevokedError = type("RevokedIdTokenError", (Exception,), {})

    with patch("app.core.firebase_auth.firebase_auth") as mock_fb_auth:
        mock_fb_auth.InvalidIdTokenError = InvalidError
        mock_fb_auth.ExpiredIdTokenError = ExpiredError
        mock_fb_auth.RevokedIdTokenError = RevokedError
        mock_fb_auth.verify_id_token.side_effect = RevokedError("revoked")

        result = fb_mod.verify_firebase_token("revoked-token")
        assert result is None

    fb_mod._firebase_app = None
