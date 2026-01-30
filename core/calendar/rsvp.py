"""Sync RSVP responses from Google Calendar to database."""

import logging
from datetime import datetime, timedelta, timezone

from dateutil.parser import isoparse
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from core.database import get_connection
from core.tables import meetings, attendances, users
from core.enums import RSVPStatus
from .events import get_event_rsvps, get_event_instances

logger = logging.getLogger(__name__)


# Map Google Calendar response status to our RSVPStatus enum
GOOGLE_TO_RSVP_STATUS = {
    "needsAction": RSVPStatus.pending,
    "accepted": RSVPStatus.attending,
    "declined": RSVPStatus.not_attending,
    "tentative": RSVPStatus.tentative,
}


async def sync_meeting_rsvps(meeting_id: int) -> dict[str, int]:
    """
    Sync RSVP statuses from Google Calendar to attendances table.

    Args:
        meeting_id: Database meeting ID

    Returns:
        Count of each status: {"attending": 3, "not_attending": 1, ...}
    """
    async with get_connection() as conn:
        # Get meeting's Google event ID
        result = await conn.execute(
            select(meetings.c.google_calendar_event_id).where(
                meetings.c.meeting_id == meeting_id
            )
        )
        row = result.first()

        if not row or not row.google_calendar_event_id:
            return {}

        # Get RSVPs from Google Calendar API
        google_rsvps = await get_event_rsvps(row.google_calendar_event_id)
        if google_rsvps is None:
            return {}

        counts: dict[str, int] = {}

        for attendee in google_rsvps:
            email = attendee["email"]
            google_status = attendee["responseStatus"]
            our_status = GOOGLE_TO_RSVP_STATUS.get(google_status, RSVPStatus.pending)

            counts[our_status.value] = counts.get(our_status.value, 0) + 1

            # Find user by email
            user_result = await conn.execute(
                select(users.c.user_id).where(users.c.email == email)
            )
            user_row = user_result.first()

            if user_row:
                # Upsert attendance record
                stmt = insert(attendances).values(
                    meeting_id=meeting_id,
                    user_id=user_row.user_id,
                    rsvp_status=our_status,
                    rsvp_at=func.now(),
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="attendances_meeting_user_unique",
                    set_={
                        "rsvp_status": our_status,
                        "rsvp_at": func.now(),
                    },
                )
                await conn.execute(stmt)

        await conn.commit()
        return counts


async def sync_upcoming_meeting_rsvps(days_ahead: int = 7) -> int:
    """
    Sync RSVPs for all meetings in the next N days.

    Call this periodically (e.g., every 6 hours) to keep RSVPs current.

    Returns:
        Number of meetings synced
    """
    async with get_connection() as conn:
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)

        result = await conn.execute(
            select(meetings.c.meeting_id)
            .where(meetings.c.scheduled_at > now)
            .where(meetings.c.scheduled_at < cutoff)
            .where(meetings.c.google_calendar_event_id.isnot(None))
        )

        meeting_ids = [row.meeting_id for row in result]

    # Sync each meeting (outside transaction to avoid long locks)
    for meeting_id in meeting_ids:
        try:
            await sync_meeting_rsvps(meeting_id)
        except Exception as e:
            print(f"Failed to sync RSVPs for meeting {meeting_id}: {e}")

    return len(meeting_ids)


async def sync_group_rsvps_from_recurring(
    group_id: int,
    recurring_event_id: str,
) -> dict[str, int]:
    """
    Sync RSVPs for all meetings in a group from recurring event instances.

    Fetches all instances in ONE API call, then matches each instance
    to a meeting by comparing datetime.

    Diff-based: Only updates attendance records where status actually changed.

    Args:
        group_id: Database group ID
        recurring_event_id: Google Calendar recurring event ID

    Returns:
        {"instances_fetched": N, "synced": N, "skipped": N, "rsvps_updated": N}
    """
    # Fetch all instances in one API call
    instances = await get_event_instances(recurring_event_id)
    if instances is None:
        return {"instances_fetched": 0, "synced": 0, "error": "api_failed"}

    result = {
        "instances_fetched": len(instances),
        "synced": 0,
        "skipped": 0,
        "rsvps_updated": 0,  # Actual DB updates (not no-ops)
    }

    async with get_connection() as conn:
        # Get all meetings for the group
        meetings_result = await conn.execute(
            select(meetings.c.meeting_id, meetings.c.scheduled_at).where(
                meetings.c.group_id == group_id
            )
        )
        meetings_by_time = {
            row["scheduled_at"].replace(tzinfo=timezone.utc): row["meeting_id"]
            for row in meetings_result.mappings()
        }

        # Process each instance
        for instance in instances:
            # Parse instance start time with error handling
            start_str = instance.get("start", {}).get("dateTime")
            if not start_str:
                continue

            try:
                instance_time = isoparse(start_str).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse instance datetime '{start_str}': {e}")
                result["skipped"] += 1
                continue

            # Find matching meeting
            meeting_id = meetings_by_time.get(instance_time)
            if not meeting_id:
                # No matching meeting (time mismatch)
                result["skipped"] += 1
                continue

            # Sync attendee RSVPs for this instance
            for attendee in instance.get("attendees", []):
                email = attendee.get("email", "").lower()
                google_status = attendee.get("responseStatus", "needsAction")
                our_status = GOOGLE_TO_RSVP_STATUS.get(
                    google_status, RSVPStatus.pending
                )

                # Find user by email
                user_result = await conn.execute(
                    select(users.c.user_id).where(users.c.email == email)
                )
                user_row = user_result.first()

                if user_row:
                    # Upsert attendance record - only update if status changed
                    stmt = insert(attendances).values(
                        meeting_id=meeting_id,
                        user_id=user_row.user_id,
                        rsvp_status=our_status,
                        rsvp_at=func.now(),
                    )
                    stmt = stmt.on_conflict_do_update(
                        constraint="attendances_meeting_user_unique",
                        set_={
                            "rsvp_status": our_status,
                            "rsvp_at": func.now(),
                        },
                        # Only update if status actually changed (diff-based)
                        where=(attendances.c.rsvp_status != our_status),
                    )
                    db_result = await conn.execute(stmt)
                    # Track actual updates (rowcount > 0 means insert or update happened)
                    if db_result.rowcount > 0:
                        result["rsvps_updated"] += 1

            result["synced"] += 1

        await conn.commit()

    return result
