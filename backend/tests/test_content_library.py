"""
PresenceOS - Content Library Service Tests

Tests for dish CRUD, asset linking, KB rebuild triggers.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.dish import Dish, DishCategory
from app.models.ai_proposal import AIProposal, ProposalSource, ProposalStatus
from app.services.content_library import ContentLibraryService


# ── Mock DB Session Builder ──────────────────────────────────────────────


def _mock_db():
    """Create a mock async DB session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    return db


def _mock_dish(
    name="Entrecôte",
    category="plats",
    price=24.90,
    brand_id=None,
    is_featured=False,
    is_available=True,
) -> Dish:
    dish = MagicMock(spec=Dish)
    dish.id = uuid.uuid4()
    dish.brand_id = brand_id or uuid.uuid4()
    dish.name = name
    dish.category = category
    dish.price = price
    dish.is_featured = is_featured
    dish.is_available = is_available
    dish.description = "Grillée sauce béarnaise"
    dish.cover_asset_id = None
    dish.ai_post_count = 0
    dish.last_posted_at = None
    dish.display_order = 0
    dish.created_at = MagicMock()
    dish.updated_at = MagicMock()
    return dish


# ── Dish CRUD Tests ──────────────────────────────────────────────────────


class TestDishCreate:
    """Tests for dish creation."""

    @pytest.mark.asyncio
    async def test_create_dish_basic(self):
        db = _mock_db()
        # Mock max display_order query
        mock_result = MagicMock()
        mock_result.scalar.return_value = -1
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)

        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            dish = await service.create_dish(
                brand_id=str(uuid.uuid4()),
                name="Tartare de boeuf",
                category="plats",
                price=18.50,
            )

        db.add.assert_called_once()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_dish_featured(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            dish = await service.create_dish(
                brand_id=str(uuid.uuid4()),
                name="Foie Gras",
                category="entrees",
                is_featured=True,
            )

        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dish_increments_display_order(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            await service.create_dish(
                brand_id=str(uuid.uuid4()),
                name="Crème brûlée",
                category="desserts",
            )

        # The added dish should have display_order = 6
        call_args = db.add.call_args[0][0]
        assert call_args.display_order == 6


class TestDishUpdate:
    """Tests for dish update."""

    @pytest.mark.asyncio
    async def test_update_dish_name(self):
        db = _mock_db()
        dish = _mock_dish(name="Old Name")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dish
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            result = await service.update_dish(str(dish.id), name="New Name")

        assert dish.name == "New Name"
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_dish_not_found(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with pytest.raises(ValueError, match="not found"):
            await service.update_dish(str(uuid.uuid4()), name="X")

    @pytest.mark.asyncio
    async def test_update_dish_ignores_unknown_fields(self):
        db = _mock_db()
        dish = _mock_dish()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dish
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            await service.update_dish(str(dish.id), unknown_field="bad")

        # Should not crash, just ignore unknown fields


class TestDishDelete:
    """Tests for dish deletion."""

    @pytest.mark.asyncio
    async def test_delete_dish_success(self):
        db = _mock_db()
        dish = _mock_dish()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dish
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            result = await service.delete_dish(str(dish.id))

        assert result is True
        db.delete.assert_called_once()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_delete_dish_not_found(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        result = await service.delete_dish(str(uuid.uuid4()))
        assert result is False


class TestDishImport:
    """Tests for bulk dish import."""

    @pytest.mark.asyncio
    async def test_import_dishes_bulk(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        dishes_data = [
            {"name": "Soupe", "category": "entrees", "price": 8.50},
            {"name": "Steak", "category": "plats", "price": 22.00},
            {"name": "Tiramisu", "category": "desserts"},
        ]

        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock):
            result = await service.import_dishes(str(uuid.uuid4()), dishes_data)

        assert db.add.call_count == 3
        db.commit.assert_called()


class TestKBRebuildTrigger:
    """Tests for KB rebuild trigger on CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_triggers_kb_rebuild(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar.return_value = -1
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock) as mock_rebuild:
            await service.create_dish(
                brand_id=str(uuid.uuid4()),
                name="Test",
                category="plats",
            )
            mock_rebuild.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_triggers_kb_rebuild(self):
        db = _mock_db()
        dish = _mock_dish()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = dish
        db.execute = AsyncMock(return_value=mock_result)

        service = ContentLibraryService(db)
        with patch.object(service, "_trigger_kb_rebuild", new_callable=AsyncMock) as mock_rebuild:
            await service.delete_dish(str(dish.id))
            mock_rebuild.assert_called_once()
