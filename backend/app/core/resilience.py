"""
PresenceOS - Service Registry & Resilience Layer

Tracks the health status of external dependencies (PostgreSQL, Redis).
Transforms hard dependencies into soft dependencies following the
AWS Well-Architected Reliability Pillar (REL05-BP01).
"""
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ServiceRegistry:
    """
    Singleton that maintains the status of all external dependencies.
    Allows the app to adapt its behavior based on what's available.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services: Dict[str, ServiceStatus] = {}
            cls._instance._last_check: Dict[str, datetime] = {}
            cls._instance._check_interval = timedelta(seconds=30)
        return cls._instance

    def register(self, name: str, status: ServiceStatus = ServiceStatus.UNAVAILABLE):
        self._services[name] = status
        self._last_check[name] = datetime.utcnow()
        logger.info(f"Service '{name}' registered as {status.value}")

    def update(self, name: str, status: ServiceStatus):
        old = self._services.get(name)
        self._services[name] = status
        self._last_check[name] = datetime.utcnow()
        if old != status:
            logger.info(f"Service '{name}' status: {old.value if old else 'unregistered'} -> {status.value}")

    def is_available(self, name: str) -> bool:
        return self._services.get(name) == ServiceStatus.HEALTHY

    def get_status(self) -> Dict[str, Any]:
        return {
            name: {
                "status": status.value,
                "last_check": (
                    self._last_check[name].isoformat()
                    if name in self._last_check
                    else "never"
                ),
            }
            for name, status in self._services.items()
        }

    @property
    def is_degraded(self) -> bool:
        return not self.is_available("postgresql")


registry = ServiceRegistry()
