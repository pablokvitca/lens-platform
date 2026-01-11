"""Calendar invite generation using iCalendar format."""

from datetime import datetime, timezone
from uuid import uuid4

from icalendar import Calendar, Event, vCalAddress, vText


def create_calendar_invite(
    title: str,
    description: str,
    start: datetime,
    end: datetime,
    attendee_emails: list[str],
    organizer_email: str,
    location: str | None = None,
    recurrence_weeks: int | None = None,
) -> str:
    """
    Create an iCalendar invite string (iTIP format).

    Args:
        title: Event title
        description: Event description
        start: Start datetime (must be timezone-aware)
        end: End datetime (must be timezone-aware)
        attendee_emails: List of attendee email addresses
        organizer_email: Organizer's email address
        location: Optional location string
        recurrence_weeks: If set, creates weekly recurring event for N weeks

    Returns:
        iCalendar string with METHOD:REQUEST for invite
    """
    cal = Calendar()
    cal.add("prodid", "-//AI Safety Course//aisafetycourse.com//")
    cal.add("version", "2.0")
    cal.add("method", "REQUEST")  # This makes it an invite, not just an event

    event = Event()
    event.add("uid", f"{uuid4()}@aisafetycourse.com")
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("summary", title)
    event.add("description", description)

    if location:
        event.add("location", location)

    # Add recurrence rule if specified
    if recurrence_weeks:
        event.add("rrule", {"freq": "weekly", "count": recurrence_weeks})

    # Add organizer
    organizer = vCalAddress(f"mailto:{organizer_email}")
    organizer.params["cn"] = vText("AI Safety Course")
    organizer.params["role"] = vText("CHAIR")
    event.add("organizer", organizer)

    # Add attendees
    for email in attendee_emails:
        attendee = vCalAddress(f"mailto:{email}")
        attendee.params["cn"] = vText(email.split("@")[0])
        attendee.params["role"] = vText("REQ-PARTICIPANT")
        attendee.params["rsvp"] = vText("TRUE")
        event.add("attendee", attendee, encode=0)

    cal.add_component(event)
    return cal.to_ical().decode("utf-8")
