"""
PresenceOS - Content Library Service

Manages dishes CRUD with automatic KB rebuilds,
and generates AI proposals from free-text requests or assets.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import Dish, DishCategory
from app.models.media import MediaAsset
from app.models.ai_proposal import AIProposal, ProposalSource, ProposalStatus

logger = structlog.get_logger()


class ContentLibraryService:
    """Content Library: dishes CRUD + AI proposal generation triggers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Dishes CRUD ───────────────────────────────────────────────────────

    async def create_dish(
        self,
        brand_id: str,
        name: str,
        category: str = "plats",
        description: str | None = None,
        price: float | None = None,
        is_featured: bool = False,
        cover_asset_id: str | None = None,
    ) -> Dish:
        """Create a new dish and trigger KB rebuild."""
        # Get next display_order
        stmt = select(func.coalesce(func.max(Dish.display_order), -1)).where(
            Dish.brand_id == brand_id
        )
        result = await self.db.execute(stmt)
        max_order = result.scalar()

        dish = Dish(
            brand_id=brand_id,
            name=name,
            category=category,
            description=description,
            price=price,
            is_featured=is_featured,
            cover_asset_id=cover_asset_id,
            display_order=max_order + 1,
        )
        self.db.add(dish)
        await self.db.commit()
        await self.db.refresh(dish)

        await self._trigger_kb_rebuild(brand_id)

        logger.info("Dish created", dish_id=str(dish.id), name=name, brand_id=brand_id)
        return dish

    async def list_dishes(
        self,
        brand_id: str,
        category: str | None = None,
        featured_only: bool = False,
        available_only: bool = True,
    ) -> list[Dish]:
        """List dishes for a brand with optional filters."""
        stmt = select(Dish).where(Dish.brand_id == brand_id)

        if category:
            stmt = stmt.where(Dish.category == category)
        if featured_only:
            stmt = stmt.where(Dish.is_featured == True)
        if available_only:
            stmt = stmt.where(Dish.is_available == True)

        stmt = stmt.order_by(Dish.display_order, Dish.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_dish(self, dish_id: str) -> Dish | None:
        """Get a single dish by ID."""
        stmt = select(Dish).where(Dish.id == dish_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_dish(
        self,
        dish_id: str,
        **updates: Any,
    ) -> Dish:
        """Update a dish and trigger KB rebuild."""
        stmt = select(Dish).where(Dish.id == dish_id)
        result = await self.db.execute(stmt)
        dish = result.scalar_one_or_none()
        if not dish:
            raise ValueError(f"Dish {dish_id} not found")

        allowed_fields = {
            "name", "category", "description", "price",
            "is_available", "is_featured", "cover_asset_id", "display_order",
        }
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(dish, field, value)

        await self.db.commit()
        await self.db.refresh(dish)

        await self._trigger_kb_rebuild(str(dish.brand_id))

        logger.info("Dish updated", dish_id=dish_id)
        return dish

    async def delete_dish(self, dish_id: str) -> bool:
        """Delete a dish and trigger KB rebuild."""
        stmt = select(Dish).where(Dish.id == dish_id)
        result = await self.db.execute(stmt)
        dish = result.scalar_one_or_none()
        if not dish:
            return False

        brand_id = str(dish.brand_id)
        await self.db.delete(dish)
        await self.db.commit()

        await self._trigger_kb_rebuild(brand_id)

        logger.info("Dish deleted", dish_id=dish_id, brand_id=brand_id)
        return True

    async def import_dishes(
        self,
        brand_id: str,
        dishes_data: list[dict],
    ) -> list[Dish]:
        """Bulk import dishes (e.g., from OCR scan results).

        Returns the list of created Dish objects.
        """
        # Get current max display_order
        stmt = select(func.coalesce(func.max(Dish.display_order), -1)).where(
            Dish.brand_id == brand_id
        )
        result = await self.db.execute(stmt)
        order = result.scalar()

        created = []
        for data in dishes_data:
            order += 1
            dish = Dish(
                brand_id=brand_id,
                name=data["name"],
                category=data.get("category", "autres"),
                description=data.get("description"),
                price=data.get("price"),
                display_order=order,
            )
            self.db.add(dish)
            created.append(dish)

        await self.db.commit()
        for d in created:
            await self.db.refresh(d)

        await self._trigger_kb_rebuild(brand_id)

        logger.info(
            "Dishes imported",
            brand_id=brand_id,
            count=len(created),
        )
        return created

    # ── Free-text Request ─────────────────────────────────────────────────

    async def create_request_proposal(
        self,
        brand_id: str,
        request_text: str,
        content_type: str = "post",
        platform: str = "instagram",
    ) -> AIProposal:
        """Create a proposal from a free-text request.

        The actual generation is done asynchronously via Celery.
        Returns a pending AIProposal.
        """
        proposal = AIProposal(
            brand_id=brand_id,
            proposal_type=content_type,
            platform=platform,
            source=ProposalSource.REQUEST.value,
            source_id=None,
            status=ProposalStatus.PENDING.value,
        )
        self.db.add(proposal)
        await self.db.commit()
        await self.db.refresh(proposal)

        # Dispatch async generation
        from app.workers.content_tasks import generate_proposal_task
        generate_proposal_task.delay(
            str(brand_id),
            "request",
            {"text": request_text, "proposal_id": str(proposal.id)},
        )

        logger.info(
            "Request proposal created",
            proposal_id=str(proposal.id),
            brand_id=brand_id,
        )
        return proposal

    async def create_asset_proposal(
        self,
        brand_id: str,
        asset_id: str,
        content_type: str = "post",
        platform: str = "instagram",
    ) -> AIProposal:
        """Create a proposal from an existing media asset.

        Returns a pending AIProposal.
        """
        # Verify asset exists
        stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        proposal = AIProposal(
            brand_id=brand_id,
            proposal_type=content_type,
            platform=platform,
            source=ProposalSource.ASSET.value,
            source_id=str(asset_id),
            image_url=asset.improved_url or asset.public_url,
            status=ProposalStatus.PENDING.value,
        )
        self.db.add(proposal)
        await self.db.commit()
        await self.db.refresh(proposal)

        # Dispatch async generation
        from app.workers.content_tasks import generate_proposal_task
        generate_proposal_task.delay(
            str(brand_id),
            "asset",
            {
                "asset_id": str(asset_id),
                "proposal_id": str(proposal.id),
                "description": asset.ai_description,
                "label": asset.asset_label,
            },
        )

        logger.info(
            "Asset proposal created",
            proposal_id=str(proposal.id),
            asset_id=asset_id,
        )
        return proposal

    # ── Helpers ────────────────────────────────────────────────────────────

    async def _trigger_kb_rebuild(self, brand_id: str) -> None:
        """Trigger a debounced KB rebuild."""
        try:
            from app.services.knowledge_base_service import KnowledgeBaseService
            kb_service = KnowledgeBaseService(self.db)
            await kb_service.rebuild_debounced(brand_id)
        except Exception as exc:
            logger.warning("KB rebuild trigger failed", error=str(exc))
