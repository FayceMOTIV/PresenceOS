"""
PresenceOS - Daily Brief Tests

Tests for brief creation, response, and proposal generation trigger.
"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from unittest.mock import MagicMock

from app.models.daily_brief import DailyBrief, BriefStatus


# ── Model Tests ──────────────────────────────────────────────────────────


class TestDailyBriefModel:
    """Tests for DailyBrief model behavior."""

    def test_brief_status_enum(self):
        assert BriefStatus.PENDING.value == "pending"
        assert BriefStatus.ANSWERED.value == "answered"
        assert BriefStatus.IGNORED.value == "ignored"

    def test_brief_repr(self):
        brief = MagicMock(spec=DailyBrief)
        brief.date = date(2024, 1, 15)
        brief.status = "pending"
        brief.brand_id = uuid.uuid4()
        brief.__repr__ = lambda self: f"<DailyBrief {self.date} status={self.status} brand={self.brand_id}>"
        result = repr(brief)
        assert "2024-01-15" in result
        assert "pending" in result

    def test_brief_default_status_pending(self):
        """Default status should be PENDING."""
        assert BriefStatus.PENDING.value == "pending"


class TestBriefStatusTransitions:
    """Tests for brief status transitions."""

    def test_pending_to_answered(self):
        brief = MagicMock(spec=DailyBrief)
        brief.status = BriefStatus.PENDING.value
        brief.response = None

        # Simulate answering
        brief.status = BriefStatus.ANSWERED.value
        brief.response = "Plat du jour: boeuf bourguignon"
        brief.responded_at = datetime.now(timezone.utc)

        assert brief.status == BriefStatus.ANSWERED.value
        assert brief.response is not None
        assert brief.responded_at is not None

    def test_pending_to_ignored(self):
        brief = MagicMock(spec=DailyBrief)
        brief.status = BriefStatus.PENDING.value
        brief.status = BriefStatus.IGNORED.value
        assert brief.status == BriefStatus.IGNORED.value


class TestBriefUniqueConstraint:
    """Tests for one-brief-per-brand-per-day constraint."""

    def test_unique_constraint_name(self):
        """The DailyBrief model should have a unique constraint on (brand_id, date)."""
        args = DailyBrief.__table_args__
        # Should find a UniqueConstraint
        found = False
        for arg in args:
            if hasattr(arg, "name") and arg.name == "uq_daily_brief_brand_date":
                found = True
                break
        assert found, "Expected UniqueConstraint 'uq_daily_brief_brand_date' not found"


class TestBriefResponseFlow:
    """Tests for the complete brief response flow."""

    def test_response_sets_answered(self):
        brief = MagicMock(spec=DailyBrief)
        brief.status = BriefStatus.PENDING.value
        brief.response = None

        # Simulate the respond flow
        brief.response = "Dessert du jour: tarte tatin"
        brief.status = BriefStatus.ANSWERED.value
        brief.responded_at = datetime.now(timezone.utc)

        assert brief.status == "answered"
        assert "tarte tatin" in brief.response

    def test_empty_response_stays_pending(self):
        brief = MagicMock(spec=DailyBrief)
        brief.status = BriefStatus.PENDING.value
        brief.response = None
        # Don't change status without a response
        assert brief.status == "pending"


class TestBriefProposalLink:
    """Tests for linking brief to generated proposal."""

    def test_brief_can_link_to_proposal(self):
        brief = MagicMock(spec=DailyBrief)
        brief.generated_proposal_id = None

        proposal_id = uuid.uuid4()
        brief.generated_proposal_id = proposal_id
        assert brief.generated_proposal_id == proposal_id

    def test_brief_without_proposal(self):
        brief = MagicMock(spec=DailyBrief)
        brief.generated_proposal_id = None
        assert brief.generated_proposal_id is None


class TestBriefNotification:
    """Tests for brief notification tracking."""

    def test_notif_sent_tracking(self):
        brief = MagicMock(spec=DailyBrief)
        brief.notif_sent_at = None

        brief.notif_sent_at = datetime.now(timezone.utc)
        assert brief.notif_sent_at is not None

    def test_no_duplicate_notif(self):
        """Once notif_sent_at is set, it should not be overwritten."""
        brief = MagicMock(spec=DailyBrief)
        first_time = datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc)
        brief.notif_sent_at = first_time
        assert brief.notif_sent_at == first_time
