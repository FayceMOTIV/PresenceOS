"""
PresenceOS — Onboarding Service (Sprint B2)

Manages onboarding state in PostgreSQL.
Coordinates with the existing OnboardingAgent for AI extraction.
"""
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding_state import OnboardingState

logger = logging.getLogger(__name__)


class OnboardingService:
    """Manages onboarding state persistence in PostgreSQL."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_state(self, brand_id: uuid.UUID) -> OnboardingState | None:
        """Get onboarding state for a brand."""
        result = await self._db.execute(
            select(OnboardingState).where(OnboardingState.brand_id == brand_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_state(self, brand_id: uuid.UUID) -> OnboardingState:
        """Get existing or create new onboarding state."""
        state = await self.get_state(brand_id)
        if state:
            return state

        state = OnboardingState(
            brand_id=brand_id,
            current_step=0,
            total_steps=8,
            is_complete=False,
            dna_snapshot={},
            raw_answers={},
        )
        self._db.add(state)
        await self._db.commit()
        await self._db.refresh(state)
        return state

    async def advance_step(
        self,
        brand_id: uuid.UUID,
        step: int,
        answer: str,
        extracted: dict[str, Any],
        dna_snapshot: dict[str, Any],
    ) -> OnboardingState:
        """Record an answer and advance the step."""
        state = await self.get_or_create_state(brand_id)

        raw = dict(state.raw_answers)
        raw[str(step)] = answer
        state.raw_answers = raw

        dna = dict(state.dna_snapshot)
        dna.update({k: v for k, v in extracted.items() if v})
        state.dna_snapshot = dna

        next_step = step + 1
        state.current_step = next_step

        if next_step >= state.total_steps:
            state.is_complete = True
            state.dna_snapshot = dna_snapshot

            # Init Mem0 conversational memory with the completed DNA
            try:
                from app.services.mem0_service import init_mem0_for_brand

                brand_name = dna_snapshot.get("business_name", "")
                scrape_data = {}
                if state.website_url:
                    scrape_data["website_url"] = state.website_url

                await init_mem0_for_brand(
                    brand_id=str(brand_id),
                    brand_name=brand_name,
                    dna=dna_snapshot,
                    scrape_data=scrape_data if scrape_data else None,
                )
            except Exception as exc:
                logger.error(
                    "Mem0 init failed during onboarding completion brand=%s: %s",
                    brand_id, exc,
                )
                # Never crash the onboarding flow if Mem0 fails

        await self._db.commit()
        await self._db.refresh(state)
        return state

    async def set_scrape_result(
        self,
        brand_id: uuid.UUID,
        website_url: str,
        scrape_status: str,
        dna_partial: dict[str, Any] | None = None,
    ) -> OnboardingState:
        """Record website scrape result."""
        state = await self.get_or_create_state(brand_id)
        state.website_url = website_url
        state.scrape_status = scrape_status

        if dna_partial:
            dna = dict(state.dna_snapshot)
            dna.update(dna_partial)
            state.dna_snapshot = dna

        await self._db.commit()
        await self._db.refresh(state)
        return state

    async def reset(self, brand_id: uuid.UUID) -> OnboardingState:
        """Reset onboarding state for a brand (re-onboard)."""
        state = await self.get_state(brand_id)
        if not state:
            return await self.get_or_create_state(brand_id)

        state.current_step = 0
        state.is_complete = False
        state.dna_snapshot = {}
        state.raw_answers = {}
        state.scrape_status = None

        await self._db.commit()
        await self._db.refresh(state)
        return state
