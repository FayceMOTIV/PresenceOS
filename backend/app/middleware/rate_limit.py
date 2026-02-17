"""Rate limiting middleware using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Rate limiter instance — uses Redis when available, falls back to in-memory
try:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200/minute"],
        storage_uri=settings.redis_url,
    )
except Exception:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200/minute"],
        storage_uri="memory://",  # Will be overridden if Redis is configured
    )
