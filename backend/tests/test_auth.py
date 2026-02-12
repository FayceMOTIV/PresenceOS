"""
PresenceOS - Auth Tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, PasswordResetToken
from app.core.security import get_password_hash, verify_password


class TestRegister:
    """Tests for user registration."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "workspace_name": "My Workspace",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]
        assert len(data["workspaces"]) == 1
        assert data["workspaces"][0]["name"] == "My Workspace"

    async def test_register_without_workspace(self, client: AsyncClient):
        """Test registration without creating a workspace."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "noworkspace@example.com",
                "password": "securepassword123",
                "full_name": "No Workspace User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["workspaces"]) == 0

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "anotherpassword123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "securepassword123",
                "full_name": "Invalid Email User",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["token"]
        assert "refresh_token" in data["token"]
        assert data["user"]["email"] == test_user.email

    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, test_user_inactive: User):
        """Test login with inactive user account."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]


class TestMe:
    """Tests for /me endpoint."""

    async def test_get_me_success(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Test getting current user info."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test /me without auth token."""
        response = await client.get("/api/v1/auth/me")
        # FastAPI returns 401 when no Authorization header is present
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test /me with invalid auth token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401


class TestForgotPassword:
    """Tests for forgot password flow."""

    async def test_forgot_password_success(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test forgot password request for existing user."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert response.status_code == 200
        # Should always return success message (anti-enumeration)
        assert "message" in response.json()

        # Verify token was created in DB
        result = await db.execute(
            select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id)
        )
        token = result.scalar_one_or_none()
        assert token is not None
        assert token.is_used is False

    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test forgot password with non-existent email (anti-enumeration)."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200
        assert "message" in response.json()

    async def test_forgot_password_inactive_user(
        self, client: AsyncClient, test_user_inactive: User
    ):
        """Test forgot password for inactive user."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user_inactive.email},
        )
        # Should still return 200 (anti-enumeration)
        assert response.status_code == 200


class TestResetPassword:
    """Tests for reset password flow."""

    async def test_reset_password_success(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test successful password reset."""
        from app.api.v1.endpoints.auth import generate_reset_token, hash_reset_token
        from datetime import datetime, timedelta, timezone

        # Create a valid reset token directly in DB
        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_token)
        await db.commit()

        # Reset the password
        new_password = "newSecurePassword456"
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": raw_token,
                "new_password": new_password,
            },
        )
        assert response.status_code == 200
        assert "successful" in response.json()["message"]

        # Verify password was changed
        await db.refresh(test_user)
        assert verify_password(new_password, test_user.hashed_password)

        # Verify token is marked as used
        await db.refresh(reset_token)
        assert reset_token.is_used is True

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test reset password with invalid token."""
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalidtoken123",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    async def test_reset_password_short_password(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test reset password with too short password."""
        from app.api.v1.endpoints.auth import generate_reset_token, hash_reset_token
        from datetime import datetime, timedelta, timezone

        # Create a valid reset token
        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_token)
        await db.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": raw_token,
                "new_password": "short",  # Less than 8 characters
            },
        )
        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    async def test_reset_password_expired_token(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test reset password with expired token."""
        from app.api.v1.endpoints.auth import generate_reset_token, hash_reset_token
        from datetime import datetime, timedelta, timezone

        # Create an expired reset token
        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        )
        db.add(reset_token)
        await db.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": raw_token,
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"]

    async def test_reset_password_used_token(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test reset password with already used token."""
        from app.api.v1.endpoints.auth import generate_reset_token, hash_reset_token
        from datetime import datetime, timedelta, timezone

        # Create a used reset token
        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=True,  # Already used
        )
        db.add(reset_token)
        await db.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": raw_token,
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "already been used" in response.json()["detail"]


