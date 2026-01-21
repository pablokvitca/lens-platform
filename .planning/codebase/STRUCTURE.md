# Codebase Structure

**Analysis Date:** 2026-01-21

## Directory Layout

```
ai-safety-course-platform/
├── main.py                         # Unified entry point (FastAPI + Discord bot)
├── conftest.py                     # Pytest configuration
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Dev dependencies
├── pyproject.toml                  # Python project config
├── pytest.ini                      # Pytest config
├── Dockerfile                      # Docker image config
├── alembic.ini                     # Alembic migration config
├── CLAUDE.md                       # Project guidelines
├── architecture.md                 # Existing architecture doc
├── README.md                       # Project overview
├── package-lock.json               # Frontend lock file
├── package.json                    # Frontend root package
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
│
├── core/                           # Layer 1: Platform-agnostic business logic
│   ├── __init__.py                 # Public API exports
│   ├── CLAUDE.md                   # Core module guidelines
│   ├── auth.py                     # Discord-to-web auth flow
│   ├── availability.py             # Availability slot handling
│   ├── cohort_names.py             # Group name generation
│   ├── cohorts.py                  # Cohort availability overlap
│   ├── config.py                   # Centralized env configuration
│   ├── constants.py                # Day codes, timezones
│   ├── data.py                     # JSON persistence (legacy)
│   ├── database.py                 # SQLAlchemy async engine
│   ├── enums.py                    # Enum definitions
│   ├── google_docs.py              # Google Docs API integration
│   ├── meetings.py                 # Meeting/calendar operations
│   ├── nickname.py                 # User nickname management
│   ├── nickname_sync.py            # Discord nickname sync
│   ├── scheduling.py               # Stochastic greedy scheduling + dataclasses
│   ├── speech.py                   # Text-to-speech integration
│   ├── stampy.py                   # Stampy chatbot
│   ├── tables.py                   # SQLAlchemy table definitions
│   ├── timezone.py                 # UTC/local conversions
│   ├── users.py                    # User profile management (async)
│   │
│   ├── calendar/                   # Google Calendar integration
│   │   ├── client.py               # Calendar API client
│   │   ├── events.py               # Event creation
│   │   └── rsvp.py                 # RSVP tracking + periodic sync
│   │
│   ├── content/                    # Educational content from GitHub
│   │   ├── cache.py                # Content caching
│   │   ├── github_fetcher.py       # GitHub content retrieval
│   │   └── webhook_handler.py      # GitHub webhook handling
│   │
│   ├── lessons/                    # Lesson-related data
│   │
│   ├── modules/                    # Course/module management
│   │   ├── types.py                # Type definitions
│   │   ├── content.py              # Module content parsing
│   │   ├── chat.py                 # LLM chat integration
│   │   ├── llm.py                  # LiteLLM provider logic
│   │   ├── loader.py               # Module loading
│   │   ├── course_loader.py        # Course loading
│   │   ├── markdown_parser.py      # Markdown parsing
│   │   ├── markdown_validator.py   # Content validation
│   │   └── sessions.py             # Chat session management
│   │
│   ├── notifications/              # Multi-channel notification system
│   │   ├── __init__.py             # Public API
│   │   ├── actions.py              # Notification actions
│   │   ├── dispatcher.py           # Notification routing
│   │   ├── scheduler.py            # APScheduler integration
│   │   ├── templates.py            # Email/Discord templates
│   │   ├── urls.py                 # Dynamic URL generation
│   │   ├── messages.yaml           # Message templates
│   │   ├── channels/               # Channel-specific implementations
│   │   │   ├── discord.py          # Discord notifications
│   │   │   └── email.py            # SendGrid integration
│   │   └── tests/                  # Notification tests
│   │
│   ├── queries/                    # Database query builders
│   │   ├── cohorts.py              # Cohort queries
│   │   ├── courses.py              # Course queries
│   │   ├── groups.py               # Group queries
│   │   ├── modules.py              # Module queries
│   │   └── users.py                # User queries
│   │
│   ├── transcripts/                # Chat transcript storage
│   │
│   └── tests/                      # Unit tests for core
│       ├── conftest.py             # Test fixtures
│       └── test_*.py               # Individual test files
│
├── discord_bot/                    # Layer 2a: Discord adapter
│   ├── __init__.py                 # Module marker
│   ├── main.py                     # Bot initialization, cog loading
│   ├── CLAUDE.md                   # Discord bot guidelines
│   ├── test_bot_manager.py         # Test bot manager
│   │
│   ├── cogs/                       # Slash command handlers (thin adapters)
│   │   ├── __init__.py
│   │   ├── ping_cog.py             # /ping command + bot status
│   │   ├── enrollment_cog.py       # /signup command
│   │   ├── scheduler_cog.py        # /schedule command
│   │   ├── groups_cog.py           # /group command + channel creation
│   │   ├── breakout_cog.py         # Breakout room management
│   │   ├── nickname_cog.py         # Nickname sync
│   │   ├── stampy_cog.py           # Stampy chatbot integration
│   │   └── sync_cog.py             # /sync command for slash command tree
│   │
│   ├── utils/                      # Discord utility functions
│   │
│   └── tests/                      # Discord bot tests
│       └── test_*.py
│
├── web_api/                        # Layer 2b: FastAPI routes
│   ├── __init__.py
│   ├── auth.py                     # JWT utilities, session helpers
│   ├── CLAUDE.md                   # Web API guidelines
│   ├── requirements.txt            # Shared dependencies
│   │
│   ├── routes/                     # RESTful endpoint handlers
│   │   ├── __init__.py
│   │   ├── auth.py                 # POST /auth/* (OAuth, session)
│   │   ├── users.py                # PATCH /api/users/me
│   │   ├── cohorts.py              # GET /api/cohorts/*
│   │   ├── courses.py              # GET /api/courses/*
│   │   ├── modules.py              # GET /api/modules/* (list)
│   │   ├── module.py               # GET /api/module/* (single + chat)
│   │   ├── content.py              # GET /api/content/*
│   │   ├── facilitator.py          # GET /api/facilitator/*
│   │   └── speech.py               # POST /api/speech/*
│   │
│   └── tests/                      # API tests
│       └── test_*.py
│
├── web_frontend/                   # Layer 3b: React SPA
│   ├── vite.config.ts              # Vite configuration
│   ├── tsconfig.json               # TypeScript config
│   ├── package.json                # Dependencies
│   ├── package-lock.json           # Lock file
│   ├── CLAUDE.md                   # Frontend guidelines
│   │
│   ├── src/                        # Frontend source
│   │   ├── main.tsx                # Entry point
│   │   ├── app.tsx                 # Root app component
│   │   ├── analytics.ts            # PostHog analytics
│   │   ├── config.ts               # Frontend configuration
│   │   ├── errorTracking.ts        # Sentry integration
│   │   ├── geolocation.ts          # Geolocation utilities
│   │   │
│   │   ├── pages/                  # Vike file-based routes
│   │   │   ├── +config.ts          # Global route config
│   │   │   ├── +Layout.tsx         # Root layout wrapper
│   │   │   ├── +Head.tsx           # Global head tags
│   │   │   ├── _spa/               # SPA fallback page
│   │   │   ├── _error/             # Error page
│   │   │   ├── index/              # / route
│   │   │   │   └── +Page.tsx
│   │   │   ├── auth/               # /auth routes
│   │   │   │   └── +Page.tsx       # Auth callback handler
│   │   │   ├── enroll/             # /enroll enrollment wizard
│   │   │   │   └── +Page.tsx
│   │   │   ├── availability/       # /availability selection
│   │   │   │   └── +Page.tsx
│   │   │   ├── course/             # /course/:id course viewer
│   │   │   │   ├── @id/
│   │   │   │   │   ├── +Page.tsx
│   │   │   │   │   └── +data.ts    # Data fetching
│   │   │   │   └── +Layout.tsx
│   │   │   ├── module/             # /module/:id module viewer
│   │   │   │   └── +Page.tsx
│   │   │   ├── facilitator/        # /facilitator dashboard
│   │   │   │   └── +Page.tsx
│   │   │   ├── privacy/            # /privacy policy
│   │   │   │   └── +Page.tsx
│   │   │   └── terms/              # /terms of service
│   │   │       └── +Page.tsx
│   │   │
│   │   ├── components/             # Reusable React components
│   │   │   ├── Layout.tsx          # Page layout wrapper
│   │   │   ├── LandingNav.tsx      # Landing page navigation
│   │   │   ├── ModuleHeader.tsx    # Module header component
│   │   │   ├── CookieBanner.tsx    # Cookie consent
│   │   │   ├── CookieSettings.tsx  # Cookie preferences
│   │   │   ├── FeedbackButton.tsx  # Feedback button
│   │   │   ├── MobileWarning.tsx   # Mobile compatibility warning
│   │   │   ├── GlobalComponents.tsx # Global UI components
│   │   │   ├── Popover.tsx         # Popover component
│   │   │   ├── Tooltip.tsx         # Tooltip component
│   │   │   ├── Providers.tsx       # Context providers
│   │   │   │
│   │   │   ├── course/             # Course-related components
│   │   │   │   └── *.tsx
│   │   │   ├── module/             # Module-related components
│   │   │   │   └── *.tsx
│   │   │   ├── enroll/             # Enrollment flow components
│   │   │   │   └── *.tsx
│   │   │   ├── schedule/           # Schedule view components
│   │   │   │   └── *.tsx
│   │   │   ├── nav/                # Navigation components
│   │   │   │   └── *.tsx
│   │   │   └── icons/              # Icon components
│   │   │       └── *.tsx
│   │   │
│   │   ├── hooks/                  # Custom React hooks
│   │   │   └── *.ts
│   │   │
│   │   ├── api/                    # API client functions
│   │   │   ├── users.ts            # User profile API calls
│   │   │   ├── auth.ts             # Auth endpoints
│   │   │   ├── courses.ts          # Course API calls
│   │   │   ├── modules.ts          # Module API calls
│   │   │   └── *.ts
│   │   │
│   │   ├── types/                  # TypeScript type definitions
│   │   │   ├── user.ts             # User types
│   │   │   ├── course.ts           # Course types
│   │   │   ├── module.ts           # Module types
│   │   │   └── *.ts
│   │   │
│   │   ├── utils/                  # Helper utilities
│   │   │   ├── api.ts              # API helpers
│   │   │   ├── date.ts             # Date utilities
│   │   │   └── *.ts
│   │   │
│   │   ├── views/                  # Layout/view components
│   │   │   └── *.tsx
│   │   │
│   │   ├── styles/                 # CSS and style configuration
│   │   │   ├── globals.css         # Global styles
│   │   │   ├── tailwind.css        # Tailwind directives
│   │   │   └── *.css
│   │   │
│   │   └── assets/                 # Static images, icons
│   │       └── *
│   │
│   ├── dist/                       # Built production bundle (generated)
│   │   ├── client/                 # Built frontend files
│   │   │   ├── index.html          # Entry HTML
│   │   │   ├── 200.html            # SPA fallback
│   │   │   ├── assets/             # Built CSS/JS
│   │   │   └── */                  # SSG pre-rendered pages
│   │   └── server/                 # Server bundle (Vike)
│   │
│   └── static/                     # Static files served directly
│       └── *
│
├── migrations/                     # Raw SQL database migrations
│   ├── V001_*.sql                  # Flyway-style migrations
│   └── ...
│
├── alembic/                        # Alembic migration config
│   ├── env.py                      # Migration environment
│   ├── script.py.mako              # Migration template
│   └── versions/                   # Generated migrations
│
├── docs/                           # Design and planning documents
│   └── *.md
│
├── scripts/                        # Utility scripts
│   ├── list-servers                # Show running dev servers
│   └── *.py or *.sh
│
├── static/                         # Static assets for landing page
│   └── *
│
└── .planning/                      # GSD planning documents
    └── codebase/                   # Codebase analysis docs
        ├── ARCHITECTURE.md         # This file
        ├── STRUCTURE.md            # Directory structure guide
        └── ...
```

