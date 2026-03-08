"""
PresenceOS — Onboarding Service Tests (Sprint B2)

Tests for OnboardingService CRUD operations.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.onboarding_service import OnboardingService
from app.models.onboarding_state import OnboardingState


def _mock_db(existing_state=None):
    """Create mock AsyncSession."""
    db = AsyncMock()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing_state

    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    return db


class TestOnboardingServiceGetState:

    @pytest.mark.asyncio
    async def test_get_state_returns_none_when_not_found(self):
        db = _mock_db(existing_state=None)
        svc = OnboardingService(db)
        result = await svc.get_state(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_state_returns_existing(self):
        state = MagicMock(spec=OnboardingState)
        state.brand_id = uuid.uuid4()
        state.current_step = 3
        state.is_complete = False

        db = _mock_db(existing_state=state)
        svc = OnboardingService(db)
        result = await svc.get_state(state.brand_id)
        assert result is state


class TestOnboardingServiceGetOrCreate:

    @pytest.mark.asyncio
    async def test_creates_new_state_when_not_found(self):
        db = _mock_db(existing_state=None)
        svc = OnboardingService(db)
        brand_id = uuid.uuid4()
        result = await svc.get_or_create_state(brand_id)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_existing_state(self):
        state = MagicMock(spec=OnboardingState)
        state.brand_id = uuid.uuid4()

        db = _mock_db(existing_state=state)
        svc = OnboardingService(db)
        result = await svc.get_or_create_state(state.brand_id)
        assert result is state
        db.add.assert_not_called()


class TestOnboardingServiceAdvanceStep:

    @pytest.mark.asyncio
    async def test_advance_step_updates_state(self):
        state = MagicMock(spec=OnboardingState)
        state.brand_id = uuid.uuid4()
        state.current_step = 2
        state.total_steps = 8
        state.raw_answers = {}
        state.dna_snapshot = {}
        state.is_complete = False

        db = _mock_db(existing_state=state)
        svc = OnboardingService(db)

        await svc.advance_step(
            brand_id=state.brand_id,
            step=2,
            answer="Le Family's",
            extracted={"business_name": "Le Family's"},
            dna_snapshot={"business_name": "Le Family's"},
        )

        assert state.current_step == 3
        assert state.is_complete is False
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_advance_to_last_step_marks_complete(self):
        state = MagicMock(spec=OnboardingState)
        state.brand_id = uuid.uuid4()
        state.current_step = 7
        state.total_steps = 8
        state.raw_answers = {}
        state.dna_snapshot = {}
        state.is_complete = False

        db = _mock_db(existing_state=state)
        svc = OnboardingService(db)

        await svc.advance_step(
            brand_id=state.brand_id,
            step=7,
            answer="Couscous, Tajine",
            extracted={"signature_dishes": ["Couscous", "Tajine"]},
            dna_snapshot={"business_name": "Le Family's", "signature_dishes": ["Couscous"]},
        )

        assert state.current_step == 8
        assert state.is_complete is True


class TestOnboardingServiceScrape:

    @pytest.mark.asyncio
    async def test_set_scrape_result_success(self):
        state = MagicMock(spec=OnboardingState)
        state.brand_id = uuid.uuid4()
        state.website_url = None
        state.scrape_status = None
        state.dna_snapshot = {}

        db = _mock_db(existing_state=state)
        svc = OnboardingService(db)

        await svc.set_scrape_result(
            brand_id=state.brand_id,
            website_url="https://lefamilys.fr",
            scrape_status="success",
            dna_partial={"business_name": "Le Family's", "city": "Lyon"},
        )

        assert state.website_url == "https://lefamilys.fr"
        assert state.scrape_status == "success"
        db.commit.assert_called_once()


class TestOnboardingServiceReset:

    @pytest.mark.asyncio
    async def test_reset_clears_state(self):
        state = MagicMock(spec=OnboardingState)
        state.brand_id = uuid.uuid4()
        state.current_step = 5
        state.is_complete = True
        state.dna_snapshot = {"business_name": "Test"}
        state.raw_answers = {"0": "Test answer"}

        db = _mock_db(existing_state=state)
        svc = OnboardingService(db)

        await svc.reset(state.brand_id)

        assert state.current_step == 0
        assert state.is_complete is False
        assert state.dna_snapshot == {}
        assert state.raw_answers == {}
        db.commit.assert_called_once()
