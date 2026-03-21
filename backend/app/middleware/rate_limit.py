"""Rate limiting middleware using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.observability import get_logger

_logger = get_logger(__name__)

# Rate limiter instance — uses Redis when available, falls back to in-memory
try:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200/minute"],
        storage_uri=settings.redis_url,
    )
except Exception as e:
    _logger.warning("Redis unavailable for rate limiter — using in-memory fallback", error=str(e))
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200/minute"],
        storage_uri="memory://",  # Will be overridden if Redis is configured
    )
