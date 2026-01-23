"""Tests for group joining business logic (TDD)."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from core.group_joining import (
    _calculate_next_meeting,
    get_user_current_group,
    assign_group_badge,
    get_joinable_groups,
)


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


class TestGetUserCurrentGroup:
    """Test getting user's current group."""

    @pytest.mark.asyncio
    async def test_returns_none_when_user_has_no_group(self):
        """Should return None if user is not in any group for the cohort."""
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        mock_conn.execute = AsyncMock(return_value=mock_result)

        result = await get_user_current_group(mock_conn, user_id=1, cohort_id=10)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_group_when_user_is_member(self):
        """Should return group info when user is an active member."""
        mock_conn = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "group_id": 5,
            "group_name": "Test Group",
            "recurring_meeting_time_utc": "Wednesday 15:00",
            "group_user_id": 100,
            "role": "participant",
        }
        mock_conn.execute = AsyncMock(return_value=mock_result)

        result = await get_user_current_group(mock_conn, user_id=1, cohort_id=10)

        assert result is not None
        assert result["group_id"] == 5
        assert result["group_name"] == "Test Group"


class TestAssignGroupBadge:
    """Test badge assignment logic."""

    def test_assigns_best_size_for_3_members(self):
        """Groups with 3 members get best_size badge."""
        assert assign_group_badge(3) == "best_size"

    def test_assigns_best_size_for_4_members(self):
        """Groups with 4 members get best_size badge."""
        assert assign_group_badge(4) == "best_size"

    def test_no_badge_for_2_members(self):
        """Groups with 2 members get no badge."""
        assert assign_group_badge(2) is None

    def test_no_badge_for_5_members(self):
        """Groups with 5 members get no badge."""
        assert assign_group_badge(5) is None

    def test_no_badge_for_0_members(self):
        """Empty groups get no badge."""
        assert assign_group_badge(0) is None


class TestGetJoinableGroups:
    """Test group listing and filtering."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_cohort_with_no_groups(self):
        """Should return empty list if cohort has no groups."""
        mock_conn = AsyncMock()

        # First call: get_user_current_group returns None
        # Second call: main query returns no rows
        mock_result_empty = MagicMock()
        mock_result_empty.mappings.return_value.first.return_value = None
        mock_result_empty.mappings.return_value = []

        mock_conn.execute = AsyncMock(return_value=mock_result_empty)

        result = await get_joinable_groups(mock_conn, cohort_id=1, user_id=None)

        assert result == []

    @pytest.mark.asyncio
    async def test_adds_badge_to_groups_with_3_to_4_members(self):
        """Groups with 3-4 members should get best_size badge."""
        mock_conn = AsyncMock()

        # Mock query results
        mock_groups = MagicMock()
        mock_groups.mappings.return_value = [
            {
                "group_id": 1,
                "group_name": "Group A",
                "recurring_meeting_time_utc": "Wednesday 15:00",
                "status": "active",
                "member_count": 3,
                "first_meeting_at": datetime.now(timezone.utc) + timedelta(days=7),
            },
            {
                "group_id": 2,
                "group_name": "Group B",
                "recurring_meeting_time_utc": "Thursday 16:00",
                "status": "active",
                "member_count": 5,
                "first_meeting_at": datetime.now(timezone.utc) + timedelta(days=7),
            },
        ]

        mock_conn.execute = AsyncMock(return_value=mock_groups)

        result = await get_joinable_groups(mock_conn, cohort_id=1, user_id=None)

        assert len(result) == 2
        assert result[0]["badge"] == "best_size"  # 3 members
        assert result[1]["badge"] is None  # 5 members

    @pytest.mark.asyncio
    async def test_marks_current_group_with_is_current_flag(self):
        """User's current group should have is_current=True."""
        mock_conn = AsyncMock()

        # First call returns user's current group
        mock_current = MagicMock()
        mock_current.mappings.return_value.first.return_value = {"group_id": 1}

        # Second call returns groups list
        mock_groups = MagicMock()
        mock_groups.mappings.return_value = [
            {
                "group_id": 1,
                "group_name": "Current Group",
                "recurring_meeting_time_utc": "Wednesday 15:00",
                "status": "active",
                "member_count": 4,
                "first_meeting_at": datetime.now(timezone.utc) + timedelta(days=7),
            },
            {
                "group_id": 2,
                "group_name": "Other Group",
                "recurring_meeting_time_utc": "Thursday 16:00",
                "status": "active",
                "member_count": 4,
                "first_meeting_at": datetime.now(timezone.utc) + timedelta(days=7),
            },
        ]

        mock_conn.execute = AsyncMock(side_effect=[mock_current, mock_groups])

        result = await get_joinable_groups(mock_conn, cohort_id=1, user_id=99)

        assert result[0]["is_current"] is True
        assert result[1]["is_current"] is False
