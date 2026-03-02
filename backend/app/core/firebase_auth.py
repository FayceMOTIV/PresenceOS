"""
PresenceOS — Firebase Admin SDK integration.

Provides Firebase ID token verification for v2 API endpoints.
Gracefully degrades when Firebase is not configured (no crash).
"""
import json
import logging

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app: firebase_admin.App | None = None


def init_firebase() -> firebase_admin.App | None:
    """Initialise Firebase Admin SDK.

    Uses service account JSON from env var if available,
    otherwise falls back to Application Default Credentials (ADC).
    Returns None and logs a warning if Firebase is not configured.
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    if not settings.firebase_project_id:
        logger.warning(
            "Firebase not configured (FIREBASE_PROJECT_ID is empty) — "
            "Firebase auth will be unavailable"
        )
        return None

    try:
        # Prefer explicit service account JSON
        if settings.firebase_service_account_json:
            sa_dict = json.loads(settings.firebase_service_account_json)
            cred = credentials.Certificate(sa_dict)
        else:
            # Fallback to ADC (e.g. GOOGLE_APPLICATION_CREDENTIALS)
            cred = credentials.ApplicationDefault()

        _firebase_app = firebase_admin.initialize_app(
            cred,
            {"projectId": settings.firebase_project_id},
        )
        logger.info(
            "Firebase Admin SDK initialized",
            extra={"project_id": settings.firebase_project_id},
        )
        return _firebase_app
    except Exception as e:
        logger.error("Firebase Admin SDK init failed: %s", e)
        return None


def verify_firebase_token(id_token: str) -> dict | None:
    """Verify a Firebase ID token and return decoded claims.

    Returns None on any verification failure (invalid, expired, revoked).
    """
    if _firebase_app is None:
        logger.warning("verify_firebase_token called but Firebase is not initialized")
        return None

    try:
        decoded = firebase_auth.verify_id_token(id_token, check_revoked=True)
        return decoded
    except firebase_auth.InvalidIdTokenError:
        logger.debug("Firebase token invalid")
        return None
    except firebase_auth.ExpiredIdTokenError:
        logger.debug("Firebase token expired")
        return None
    except firebase_auth.RevokedIdTokenError:
        logger.debug("Firebase token revoked")
        return None
    except Exception as e:
        logger.warning("Firebase token verification failed: %s", e)
        return None
