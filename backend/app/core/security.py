"""
PresenceOS - Security utilities
"""
import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jose import JWTError, jwt

from app.core.config import settings

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for storage (we don't store raw tokens)."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


class TokenEncryption:
    """Encrypt/decrypt OAuth tokens at rest using Fernet (AES-128-CBC)."""

    def __init__(self, key: str | None = None):
        encryption_key = key or settings.token_encryption_key
        if not encryption_key or len(encryption_key) < 16:
            # Generate a key if none provided (for development)
            encryption_key = secrets.token_urlsafe(32)

        # Derive a proper Fernet key from the encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"presenceos_salt_v1",  # Static salt for deterministic key derivation
            iterations=100000,
        )
        key_bytes = kdf.derive(encryption_key.encode())
        self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return base64-encoded ciphertext."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext and return plaintext."""
        return self._fernet.decrypt(ciphertext.encode()).decode()


# Singleton instance
_token_encryption: TokenEncryption | None = None


def get_token_encryption() -> TokenEncryption:
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption
