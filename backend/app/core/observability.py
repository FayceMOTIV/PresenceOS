"""
Observabilité RS3 — logging structuré + Sentry optionnel.

Centralise:
- get_logger(name) → structlog logger cohérent avec le reste de l'app
- init_sentry()     → initialise Sentry si SENTRY_DSN est présent
- capture_exception → log + forwarde vers Sentry avec contexte

Usage:
    from app.core.observability import get_logger, capture_exception
    logger = get_logger(__name__)

    try:
        ...
    except Exception as e:
        logger.error("Description du problème", error=str(e))
        capture_exception(e, {"context": "description"})
"""

import os
from typing import Optional

import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structured logger bound to the given module name.

    Uses structlog (already configured in main.py) for JSON-formatted,
    production-ready logging that is consistent across the app.
    """
    return structlog.get_logger(name)


def init_sentry() -> None:
    """Initialize Sentry error tracking if SENTRY_DSN is set.

    Called once at application startup (main.py lifespan).
    Safe to call even if sentry-sdk is not installed.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        get_logger("sentry").debug("SENTRY_DSN not set — Sentry disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        def _filter_sensitive_data(event, hint):
            """Strip passwords and tokens before sending to Sentry."""
            if "request" in event and "data" in event["request"]:
                data = event["request"]["data"]
                if isinstance(data, dict):
                    for key in ("password", "token", "api_key", "secret"):
                        if key in data:
                            data[key] = "[FILTERED]"
            return event

        sentry_sdk.init(
            dsn=dsn,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "production"),
            before_send=_filter_sensitive_data,
        )
        get_logger("sentry").info("Sentry initialisé", environment=os.getenv("ENVIRONMENT", "production"))
    except ImportError:
        get_logger("sentry").warning("sentry-sdk non installé — SENTRY_DSN ignoré")


def capture_exception(e: Exception, context: Optional[dict] = None) -> None:
    """Log an exception and forward it to Sentry (if available).

    Always logs the error via structlog. If Sentry is initialized,
    the exception is also captured there with optional extra context.

    Args:
        e: The exception to capture.
        context: Optional dict of extra context (e.g. {"brand_id": "...", "endpoint": "/..."}).
    """
    logger = get_logger("error")
    logger.error(
        f"{type(e).__name__}: {e}",
        error_type=type(e).__name__,
        **(context or {}),
    )
    try:
        import sentry_sdk

        if sentry_sdk.is_initialized():
            with sentry_sdk.push_scope() as scope:
                if context:
                    for k, v in context.items():
                        scope.set_extra(k, v)
                sentry_sdk.capture_exception(e)
    except ImportError:
        pass  # sentry-sdk not installed — already logged above
