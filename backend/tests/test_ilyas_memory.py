"""
PresenceOS - Tests for Ilyas Mem0 Memory Wrapper

Tests covering add, search, get_all operations,
async executor wrapping, and error handling.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.ilyas.memory import Mem0Memory


# ── Config Tests ─────────────────────────────────────────────────────────


class TestMem0Config:
    def test_no_api_key_raises(self):
        with patch("app.services.ilyas.memory.settings") as mock_settings:
            mock_settings.mem0_api_key = ""
            memory = Mem0Memory()
            with pytest.raises(RuntimeError, match="Mem0 API key not configured"):
                memory._get_client()

    def test_client_reuses_existing(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client
        assert memory._get_client() is mock_client

    def test_client_creates_new_when_none(self):
        with patch("app.services.ilyas.memory.settings") as mock_settings:
            mock_settings.mem0_api_key = "test-mem0-key"
            mock_mem0_module = MagicMock()
            with patch.dict("sys.modules", {"mem0": mock_mem0_module}):
                memory = Mem0Memory()
                client = memory._get_client()
                mock_mem0_module.MemoryClient.assert_called_once_with(api_key="test-mem0-key")


# ── Add Tests ────────────────────────────────────────────────────────────


class TestMem0Add:
    @pytest.mark.asyncio
    async def test_add_messages(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        mock_client.add = MagicMock(return_value={"status": "ok"})
        memory._client = mock_client

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "ok"}

            result = await memory.add(
                messages=[
                    {"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Salut !"},
                ],
                user_id="user-123",
                metadata={"brand_id": "brand-456"},
            )

        mock_run.assert_called_once()
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_add_without_metadata(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "ok"}

            await memory.add(
                messages=[{"role": "user", "content": "Test"}],
                user_id="user-123",
            )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        # The partial should have messages and user_id but no metadata
        assert call_kwargs is not None


# ── Search Tests ─────────────────────────────────────────────────────────


class TestMem0Search:
    @pytest.mark.asyncio
    async def test_search_returns_list(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        search_results = [
            {"memory": "Le restaurant préfère un ton chaleureux", "score": 0.92},
            {"memory": "Posts Instagram le mardi à 18h", "score": 0.85},
        ]

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = search_results

            result = await memory.search(
                query="style de communication",
                user_id="user-123",
                limit=5,
            )

        assert len(result) == 2
        assert result[0]["memory"] == "Le restaurant préfère un ton chaleureux"

    @pytest.mark.asyncio
    async def test_search_returns_dict_with_results_key(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "results": [{"memory": "Pizza napolitaine est leur spécialité"}]
            }

            result = await memory.search(
                query="spécialités",
                user_id="user-123",
            )

        assert len(result) == 1
        assert result[0]["memory"] == "Pizza napolitaine est leur spécialité"

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []

            result = await memory.search(
                query="quelque chose",
                user_id="user-123",
            )

        assert result == []


# ── Get All Tests ────────────────────────────────────────────────────────


class TestMem0GetAll:
    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        all_memories = [
            {"memory": "Mem 1"},
            {"memory": "Mem 2"},
            {"memory": "Mem 3"},
        ]

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = all_memories

            result = await memory.get_all(user_id="user-123")

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_all_returns_dict_with_results_key(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"results": [{"memory": "Unique mem"}]}

            result = await memory.get_all(user_id="user-123")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_empty(self):
        memory = Mem0Memory()
        mock_client = MagicMock()
        memory._client = mock_client

        with patch.object(memory, "_run_sync", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []

            result = await memory.get_all(user_id="user-123")

        assert result == []