## Directory Purposes

**core/:**
- Purpose: Platform-agnostic business logic, no framework imports
- Contains: Scheduling, user management, auth, notifications, database access
- Key files: `__init__.py` (public API), `database.py` (SQLAlchemy engine), `tables.py` (schema)

**core/calendar/:**
- Purpose: Google Calendar API integration
- Contains: Calendar client, event creation, RSVP tracking
- Key files: `rsvp.py` (periodic sync job)

**core/content/:**
- Purpose: Fetch and cache educational content from GitHub
- Contains: GitHub API client, content cache, webhook handler
- Key files: `cache.py` (initialization), `github_fetcher.py` (content retrieval)

**core/modules/:**
- Purpose: Course/module content management and LLM chat
- Contains: Module loading, markdown parsing, chat session management
- Key files: `chat.py` (chat routing to LiteLLM), `loader.py` (module content loading)

**core/notifications/:**
- Purpose: Multi-channel notification system (email, Discord DM, Discord mentions)
- Contains: Notification dispatcher, templates, APScheduler integration
- Key files: `dispatcher.py` (routing), `scheduler.py` (delayed jobs), `channels/` (implementations)

**discord_bot/:**
- Purpose: Discord UI adapter, thin command handlers
- Contains: Cogs (slash commands), bot initialization
- Key files: `main.py` (bot setup), `cogs/` (command handlers)

