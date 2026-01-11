"""Tests for calendar invite generation."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.notifications.channels.calendar import create_calendar_invite


class TestCreateCalendarInvite:
    def test_creates_valid_ics(self):
        start = datetime(2026, 1, 15, 14, 0, tzinfo=ZoneInfo("UTC"))
        end = start + timedelta(hours=1)

        ics = create_calendar_invite(
            title="AI Safety Study Group",
            description="Weekly meeting",
            start=start,
            end=end,
            attendee_emails=["alice@example.com"],
            organizer_email="course@example.com",
        )

        assert "BEGIN:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "AI Safety Study Group" in ics
        assert "METHOD:REQUEST" in ics
        assert "ATTENDEE" in ics
        assert "alice@example.com" in ics

    def test_includes_recurrence_rule(self):
        start = datetime(2026, 1, 15, 14, 0, tzinfo=ZoneInfo("UTC"))
        end = start + timedelta(hours=1)

        ics = create_calendar_invite(
            title="Study Group",
            description="Weekly",
            start=start,
            end=end,
            attendee_emails=["alice@example.com"],
            organizer_email="course@example.com",
            recurrence_weeks=8,
        )

        assert "RRULE:FREQ=WEEKLY;COUNT=8" in ics
