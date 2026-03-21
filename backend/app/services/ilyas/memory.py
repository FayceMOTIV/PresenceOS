"""
PresenceOS - Ilyas Conversational Memory (Mem0)

Wraps the sync Mem0 MemoryClient in async-safe calls via run_in_executor.
"""
import asyncio
from functools import partial
from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger()


class Mem0Memory:
    """Async wrapper around the sync Mem0 MemoryClient."""

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            if not settings.mem0_api_key:
                raise RuntimeError("Mem0 API key not configured. Set MEM0_API_KEY.")
            from mem0 import MemoryClient
            self._client = MemoryClient(api_key=settings.mem0_api_key)
        return self._client

    async def _run_sync(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Run a sync Mem0 call in the default executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def add(
        self,
        messages: list[dict[str, str]],
        user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Store conversation messages in Mem0."""
        client = self._get_client()
        kwargs: dict[str, Any] = {"messages": messages, "user_id": user_id}
        if metadata:
            kwargs["metadata"] = metadata
        result = await self._run_sync(client.add, **kwargs)
        logger.debug("Mem0 memory added", user_id=user_id)
        return result

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search relevant memories for a user."""
        client = self._get_client()
        result = await self._run_sync(
            client.search, query=query, user_id=user_id, limit=limit
        )
        memories = result if isinstance(result, list) else result.get("results", [])
        logger.debug("Mem0 search", user_id=user_id, query=query[:50], results=len(memories))
        return memories

    async def get_all(self, user_id: str) -> list[dict[str, Any]]:
        """Get all memories for a user."""
        client = self._get_client()
        result = await self._run_sync(client.get_all, user_id=user_id)
        memories = result if isinstance(result, list) else result.get("results", [])
        return memories

    async def delete(self, memory_id: str) -> bool:
        """Delete a specific memory by its Mem0 ID. Returns True on success."""
        client = self._get_client()
        await self._run_sync(client.delete, memory_id=memory_id)
        logger.debug("Mem0 memory deleted", memory_id=memory_id)
        return True