**discord_bot/cogs/:**
- Purpose: Slash command implementations as thin adapters
- Contains: Command handlers that delegate to core
- Pattern: Each cog handles one command domain (enrollment, scheduling, etc.)

**web_api/:**
- Purpose: HTTP API for React frontend
- Contains: FastAPI routes, JWT utilities
- Key files: `routes/` (endpoint handlers), `auth.py` (JWT/session helpers)

**web_api/routes/:**
- Purpose: RESTful endpoint implementations
- Pattern: Each file handles one domain (auth, users, modules, etc.)
- Pattern: Routes call core functions, return JSON responses

**web_frontend/:**
- Purpose: React SPA with Vike SSG
- Contains: Pages, components, hooks, API client functions
- Build output: `dist/` (built SPA served by FastAPI)

**web_frontend/src/pages/:**
- Purpose: Vike file-based routes
- Pattern: Directory = route segment, `+Page.tsx` = page component
- Pattern: `+data.ts` loads data server-side for SSG/SSR

**migrations/:**
- Purpose: Raw SQL database migrations (Flyway format)
- Pattern: `V001_initial.sql`, `V002_add_users.sql`, etc.
- Run by: Flyway or manual migration scripts

**alembic/:**
- Purpose: Alembic migration management (newer approach)
- Contains: Migration scripts generated by `alembic revision`
- Pattern: Hybrid with migrations/ - depends on deployment choice

