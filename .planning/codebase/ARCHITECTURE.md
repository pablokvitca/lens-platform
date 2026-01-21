# Architecture

**Analysis Date:** 2026-01-21

## Pattern Overview

**Overall:** Unified backend with layered adapter pattern

**Key Characteristics:**
- One Python process runs FastAPI + Discord bot as peer services in the same asyncio event loop
- Three-layer architecture: platform-agnostic core, adapter layer (FastAPI + Discord), client layer (web + Discord native)
- Clear separation between adapters - FastAPI and Discord layers never import from each other
- Asynchronous throughout using asyncio and SQLAlchemy async

## Layers

**Layer 1: Core (`core/`)**
- Purpose: Platform-agnostic business logic with no framework dependencies
- Location: `core/`
- Contains: Scheduling algorithm, user management, auth flows, notifications, calendar integration, content fetching
- Depends on: SQLAlchemy async, httpx, external APIs (Discord, Google Calendar, SendGrid, LiteLLM)
- Used by: Both FastAPI routes and Discord cogs

**Layer 2a: Discord Adapter (`discord_bot/`)**
- Purpose: Discord UI/event handling; delegates to core business logic
- Location: `discord_bot/`
- Contains: Cogs (thin command handlers), Discord bot initialization
- Depends on: Core, discord.py
- Used by: Discord clients via WebSocket

**Layer 2b: FastAPI (`web_api/`)**
- Purpose: HTTP API for web frontend; delegates to core business logic
- Location: `web_api/`
- Contains: RESTful routes for auth, users, modules, facilitators, cohorts, courses, content
- Depends on: Core, FastAPI
- Used by: React frontend via HTTP/REST

**Layer 3a: Discord Client**
- Purpose: Discord native UI
- Location: External (Discord platform)
- Channels: Slash commands, buttons, selects, embeds, DMs

**Layer 3b: React Frontend (`web_frontend/`)**
- Purpose: Web-based UI for enrollment, course viewing, scheduling
- Location: `web_frontend/src/`
- Contains: Vike pages, React components, hooks, API client functions
- Depends on: Web API endpoints, TypeScript, React 19, Tailwind CSS v4
- Used by: Browsers via HTTP/HTML/JS

## Data Flow

**User Authentication (Discord OAuth):**
1. User clicks login in React frontend
2. Frontend redirects to `/auth/discord` (FastAPI)
3. FastAPI redirects to Discord OAuth endpoint
4. User authorizes in Discord
5. Discord redirects to `/auth/discord/callback` (FastAPI)
6. FastAPI exchanges code for access token via Discord API
7. FastAPI fetches user info, creates/updates in database
8. FastAPI creates JWT token, sets session cookie
9. Frontend receives cookie, can access authenticated endpoints

**User Authentication (Discord Bot Auth Code Flow):**
1. User types `/signup` in Discord
2. Discord bot calls `create_auth_code()` (core)
3. Core creates row in `auth_codes` table with 10-minute TTL
4. Bot sends URL with code to user
5. User clicks link → browser navigates to `/auth/code?code=X` (FastAPI)
6. FastAPI validates code (exists, not used, not expired)
7. FastAPI marks code as used, creates JWT, sets cookie
8. User is now authenticated in web

**Cohort Scheduling:**
1. Admin runs `/schedule` in Discord (Discord cog)
2. Cog calls `schedule_cohort()` (core)
3. Core fetches signups from database (users + availability)
4. Core runs stochastic greedy scheduling algorithm (1000 iterations)
5. Core persists groups to database
6. Cog retrieves groups, creates Discord channels/events for each
7. Cog sends group assignment notifications via `notify_group_assigned()` (core)

**Meeting RSVP Sync (Periodic Job):**
1. Scheduler runs `sync_upcoming_meeting_rsvps()` every 6 hours (core)
2. Core fetches upcoming meetings from database
3. Core queries Google Calendar API for RSVP status
4. Core updates RSVP records in database
5. Notifications dispatched to users if status changes

