"""
PresenceOS - Health Check Endpoints (Kubernetes-ready)

Three probes following the Kubernetes health check pattern:
- /health/live   : Is the process alive?
- /health/ready  : Can we accept traffic? (checks DB + Redis)
- /health/status : Detailed status of all services
"""
from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.resilience import registry, ServiceStatus

router = APIRouter(tags=["Health"])


@router.get("/health/live")
async def liveness():
    """Liveness probe: always 200 if the process is running."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(response: Response):
    """Readiness probe: 200 if critical services are available, 503 otherwise."""
    pg_ok = registry.is_available("postgresql")
    redis_ok = registry.is_available("redis")

    if pg_ok:
        return {"status": "ready", "postgresql": "ok", "redis": "ok" if redis_ok else "unavailable"}

    response.status_code = 503
    return {
        "status": "not_ready",
        "postgresql": "ok" if pg_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
    }


@router.get("/health/status")
async def detailed_status():
    """Detailed status of all registered services."""
    services = registry.get_status()
    degraded = registry.is_degraded
    return {
        "mode": "degraded" if degraded else "full",
        "services": services,
    }
