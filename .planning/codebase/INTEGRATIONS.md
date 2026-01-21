# External Integrations

**Analysis Date:** 2026-01-21

## APIs & External Services

**Discord:**
- Discord Bot API - Slash commands, message handling, voice channels
  - SDK/Client: `discord.py` 2.3.0+
  - Auth: `DISCORD_BOT_TOKEN` (env var)
  - Usage: `discord_bot/main.py` initializes bot, cogs handle commands/events

**Google Calendar:**
- Google Calendar API v3 - Event creation, scheduling, RSVP tracking
  - SDK/Client: `google-api-python-client` 2.100.0+, `google-auth` 2.25.0+
  - Auth: Service account via `GOOGLE_CALENDAR_CREDENTIALS_FILE` (JSON path) + `GOOGLE_CALENDAR_EMAIL` (calendar user)
  - Client: `core/calendar/client.py` - singleton service initialization
  - Usage: `core/calendar/events.py` (event creation), `core/calendar/rsvp.py` (RSVP sync)

**GitHub:**
- GitHub REST API - Content fetching for educational materials
  - SDK/Client: `httpx` async HTTP client
  - Auth: Optional `GITHUB_TOKEN` (env var, for rate limit increases)
  - Repository: `lucbrinkman/lens-educational-content`
  - Branches: `staging` (dev/staging) or `main` (production) - set via `EDUCATIONAL_CONTENT_BRANCH` env var
  - Client: `core/content/github_fetcher.py` - fetches markdown content
  - Webhooks: `core/content/webhook_handler.py` - handles GitHub webhook events (content updates)

**LiteLLM (LLM Provider Abstraction):**
- Supports: Claude (Anthropic), Gemini (Google), GPT (OpenAI), and others
  - SDK/Client: `litellm` 1.40.0+
  - Auth: Provider-specific keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, etc.)
  - Default provider: `anthropic/claude-sonnet-4-20250514` (configurable via `LLM_PROVIDER` env var)
  - Client: `core/modules/llm.py` - async streaming chat completion
  - Usage: `core/modules/chat.py` - AI Tutor chat sessions

## Data Storage