**Multi-Channel Notifications:**
1. Code calls `notify_welcome()` or other notification action (core)
2. Notification action calls `send_notification(user_id, message_type, context)` (core/notifications)
3. Dispatcher routes to appropriate channels:
   - Email: Formats template, sends via SendGrid API
   - Discord DM: Routes to Discord bot, sends as DM
   - Discord mention: Routes to bot, sends as channel mention
4. Scheduler can delay notifications for later delivery

**Educational Module Access:**
1. User navigates to `/course/:id` in React frontend
2. Frontend fetches module metadata via `/api/modules/:id` (FastAPI)
3. FastAPI returns module structure + LLM chat session ID
4. Frontend renders markdown content (pre-fetched from GitHub)
5. User opens chat → frontend sends message to `/api/modules/:id/chat` (FastAPI)
6. FastAPI routes to `core/modules/chat.py` which calls LiteLLM for response
7. Response stored in session and returned to frontend

## State Management

**Persistent State:**
- User profiles, availability, enrollments: PostgreSQL via SQLAlchemy
- Scheduling results: Groups, group memberships, meeting times in database
- Auth codes: Temporary codes in auth_codes table with TTL
- Chat transcripts: Stored in transcripts table, keyed by session_id

**Transient State:**
- OAuth states: In-memory dict in `web_api/routes/auth.py` with 10-minute TTL
- Bot ready status: Checked via `bot.is_ready()` boolean
- Scheduler jobs: Managed by APScheduler, periodic tasks

## Key Abstractions

**Person (dataclass in `core/scheduling.py`):**
- Purpose: Represents a user for scheduling with availability
- Fields: id, name, intervals (list of minute tuples), if_needed_intervals, timezone
- Pattern: Input to scheduling algorithm, converted from database signup records

**Group (from cohort_scheduler package):**
- Purpose: Represents a scheduled cohort with assigned users
- Contains: group_id, name, people list, facilitator_id, selected_time
- Pattern: Output of scheduling algorithm, persisted to database

**CohortSchedulingResult (dataclass in `core/scheduling.py`):**
- Purpose: Encapsulates result of scheduling operation
- Fields: cohort_id, cohort_name, groups_created, users_grouped, users_ungroupable, groups list, warnings, ungroupable_details
- Pattern: Returned by `schedule_cohort()`, used by Discord cog to create channels

**Notification Context (dicts in `core/notifications/`):**
- Purpose: Pass structured data to notification templates
- Pattern: `notify_group_assigned(user_id, cohort_name, group_name, meeting_time, ...)` builds context dict
- Templates render context as emails (Jinja2) or Discord messages (format strings)

## Entry Points

**HTTP Server (`main.py`)**
- Location: `/Users/luca/dev/ai-safety-course-platform/main.py`
- Triggers: `python main.py [--dev] [--no-bot] [--port PORT]`
- Responsibilities:
  - Parse CLI flags early to set DEV_MODE before importing auth
  - Initialize Sentry for error tracking
  - Check database connection
  - Initialize content cache from GitHub
  - Start APScheduler for periodic jobs
  - Create FastAPI app with CORS middleware
  - Mount API routes from `web_api/routes/`
  - Mount static files (frontend build)
  - Serve SPA with catchall routing
  - Lifespan context: start Discord bot, initialize scheduler, graceful shutdown

**Discord Bot (`discord_bot/main.py`)**
- Location: `discord_bot/main.py`
- Triggers: Loaded as cog during FastAPI startup
- Responsibilities:
  - Create Bot instance with intents (message_content, voice_states, members, presences)
  - Load cogs on_ready event
  - Sync slash commands (manual via !sync)
  - Handle global error handler for app commands
  - Run in background task alongside FastAPI in same event loop

**FastAPI Routes**
- Auth router (`web_api/routes/auth.py`): Discord OAuth, auth code validation, session management
- Users router (`web_api/routes/users.py`): User profile endpoints
- Modules router (`web_api/routes/modules.py`): Module list, module metadata
- Module router (`web_api/routes/module.py`): Single module content, chat
- Cohorts router (`web_api/routes/cohorts.py`): Cohort queries
- Courses router (`web_api/routes/courses.py`): Course list, course details
- Content router (`web_api/routes/content.py`): Educational content from GitHub
- Facilitator router (`web_api/routes/facilitator.py`): Facilitator-specific endpoints
- Speech router (`web_api/routes/speech.py`): Text-to-speech

