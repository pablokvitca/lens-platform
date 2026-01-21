# Coding Conventions

**Analysis Date:** 2026-01-21

## Naming Patterns

**Files:**
- Python: `snake_case.py` (e.g., `core/scheduling.py`, `core/users.py`)
- TypeScript/React: `PascalCase.tsx` for components, `camelCase.ts` for utilities/APIs
  - Example components: `web_frontend/src/components/Tooltip.tsx`, `web_frontend/src/components/LandingNav.tsx`
  - Example utilities: `web_frontend/src/utils/formatDuration.ts`, `web_frontend/src/api/modules.ts`
- Tests: `test_*.py` (Python) or files under `tests/` directories

**Functions:**
- Python: `snake_case` (e.g., `find_availability_overlap()`, `get_user_profile()`)
- TypeScript: `camelCase` (e.g., `formatDuration()`, `getModule()`, `createSession()`)
- React hooks: `useCapitalCase` (e.g., `useAuth()`, `useActivityTracker()`)

**Variables:**
- Python: `snake_case` (locals, module-level), `ALL_CAPS` for constants (e.g., `DAY_MAP`, `DEFAULT_TIMEOUT_MS`)
- TypeScript: `camelCase` (locals), `UPPER_CASE` for module constants (e.g., `DEFAULT_TIMEOUT_MS = 10000`)

**Types:**
- TypeScript: `PascalCase` (e.g., `type User`, `interface AuthState`, `type SessionState`)
- Python dataclasses: `PascalCase` (e.g., `class Person:`, `class UngroupableDetail:`)
- Python enums: `PascalCase` for class, `UPPER_CASE` for values (e.g., `class UngroupableReason(str, Enum):`)

## Code Style

**Formatting:**
- Python: `ruff format` (default settings: double quotes, 4-space indentation, 88 char line length)
- TypeScript: ESLint with typescript-eslint, Vite/PostCSS for styles
  - Config: `web_frontend/eslint.config.mjs` (ES modules)
  - No formatter explicitly configured; ESLint is primary linter

**Linting:**
- Python: `ruff check` (config in `pyproject.toml`)
  - Line length: 88 characters
  - Target: Python 3.11
  - Per-file ignores: `main.py` ignores E402 (module level imports not at top)
- TypeScript: ESLint with rules in `web_frontend/eslint.config.mjs`
  - React hooks: `react-hooks/rules-of-hooks` (error), `react-hooks/exhaustive-deps` (warn)
  - Unused vars: `@typescript-eslint/no-unused-vars` with pattern `argsIgnorePattern: "^_"` (allow underscore-prefixed unused arguments)

## Import Organization

**Order (Python):**
1. Standard library (`sys`, `os`, `json`, `asyncio`)
2. Third-party packages (`sqlalchemy`, `discord`, `fastapi`)
3. Local imports (relative `.` or absolute `core`, `web_api`, etc.)

**Order (TypeScript):**
1. React/external libraries (`react`, `@floating-ui/react`)
2. Internal imports (relative `../` or alias `@/`)
3. Type imports (using `type` keyword)

**Path Aliases:**
- TypeScript: `@/*` → `./src/*` (set in `web_frontend/tsconfig.json`)
  - Usage: `import { User } from "@/types/user"`

## Error Handling

**Python:**
- Custom exceptions inherit from `Exception` or specific base types
- Async functions use `try/except` with context managers for resource cleanup
- Example from `core/cohorts.py`: try/except with `json.loads()` fallback to empty dict
- Pattern: Check for `None` returns or raise `HTTPException` in FastAPI routes
  - Example: `if not item: raise HTTPException(status_code=404, detail="...")`

**TypeScript:**
- Custom error classes: `class RequestTimeoutError extends Error`
  - Set `this.name` for error type identification
  - Include context fields (e.g., `url`, `timeoutMs`)
