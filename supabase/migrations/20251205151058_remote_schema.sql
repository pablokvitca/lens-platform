-- =====================================================
-- ENUMS
-- =====================================================

CREATE TYPE user_role AS ENUM ('admin', 'facilitator');
CREATE TYPE cohort_status AS ENUM ('active', 'completed', 'cancelled');
CREATE TYPE group_status AS ENUM ('forming', 'active', 'completed', 'merged', 'cancelled');
CREATE TYPE group_user_role AS ENUM ('participant', 'facilitator');
CREATE TYPE group_user_status AS ENUM ('active', 'dropped', 'completed', 'removed');
CREATE TYPE dropout_reason AS ENUM ('time_constraints', 'personal_reasons', 'course_fit', 'unresponsive', 'other');
CREATE TYPE cohort_role AS ENUM ('participant', 'facilitator');
CREATE TYPE grouping_status AS ENUM ('awaiting_grouping', 'grouped', 'ungroupable');
CREATE TYPE rsvp_status AS ENUM ('pending', 'attending', 'not_attending', 'tentative');
CREATE TYPE delivery_method AS ENUM ('email', 'discord_dm', 'discord_channel');
CREATE TYPE delivery_status AS ENUM ('pending', 'delivered', 'failed');

-- =====================================================
-- TABLES
-- =====================================================

-- 1. USERS
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    discord_id TEXT,
    discord_username TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    email_verified_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ,
    timezone TEXT,
    availability_utc TEXT,
    if_needed_availability_utc TEXT,
    availability_last_updated_at TIMESTAMPTZ,
    reminder_preferences JSONB,
    reminder_timing TEXT,
    email_notifications_enabled BOOLEAN DEFAULT true,
    dm_notifications_enabled BOOLEAN DEFAULT true,
    data_sharing_consent BOOLEAN DEFAULT false,
    analytics_opt_in BOOLEAN DEFAULT false,
    public_profile_visible BOOLEAN DEFAULT false,
    show_in_alumni_directory BOOLEAN DEFAULT false,
    tos_accepted_at TIMESTAMPTZ,
    notes TEXT,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- 2. FACILITATORS