## Key File Locations

**Entry Points:**
- `main.py`: Unified server entry point (FastAPI + Discord bot)
- `discord_bot/main.py`: Bot initialization (imported by main.py)
- `web_frontend/src/main.tsx`: Frontend entry point

**Configuration:**
- `core/config.py`: Centralized environment configuration
- `.env.example`: Environment variable template
- `vite.config.ts`: Frontend build config
- `alembic.ini`: Alembic config

**Database:**
- `core/database.py`: SQLAlchemy async engine singleton
- `core/tables.py`: Table definitions
- `migrations/` or `alembic/versions/`: Schema migrations

**Core Business Logic:**
- `core/scheduling.py`: Stochastic greedy scheduling algorithm
- `core/users.py`: User profile management
- `core/auth.py`: Discord-to-web auth flow
- `core/notifications/`: Multi-channel notification system
- `core/modules/`: LLM chat and module content

**API Routes:**
- `web_api/routes/auth.py`: OAuth, session management
- `web_api/routes/users.py`: User profile endpoints
- `web_api/routes/modules.py`: Module list and content
- `web_api/routes/module.py`: Single module + chat

**Frontend Pages:**
- `web_frontend/src/pages/index/+Page.tsx`: Home page
- `web_frontend/src/pages/auth/+Page.tsx`: Auth callback
- `web_frontend/src/pages/enroll/+Page.tsx`: Enrollment wizard
- `web_frontend/src/pages/course/@id/+Page.tsx`: Course viewer
- `web_frontend/src/pages/module/+Page.tsx`: Module viewer