- API calls use `if (!res.ok) throw new Error()` pattern
- Sentry integration: `Sentry.captureException(error, { tags, extra })`

## Logging

**Framework:**
- Python: `print()` for startup messages (e.g., `print("✓ Sentry error tracking initialized")`)
- TypeScript: `console.error()`, `console.log()` for API-level debugging (e.g., `console.error(\`[API] Request timeout...\`)`)

**Patterns:**
- Python: Print to stdout for informational startup messages
- TypeScript: Log API failures with context (URL, timeout, elapsed time) before throwing
  - Example: `console.error(\`[API] Request timeout after ${elapsed}ms:\`, url, { timeoutMs, elapsed })`

## Comments

**When to Comment:**
- JSDoc/TSDoc for public functions and hooks (especially in libraries)
  - Example: `/**\n * Format seconds as human-readable duration.\n * ...examples...\n */`
- Complex business logic (e.g., scheduling algorithm reasoning)
- Non-obvious async/await patterns
- Avoid redundant comments (don't repeat what code already says)

**Documentation Style:**
- Python: Module docstrings at top of file explaining purpose
  - Example: `"""User profile management. All functions are async and use the database."""`
- TypeScript: Function-level JSDoc with `@param`, `@returns` tags for public APIs
  - Example in `web_frontend/src/api/modules.ts`: detailed SessionState interface with comment

## Function Design

**Size:**
- Python: Aim for <50 lines; break complex logic into helpers
- TypeScript: Aim for <60 lines; prefer composed hooks over monolithic components

**Parameters:**
- Python: Use positional args for required params, keyword args for optional
  - Example: `save_user_profile(discord_id, nickname=None, timezone_str=None, ...)`
- TypeScript: Use object destructuring for multiple params
  - Example: `function Tooltip({ content, children, placement = "top", delay = 400 })`

**Return Values:**
- Python: Functions return `dict`, dataclasses, or `None`; async functions return awaitable values
- TypeScript: Use `Promise<T>` for async, typed return objects, or union types for multiple cases
  - Example: `Promise<ModuleCompletionResult>` where `type ModuleCompletionResult = { type: "next_module"; slug: string } | null`

## Module Design

**Exports:**
- Python: Use `from .my_module import function` in `__init__.py` to expose public API
  - Example: `core/__init__.py` exports functions like `get_user_profile`, `save_user_profile`
- TypeScript: Named exports are preferred for clarity
  - Re-exports in barrel files: `web_frontend/src/components/index.ts` (if used)

**Barrel Files:**
- Minimal use in this codebase
- When used, explicitly list exports to avoid circular dependencies
- Example: `core/__init__.py` collects exports from submodules

## Architecture-Specific Patterns

**Python (Backend):**
- Async-first: All I/O uses `async`/`await` (database, HTTP, Discord)
- Dependency injection: Inject database connections as parameters, not globals
  - Pattern: `async def function(user_id: int) -> dict: async with get_connection() as conn: ...`
- No logging framework: Use `print()` for startup, let exceptions bubble up to Sentry

**TypeScript (Frontend):**
- Declarative UI: Components are functional, hooks manage state
- Custom hooks encapsulate logic (e.g., `useAuth()`, `useActivityTracker()`)
- Timeout handling: Custom `fetchWithTimeout()` wrapper with AbortController
  - Timeouts vary by endpoint type: 10s default, 8s for content, 30s for transcription
- Tailwind CSS: Utility-first styling, no CSS files except global `styles/`

## Database Patterns

**Python:**
- SQLAlchemy ORM with async driver (`asyncpg` for PostgreSQL)
- Connections managed via context managers: `async with get_connection() as conn:`
- Transactions: `async with get_transaction() as conn:` auto-commits on success, rolls back on exception
- Query builders in `core/queries/` separate from business logic

## Testing Patterns (Covered in TESTING.md)

See TESTING.md for test structure, fixtures, and mocking conventions.

---

*Convention analysis: 2026-01-21*
