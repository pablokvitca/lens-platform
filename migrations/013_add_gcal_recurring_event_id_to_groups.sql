-- Add recurring calendar event ID to groups table
ALTER TABLE groups ADD COLUMN gcal_recurring_event_id TEXT;
ALTER TABLE groups ADD COLUMN calendar_invite_sent_at TIMESTAMP WITH TIME ZONE;

-- Add comment for documentation
COMMENT ON COLUMN groups.gcal_recurring_event_id IS 'Google Calendar recurring event ID for all meetings in this group';
COMMENT ON COLUMN groups.calendar_invite_sent_at IS 'When the recurring calendar invite was created';