class TestRefreshToken:
    """Tests for refresh token rotation."""

    async def test_refresh_token_success(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test successful token refresh with rotation."""
        # First, login to get tokens
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        tokens = response.json()["token"]
        original_refresh_token = tokens["refresh_token"]

        # Use the refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Token rotation: new refresh token should be different
        assert data["refresh_token"] != original_refresh_token

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalidtoken123"},
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    async def test_refresh_token_reuse_attack(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test that reusing an old refresh token invalidates the whole family."""
        from app.core.security import generate_refresh_token, hash_refresh_token
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta, timezone
        import uuid

        # Create a refresh token directly in DB (bypassing rate limit)
        original_raw_token = generate_refresh_token()
        original_hash = hash_refresh_token(original_raw_token)
        family_id = uuid.uuid4()

        refresh_token_db = RefreshToken(
            user_id=test_user.id,
            token_hash=original_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            family_id=family_id,
        )
        db.add(refresh_token_db)
        await db.commit()

        # Refresh once (this revokes the original token and creates a new one)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_raw_token},
        )
        assert response.status_code == 200
        new_refresh_token = response.json()["refresh_token"]

        # Try to reuse the original token (should detect reuse attack)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": original_raw_token},
        )
        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

        # The new token should also be invalidated (family compromised)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh_token},
        )
        assert response.status_code == 401

    async def test_refresh_token_expired(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test refresh with expired token."""
        from app.core.security import generate_refresh_token, hash_refresh_token
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta, timezone
        import uuid

        # Create an expired refresh token directly in DB
        raw_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_token)
        refresh_token_db = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            family_id=uuid.uuid4(),
        )
        db.add(refresh_token_db)
        await db.commit()

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_token},
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    async def test_refresh_token_inactive_user(
        self, client: AsyncClient, test_user: User, db: AsyncSession
    ):
        """Test refresh when user account is disabled."""
        from app.core.security import generate_refresh_token, hash_refresh_token
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta, timezone
        import uuid

        # Create a valid refresh token
        raw_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_token)
        refresh_token_db = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            family_id=uuid.uuid4(),
        )
        db.add(refresh_token_db)

        # Disable the user
        test_user.is_active = False
        await db.commit()

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_token},
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


class TestLogout:
    """Tests for logout endpoints."""

    async def test_logout_success(
        self, client: AsyncClient, test_user: User, auth_headers: dict, db: AsyncSession
    ):
        """Test successful logout."""
        from app.core.security import generate_refresh_token, hash_refresh_token
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta, timezone
        import uuid

        # Create a refresh token directly in DB (bypassing rate limit)
        raw_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_token)

        refresh_token_db = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            family_id=uuid.uuid4(),
        )
        db.add(refresh_token_db)
        await db.commit()

        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": raw_token},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Try to use the refresh token (should fail - token is revoked)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_token},
        )
        assert response.status_code == 401

    async def test_logout_all_devices(
        self, client: AsyncClient, test_user: User, auth_headers: dict, db: AsyncSession
    ):
        """Test logout from all devices."""
        from sqlalchemy import select
        from app.core.security import generate_refresh_token, hash_refresh_token
        from app.models.user import RefreshToken
        from datetime import datetime, timedelta, timezone
        import uuid

        # Create multiple refresh tokens directly in DB (bypassing rate limit)
        for i in range(3):
            raw_token = generate_refresh_token()
            token_hash = hash_refresh_token(raw_token)
            refresh_token_db = RefreshToken(
                user_id=test_user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            db.add(refresh_token_db)
        await db.commit()

        # Verify we have multiple tokens
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.user_id == test_user.id)
        )
        tokens_before = result.scalars().all()
        assert len(tokens_before) >= 3

        # Logout from all devices
        response = await client.post(
            "/api/v1/auth/logout-all",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "all devices" in response.json()["message"].lower()

        # Verify all tokens are deleted
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.user_id == test_user.id)
        )
        tokens_after = result.scalars().all()
        assert len(tokens_after) == 0

    async def test_logout_without_auth(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "sometoken"},
        )
        assert response.status_code == 401
