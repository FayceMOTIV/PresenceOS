"""
PresenceOS - Base Connector Interface
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.core.security import get_token_encryption


class BaseConnector(ABC):
    """Abstract base class for social media connectors."""

    platform_name: str = "unknown"

    def __init__(self):
        self._encryption = get_token_encryption()

    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage."""
        return self._encryption.encrypt(token)

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token."""
        return self._encryption.decrypt(encrypted_token)

    @abstractmethod
    def get_oauth_url(self, state: str) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.
        Returns: (url, state)
        """
        pass

    @abstractmethod
    async def exchange_code(
        self, authorization_code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access tokens.
        Returns: {
            "access_token": str,
            "refresh_token": str | None,
            "expires_at": datetime | None,
            "scope": str | None,
        }
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an expired access token.
        Returns same structure as exchange_code.
        """
        pass

    @abstractmethod
    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke an access token (disconnect).
        Returns: True if successful.
        """
        pass

    @abstractmethod
    async def get_account_info(self, access_token: str) -> dict[str, Any]:
        """
        Get connected account information.
        Returns: {
            "account_id": str,
            "account_name": str | None,
            "account_username": str | None,
            "account_avatar_url": str | None,
            "platform_data": dict | None,
        }
        """
        pass

    @abstractmethod
    async def publish(
        self,
        access_token: str,
        content: dict[str, Any],
        media_urls: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Publish content to the platform.
        Returns: {
            "post_id": str,
            "post_url": str | None,
            "published_at": datetime,
            "platform_response": dict,
        }
        """
        pass

    @abstractmethod
    async def get_post_status(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """
        Get the status of a published post.
        Returns: {
            "status": str,
            "post_url": str | None,
            "error": str | None,
        }
        """
        pass

    @abstractmethod
    async def get_post_metrics(
        self, access_token: str, post_id: str
    ) -> dict[str, Any]:
        """
        Get metrics for a published post.
        Returns metrics dict with impressions, reach, likes, etc.
        """
        pass

    @abstractmethod
    async def get_account_metrics(self, access_token: str) -> dict[str, Any]:
        """
        Get account-level metrics.
        Returns metrics dict with followers, etc.
        """
        pass