**React Frontend (`web_frontend/src/pages/`)**
- Location: `web_frontend/src/pages/`
- Channels: Vike file-based routing
- Key pages:
  - `index/+Page.tsx`: Landing/home
  - `auth/+Page.tsx`: Auth callback handler
  - `enroll/+Page.tsx`: Enrollment wizard
  - `course/+Page.tsx`: Course browser
  - `module/@id/+Page.tsx`: Single module viewer
  - `availability/+Page.tsx`: Availability selection
  - `facilitator/+Page.tsx`: Facilitator dashboard
- Pattern: Each page can have `+Page.tsx` (component), `+data.ts` (data loading), `+Head.tsx` (metadata)

## Error Handling

**Strategy:** Try-catch at adapter boundaries, validation at core layer

**Patterns:**

**FastAPI Route Level** (in `web_api/routes/*.py`):
```python
# Immediate HTTP exceptions for invalid input
raise HTTPException(status_code=400, detail="Invalid timezone")

# Try/except for unexpected errors
try:
    result = await some_core_function()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception:
    raise HTTPException(status_code=500, detail="Internal error")
```

**Core Layer** (in `core/*.py`):
```python
# Raise exceptions for business logic violations
if not availability:
    raise ValueError("User must have at least one availability slot")

# Return error tuples for non-fatal issues
error = "authentication_failed"
return None, error
```

**Discord Cog Level** (in `discord_bot/cogs/*.py`):
```python
# Send error messages to Discord user
try:
    await some_core_function()
except ValueError as e:
    await interaction.response.send_message(f"Error: {e}", ephemeral=True)
except Exception as e:
    await interaction.response.send_message("Internal error", ephemeral=True)
    # Log exception
```

**Notification Error Handling** (in `core/notifications/`):
- Non-critical failures (SendGrid down) log and continue
- Missing users are skipped during bulk sends
- Template render errors caught and logged, don't block other notifications

## Cross-Cutting Concerns

**Logging:**
- Strategy: Print statements for startup/shutdown, exception logs via Sentry
- Sentry initialized at top of `main.py` with `traces_sample_rate=0.1`
- Environment-based sampling: 10% of transactions in all environments
- Discord bot errors caught and re-raised (propagates to Sentry)

**Validation:**
- Input validation at adapter layer (FastAPI Pydantic, Discord interaction checks)
- Business logic validation at core layer (availability overlap, scheduling constraints)
- Database schema validation via SQLAlchemy types and constraints

**Authentication:**
- JWT tokens created by `web_api/auth.py:create_jwt()`, verified with `verify_jwt()`
- Session cookie set via `set_session_cookie()` helper
- Discord bot context available via `interaction.user` for permissions
- FastAPI dependencies: `get_current_user()` (required), `get_optional_user()` (optional)

**Authorization:**
- Discord permissions checked via `@app_commands.checks.has_permissions(administrator=True)`
- Admin routes check `is_admin` flag on user record
- Facilitator access checked via `is_facilitator()` function
- No row-level security currently implemented (all users can see their own data)

**Configuration Management:**
- Centralized in `core/config.py`
- Functions: `is_dev_mode()`, `is_production()`, `get_api_port()`, `get_frontend_port()`, `get_frontend_url()`, `get_allowed_origins()`
- Dev mode paths: separate API/frontend servers, JSON responses at /
- Production paths: single-service SPA with FastAPI serving static frontend build
- Workspace number auto-detected from directory name (e.g., "-ws2" → 8002/3002)

**CORS:**
- Configured in `main.py` with `get_allowed_origins()` from core config
- Allows credentials (cookies), all methods, all headers
- Includes localhost variants for dev (5173 Vite, 8000-8003 API, 3000-3001 frontend)
- Adds production FRONTEND_URL and explicit FRONTEND_URL env var

---

*Architecture analysis: 2026-01-21*