**Databases:**
- PostgreSQL (primary) - User data, cohorts, sessions, transcripts
  - Connection: `DATABASE_URL` (Supabase pooler format: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`)
  - Client: SQLAlchemy 2.0.0+ (async mode with asyncpg driver)
  - Connection pool: 5 base + 10 overflow, 30s timeout, 30min recycle, prepared statements disabled
  - Access: `core/database.py` - `get_connection()`, `get_transaction()` context managers
  - ORM: SQLAlchemy Core (table definitions in `core/tables.py`)

**Migrations:**
- Alembic 1.13.0+ - Database schema management
  - Config: `alembic/` directory
  - Run on startup: Dockerfile runs `alembic upgrade head` before starting app
  - Migrations: `migrations/` directory (raw SQL files)

**File Storage:**
- Transcripts: Stored in PostgreSQL (no external blob storage)
- Educational content: Fetched from GitHub on cache initialization
- No local file system persistence for user data

**Caching:**
- In-memory cache for educational content
  - Initialized at startup: `core/content/cache.py`
  - Branch-based (staging vs main)
  - Can be refreshed via webhook (GitHub pushes trigger content reload)
  - No external cache service (Redis, etc.)

## Authentication & Identity

**Auth Provider:**
- Discord OAuth2 - User identity and authentication
  - Implementation: Custom flow in `web_api/routes/auth.py`
  - Discord OAuth endpoints: Authorization code flow
  - Redirect URI: `DISCORD_REDIRECT_URI` (defaults to `http://localhost:8000/auth/discord/callback`)
  - Client ID/Secret: `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET` (env vars)

**Session Management:**
- JWT tokens - Stateless session auth
  - Algorithm: HS256 (HMAC SHA-256)
  - Secret: `JWT_SECRET` (env var, 256-bit)
  - Expiration: 24 hours
  - Storage: HttpOnly cookie (domain/SameSite configurable)
  - Utilities: `web_api/auth.py` - `create_jwt()`, `verify_jwt()`, `get_current_user()` (FastAPI dependency)
  - Cookie config: `COOKIE_DOMAIN`, `COOKIE_SAMESITE` (env vars, defaults to "lax")

**User Identity Sync:**
- Discord nicknames synced to database
  - Module: `core/nickname_sync.py`
  - Cog: `discord_bot/cogs/nickname_cog.py`

## Monitoring & Observability

**Error Tracking:**
- Sentry - Error capturing and performance monitoring
  - Backend: `sentry-sdk[fastapi]` 1.40.0+
  - Frontend: `@sentry/react` 10.35.0 + `@sentry/vite-plugin` 4.7.0
  - DSN: `SENTRY_DSN` (backend), `VITE_SENTRY_DSN` (frontend) - can be same project or separate
  - Initialized in: `main.py` (backend), `src/errorTracking.ts` (frontend)
  - Tracing: 10% sample rate (backend), browser tracing + session replay (frontend)
  - Release tracking: Vite plugin uploads sourcemaps

**Logs:**
- Console/stdout - Printed to container logs
  - Approach: Python print statements, structured logging not used
  - Railway captures stdout/stderr for viewing

**Analytics:**
- PostHog - Product analytics
  - SDK: `posthog-js` 1.325.0
  - Host: `VITE_POSTHOG_HOST` (defaults to `https://eu.posthog.com`)
  - API Key: `VITE_POSTHOG_KEY` (env var)
  - Initialized in: `src/analytics.ts` (frontend only, production builds only)
  - Features: Page view tracking, event capture, user identification

## CI/CD & Deployment

**Hosting:**
- Railway.app - Single containerized service
  - Runs: `python main.py --port ${PORT:-8000}` (unified backend: FastAPI + Discord bot + migrations)
  - Environment: Production on Railway.app, staging/dev locally
  - Environment detection: `RAILWAY_ENVIRONMENT` env var

**CI Pipeline:**
- GitHub Actions - Pre-commit checks (defined in CLAUDE.md)
  - Frontend: ESLint linting, TypeScript build check, Vite build
  - Backend: ruff linting/formatting check, pytest tests
  - No auto-deployment (manual via Railway CLI or dashboard)

**Container:**
- Dockerfile - Multi-step build
  - Base: `python:3.12-slim`
  - Includes: Node.js for frontend build, system deps (libpq, git)
  - Steps: Install Python deps, copy code, build frontend, run migrations, start app
  - Frontend build: `npm ci && npm run build` (produces `web_frontend/dist/`)
  - App startup: `alembic upgrade head && python main.py --port ${PORT:-8000}`

## Environment Configuration

**Required env vars (production/staging):**
- `DATABASE_URL` - PostgreSQL connection string (Supabase pooler format)
- `JWT_SECRET` - 256-bit secret for JWT signing
- `DISCORD_BOT_TOKEN` - Bot token from Discord Developer Portal
- `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET` - OAuth credentials
- `DISCORD_REDIRECT_URI` - OAuth redirect URL (auto-set in dev, explicit in production)
- `DISCORD_SERVER_ID` - Server ID for notifications and nickname sync

**Optional integrations:**
- `GOOGLE_CALENDAR_CREDENTIALS_FILE` - Path to service account JSON
- `GOOGLE_CALENDAR_EMAIL` - Calendar email for event creation
- `SENDGRID_API_KEY` - Email delivery
- `FROM_EMAIL`, `FROM_NAME` - Email sender info
- `SENTRY_DSN`, `VITE_SENTRY_DSN` - Error tracking
- `VITE_POSTHOG_KEY`, `VITE_POSTHOG_HOST` - Analytics (frontend only, production)
- `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY` - LLM provider keys
- `LLM_PROVIDER` - Override default provider (defaults to Claude)
- `GITHUB_TOKEN` - Optional token for GitHub API (rate limit increases)
- `EDUCATIONAL_CONTENT_BRANCH` - Git branch for content (staging or main)

**Secrets location:**
- Railway environment variables (production)
- `.env.local` file (local dev, gitignored)
- `.env` file (fallback defaults)

**Dev-specific:**
- `DEV_MODE` - Serves API-only, frontend runs separately via Vite
- `SKIP_DB_CHECK` - Allow startup without database (frontend-only dev)
- `DISABLE_DISCORD_BOT` - Disable Discord bot (multi-dev-server isolation)
- `API_PORT`, `FRONTEND_PORT` - Auto-assigned per workspace

## Webhooks & Callbacks

**Incoming:**
- GitHub webhooks - Content update notifications
  - Endpoint: `POST /api/content/webhook` (requires secret validation)
  - Handler: `core/content/webhook_handler.py`
  - Triggers: Content refresh when repo is pushed

**Outgoing:**
- Google Calendar invites - Meeting notifications
  - Sent via Google Calendar API (not explicit webhook)
  - Includes calendar invites for accepted RSVPs

**Discord Integration:**
- Discord bot listens for commands (implicit via WebSocket)
- No traditional webhooks for Discord

---

*Integration audit: 2026-01-21*