CREATE TABLE facilitators (
    facilitator_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    max_active_groups INTEGER DEFAULT 2,
    average_rating REAL,
    rating_count INTEGER DEFAULT 0,
    certified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. ROLES_USERS
CREATE TABLE roles_users (
    role_user_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role user_role,
    granted_at TIMESTAMPTZ,
    granted_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. COURSES
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name TEXT NOT NULL,
    description TEXT,
    duration_days_options INTEGER[],
    is_public BOOLEAN DEFAULT true,
    last_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL
);

-- 5. COHORTS
CREATE TABLE cohorts (
    cohort_id SERIAL PRIMARY KEY,
    cohort_name TEXT,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    cohort_start_date DATE NOT NULL,
    duration_days INTEGER NOT NULL,
    status cohort_status DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. GROUPS
CREATE TABLE groups (
    group_id SERIAL PRIMARY KEY,
    group_name TEXT NOT NULL,
    cohort_id INTEGER NOT NULL REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
    discord_text_channel_id TEXT,
    discord_voice_channel_id TEXT,
    recurring_meeting_time_utc TEXT,
    recurrence_pattern TEXT,
    status group_status DEFAULT 'forming',
    start_date DATE,
    expected_end_date DATE,
    actual_end_date DATE,
    discord_channel_archived_at TIMESTAMPTZ,
    total_messages_in_channel INTEGER,
    last_message_at TIMESTAMPTZ,
    merged_from_groups INTEGER[],
    merged_into_group_id INTEGER REFERENCES groups(group_id) ON DELETE SET NULL,
    max_capacity INTEGER DEFAULT 8,
    min_size_threshold INTEGER DEFAULT 3,
    notes TEXT,
    flags JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL
);

-- 7. GROUPS_USERS
CREATE TABLE groups_users (
    group_user_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    role group_user_role NOT NULL,
    status group_user_status DEFAULT 'active',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    dropout_reason dropout_reason,
    dropout_details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. COURSES_USERS
CREATE TABLE courses_users (
    course_user_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    cohort_id INTEGER REFERENCES cohorts(cohort_id) ON DELETE SET NULL,
    cohort_role cohort_role NOT NULL,
    grouping_status grouping_status DEFAULT 'awaiting_grouping',
    grouping_attempt_count INTEGER DEFAULT 0,
    last_grouping_attempt_at TIMESTAMPTZ,
    is_course_committee_member BOOLEAN DEFAULT false,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. MEETINGS
CREATE TABLE meetings (
    meeting_id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(group_id) ON DELETE CASCADE,
    cohort_id INTEGER REFERENCES cohorts(cohort_id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(course_id) ON DELETE CASCADE,
    scheduled_time_utc TIMESTAMPTZ NOT NULL,
    was_rescheduled BOOLEAN DEFAULT false,
    reschedule_reason TEXT,
    discord_event_id TEXT,
    discord_voice_channel_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. ATTENDANCES
CREATE TABLE attendances (
    attendance_id SERIAL PRIMARY KEY,
    meeting_id INTEGER NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    rsvp_status rsvp_status DEFAULT 'pending',
    rsvp_at TIMESTAMPTZ,
    checked_in_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. REMINDERS_LOG
CREATE TABLE reminders_log (
    reminder_id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    reminder_type TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    delivery_method delivery_method NOT NULL,
    delivery_status delivery_status DEFAULT 'pending',
    delivery_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. REMINDER_RECIPIENTS_LOG
CREATE TABLE reminder_recipients_log (
    reminder_user_id SERIAL PRIMARY KEY,
    reminder_id INTEGER NOT NULL REFERENCES reminders_log(reminder_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    group_id INTEGER REFERENCES groups(group_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. AUTH_CODES
CREATE TABLE auth_codes (
    code_id SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    discord_id TEXT
);

-- =====================================================
-- INDEXES (for better query performance)
-- =====================================================

CREATE INDEX idx_users_discord_id ON users(discord_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_facilitators_user_id ON facilitators(user_id);
CREATE INDEX idx_roles_users_user_id ON roles_users(user_id);
CREATE INDEX idx_cohorts_course_id ON cohorts(course_id);
CREATE INDEX idx_cohorts_start_date ON cohorts(cohort_start_date);
CREATE INDEX idx_groups_cohort_id ON groups(cohort_id);
CREATE INDEX idx_groups_users_user_id ON groups_users(user_id);
CREATE INDEX idx_groups_users_group_id ON groups_users(group_id);
CREATE INDEX idx_courses_users_user_id ON courses_users(user_id);
CREATE INDEX idx_courses_users_course_id ON courses_users(course_id);
CREATE INDEX idx_meetings_group_id ON meetings(group_id);
CREATE INDEX idx_meetings_cohort_id ON meetings(cohort_id);
CREATE INDEX idx_meetings_scheduled_time ON meetings(scheduled_time_utc);
CREATE INDEX idx_attendances_meeting_id ON attendances(meeting_id);
CREATE INDEX idx_attendances_user_id ON attendances(user_id);
CREATE INDEX idx_auth_codes_code ON auth_codes(code);
CREATE INDEX idx_auth_codes_user_id ON auth_codes(user_id);

-- =====================================================
-- UPDATE TRIGGERS (to auto-update updated_at columns)
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_facilitators_updated_at BEFORE UPDATE ON facilitators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_users_updated_at BEFORE UPDATE ON roles_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cohorts_updated_at BEFORE UPDATE ON cohorts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_users_updated_at BEFORE UPDATE ON groups_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_users_updated_at BEFORE UPDATE ON courses_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meetings_updated_at BEFORE UPDATE ON meetings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();