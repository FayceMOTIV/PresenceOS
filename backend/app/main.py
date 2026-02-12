"""
PresenceOS - FastAPI Application
"""
import asyncio
import os

import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.resilience import registry, ServiceStatus
from app.core.degraded_middleware import DegradedModeMiddleware
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import router as health_router
from app.api.webhooks.whatsapp import router as whatsapp_webhook_router
from app.api.webhooks.telegram import router as telegram_webhook_router

# Rate limiter instance (uses Redis in production, in-memory for dev)
try:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100/minute"],
        storage_uri=settings.redis_url,
    )
except Exception:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100/minute"],
    )

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def _probe_postgresql():
    """Check PostgreSQL connectivity and update registry."""
    from sqlalchemy import text as sa_text

    try:
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
        registry.update("postgresql", ServiceStatus.HEALTHY)
        return True
    except Exception:
        registry.update("postgresql", ServiceStatus.UNAVAILABLE)
        return False


async def _probe_redis():
    """Check Redis connectivity and update registry."""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        registry.update("redis", ServiceStatus.HEALTHY)
        return True
    except Exception:
        registry.update("redis", ServiceStatus.UNAVAILABLE)
        return False


async def _health_monitor(app: FastAPI):
    """Background task that periodically checks service health.

    Enables auto-recovery: if PostgreSQL starts after the backend,
    the app automatically switches from degraded to full mode.
    """
    while True:
        try:
            pg_ok = await _probe_postgresql()
            await _probe_redis()
            app.state.degraded = not pg_ok
        except Exception as e:
            logger.error("Health monitor error", error=str(e))
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    logger.info("Starting PresenceOS API", env=settings.app_env)

    # Register services
    registry.register("postgresql", ServiceStatus.UNAVAILABLE)
    registry.register("redis", ServiceStatus.UNAVAILABLE)

    # Probe PostgreSQL
    pg_ok = await _probe_postgresql()
    if pg_ok:
        try:
            await init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.warning("Database init failed", error=str(e))
            pg_ok = False
            registry.update("postgresql", ServiceStatus.UNAVAILABLE)
    else:
        logger.warning("PostgreSQL not available — running in DEGRADED mode")

    # Probe Redis
    redis_ok = await _probe_redis()
    if not redis_ok:
        logger.warning("Redis not available — using in-memory fallback")

    # Set app-level degraded flag
    app.state.degraded = not pg_ok

    mode = "FULL" if pg_ok else "DEGRADED"
    logger.info(f"PresenceOS starting in {mode} mode", postgresql=pg_ok, redis=redis_ok)

    # Start background health monitor
    monitor_task = asyncio.create_task(_health_monitor(app))

    yield

    # Shutdown
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutting down PresenceOS API")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered social media marketing agent for multi-brand businesses",
        version="1.0.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Degraded mode middleware (must be added BEFORE CORS so it runs after CORS)
    app.add_middleware(DegradedModeMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            # Add production URLs here
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Health check probes (outside /api/v1 for Kubernetes compatibility)
    app.include_router(health_router)

    # WhatsApp webhook (outside /api/v1 for Meta compatibility)
    app.include_router(whatsapp_webhook_router)

    # Telegram webhook (outside /api/v1, same pattern)
    app.include_router(telegram_webhook_router)

    # Serve uploaded files
    upload_dir = "/tmp/presenceos/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

    # Legacy /health endpoint (kept for backwards compat)
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(
            "Unhandled exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_application()
