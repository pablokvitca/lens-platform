"""Tests for group joining business logic (TDD)."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from core.group_joining import _calculate_next_meeting


class TestCalculateNextMeeting:
    """Test meeting time calculation."""

    def test_returns_first_meeting_if_in_future(self):
        """Should return first_meeting_at if it's in the future."""
        future = datetime.now(timezone.utc) + timedelta(days=7)
        result = _calculate_next_meeting("Wednesday 15:00", future)
        assert result == future.isoformat()

    def test_returns_none_for_empty_recurring_time(self):
        """Should return None if no recurring time provided."""
        result = _calculate_next_meeting("", None)
        assert result is None

    def test_returns_none_for_invalid_format(self):
        """Should return None for invalid recurring time format."""
        result = _calculate_next_meeting("invalid", None)
        assert result is None

    def test_calculates_next_wednesday(self):
        """Should calculate next occurrence from recurring time."""
        result = _calculate_next_meeting("Wednesday 15:00", None)
        assert result is not None
        parsed = datetime.fromisoformat(result)
        assert parsed.weekday() == 2  # Wednesday
        assert parsed.hour == 15
        assert parsed.minute == 0