**Discord Cogs:**
- `discord_bot/cogs/enrollment_cog.py`: `/signup` command
- `discord_bot/cogs/scheduler_cog.py`: `/schedule` command
- `discord_bot/cogs/groups_cog.py`: `/group` command + channel creation
- `discord_bot/cogs/ping_cog.py`: `/ping` command + bot status

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `enrollment_cog.py`, `google_docs.py`)
- TypeScript/React: `camelCase.ts`, `PascalCase.tsx` (e.g., `useAuth.ts`, `Layout.tsx`)
- Migration: `V001_description.sql` (Flyway) or `migration_description.py` (Alembic)

**Directories:**
- Module directories: `snake_case/` (e.g., `discord_bot/`, `web_api/`, `core/notifications/`)
- Feature directories: `snake_case/` (e.g., `calendar/`, `modules/`, `queries/`)
- Route directories: Match prefix (e.g., `routes/auth.py` → `/auth/*`, `routes/modules.py` → `/api/modules/*`)

**Components/Pages:**
- React components: `PascalCase.tsx` (e.g., `Layout.tsx`, `CookieBanner.tsx`)
- Custom hooks: `useCamelCase.ts` (e.g., `useAuth.ts`, `useFetch.ts`)
- API functions: `camelCase.ts` (e.g., `getProfile()`, `fetchModules()`)
- Types: `camelCase.ts` (e.g., `user.ts`, `course.ts`) or `camelCaseType.ts`

**Async Functions:**
- Async functions in core: `async def function_name(...) -> Type:`
- Async functions in routes: `async def endpoint(...) -> dict:`
- Async functions in cogs: `async def command(...) -> None:`
- Convention: Always explicitly mark async, no hiding in dependencies

## Where to Add New Code

**New Feature (End-to-end):**
1. Business logic: `core/new_feature.py`
   - Platform-agnostic functions
   - No Discord or FastAPI imports
   - Export in `core/__init__.py`

2. Discord integration: `discord_bot/cogs/new_feature_cog.py`
   - Slash command or event handler
   - Calls core functions
   - Added to `COGS` list in `discord_bot/main.py`

3. Web API: `web_api/routes/new_feature.py`
   - FastAPI router with endpoints
   - Calls core functions
   - Imported and included in root `main.py`

4. Frontend: `web_frontend/src/pages/new-feature/+Page.tsx`
   - Vike page component
   - Data loader in `+data.ts` if needed
   - API calls via `web_frontend/src/api/newFeature.ts`

**New Component/Module:**
- Location: `core/` or subdirectory (e.g., `core/modules/`, `core/notifications/`)
- Pattern: Module exports public functions/classes
- Pattern: Internal helpers kept private
- Pattern: Tests in `core/tests/` with same name

**Utilities:**
- Shared helpers for core: `core/utils/` (not created yet, consider for new utilities)
- Shared helpers for frontend: `web_frontend/src/utils/` (already exists)
- Shared helpers for API: `web_api/utils/` (not created yet, could add)

**Database Queries:**
- Location: `core/queries/` (organized by domain)
- Pattern: One file per domain (e.g., `users.py`, `groups.py`, `modules.py`)
- Pattern: Export async query functions
- Pattern: Used by core business logic and routes

**New Page/Route (Frontend):**
- Pages: Create `web_frontend/src/pages/my-page/+Page.tsx`
- Dynamic routes: Create `web_frontend/src/pages/my-page/@id/+Page.tsx`
- Data loading: Create `web_frontend/src/pages/my-page/+data.ts` if needed
- Components for page: Create in `web_frontend/src/components/myPage/`

**New API Endpoint:**
- Location: `web_api/routes/` (existing domain) or new `web_api/routes/domain.py`
- Pattern: Use APIRouter with prefix
- Pattern: Include in `main.py` via `app.include_router()`
- Pattern: Return JSON responses (dict or Pydantic models)

**New Discord Command:**
- Location: Existing cog in `discord_bot/cogs/` or new cog file
- Pattern: Define command as method with `@app_commands.command()` decorator
- Pattern: Delegate to core functions
- Pattern: Send Discord messages via `interaction.response.send_message()`

---

*Structure analysis: 2026-01-21*
