# Technology Stack

**Analysis Date:** 2026-01-21

## Languages

**Primary:**
- Python 3.12+ - Backend (unified service: FastAPI + Discord bot)
- TypeScript 5.x - Frontend (React + Vite + Vike)
- JavaScript (Node.js 25.2.1) - Frontend tooling

**Secondary:**
- SQL - Database (migrations via Alembic)
- YAML - Configuration (APScheduler, other configs)

## Runtime

**Environment:**
- Python 3.12+ (specified in Dockerfile)
- Node.js 25.2.1 (for frontend build and dev)

**Package Manager:**
- pip - Python dependencies
- npm - JavaScript/Node dependencies
- Lockfile: `package.json`/`package-lock.json` for frontend; `requirements.txt` pinned for backend

## Frameworks

**Core:**
- FastAPI 0.109.0+ - HTTP API server (serves web API and static SPA)
- discord.py 2.3.0+ - Discord bot (WebSocket connection to Discord)
- Uvicorn 0.27.0+ - ASGI server for FastAPI

**Frontend:**
- React 19.2.3 - UI framework
- Vike 0.4.252 - SSG + SPA router (file-based routing)
- Vite 7.3.1 - Frontend build tool and dev server
- Tailwind CSS 4.x - Utility-first CSS framework

**Testing:**
- pytest - Python test runner with asyncio support
- ESLint 9.x - JavaScript/TypeScript linting

**Build/Dev:**
- Alembic 1.13.0+ - Database migrations
- ruff 0.8.0+ - Python linting and formatting
- @vitejs/plugin-react 5.1.2 - React support for Vite

## Key Dependencies

**Critical:**
- sqlalchemy[asyncio] 2.0.0+ - ORM and async database access
- asyncpg 0.29.0+ - PostgreSQL driver (used with SQLAlchemy)
- psycopg2-binary 2.9.9+ - PostgreSQL driver (alternative, for migrations)
- pyjwt 2.8.0+ - JWT token creation/verification (session auth)

**Infrastructure:**
- python-dotenv 1.0.0+ - Environment variable management
- httpx 0.27.0+ - Async HTTP client (for API calls)
- litellm 1.40.0+ - LLM provider abstraction (Claude, Gemini, GPT support)

**Integrations:**
- discord.py 2.3.0+ - Discord API client
- sendgrid 6.11.0+ - Email delivery service
- google-api-python-client 2.100.0+ - Google Calendar API
- google-auth 2.25.0+ - Google authentication/service accounts
- sentry-sdk[fastapi] 1.40.0+ - Error tracking and performance monitoring

**Scheduling:**
- APScheduler 3.10.0+ - Background job scheduler (notification reminders, RSVP sync)
- pytz 2023.3+ - Timezone handling
- cohort-scheduler - Custom scheduling algorithm (from git: https://github.com/cpdally/cohort-scheduler.git)

**Frontend Integration:**
- @sentry/react 10.35.0 - Frontend error tracking
- @sentry/vite-plugin 4.7.0 - Sentry release tracking
- posthog-js 1.325.0 - Product analytics
- react-markdown 10.1.0 - Markdown rendering
- lucide-react 0.562.0 - Icon library
- @floating-ui/react 0.27.16 - Floating UI positioning

## Configuration

**Environment:**
- `.env.local` (gitignored) - Local dev overrides
- `.env` - Default environment variables
- Environment variables control: database URL, API keys, Discord tokens, JWT secret, logging levels

**Build:**
- `web_frontend/vite.config.ts` - Vite configuration (dev server, build, proxy)
- `tsconfig.json` - TypeScript compiler options (target ES2022, strict mode, path aliases)
- `pytest.ini` - Pytest configuration (asyncio mode, import mode)
- `Dockerfile` - Container build (Python 3.12, includes Node.js for frontend build)

## Platform Requirements

**Development:**
- Python 3.12+
- Node.js 25.2.1 (or compatible v25.x)
- npm (comes with Node.js)
- PostgreSQL database (Supabase or local)
- Discord bot token (for Discord integration)
- Google service account JSON (for Calendar integration, optional)
- SendGrid API key (for email notifications, optional)
- Sentry DSN (for error tracking, optional)

**Production:**
- Railway.app (or Docker-compatible container environment)
- PostgreSQL database (Supabase recommended)
- All environment variables from `.env.example`
- Workspace auto-ports: API :8000 (or :8000+ws_num), Frontend :3000 (or :3000+ws_num)

---

*Stack analysis: 2026-01-21*
