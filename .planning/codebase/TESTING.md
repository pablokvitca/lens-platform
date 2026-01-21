# Testing Patterns

**Analysis Date:** 2026-01-21

## Test Framework

**Python:**
- Runner: `pytest` (installed via `requirements-dev.txt`)
- Async support: `pytest-asyncio`
- Config: `pyproject.toml` (minimal; relies on pytest defaults)
- Run commands:
  ```bash
  pytest                        # Run all tests
  pytest core/tests/            # Core module tests
  pytest discord_bot/tests/     # Discord bot tests
  pytest web_api/tests/         # Web API tests
  pytest -v -s                  # Verbose, show print output
  ```

**TypeScript:**
- No TypeScript test runner configured (tests are Python-only for backend)
- Frontend uses type checking via `typescript` compiler, no runtime tests

**Assertion Library:**
- Python: pytest's built-in `assert` statements

## Test File Organization

**Location:**
- Python: Co-located with source in `tests/` subdirectories
  - `core/tests/` for core logic tests
  - `web_api/tests/` for API endpoint tests
  - `discord_bot/tests/` for bot cog tests

**Naming:**
- `test_*.py` files (e.g., `test_meetings.py`, `test_courses_api.py`)
- Organized by feature or module

**Structure:**
```
core/tests/
├── __init__.py
└── test_meetings.py

web_api/tests/
├── __init__.py
├── conftest.py        # Shared fixtures
├── test_courses_api.py
├── test_modules_api.py
└── test_content_routes.py

discord_bot/tests/
├── __init__.py
├── conftest.py        # Shared fixtures (db_conn, event loop)
├── fake_interaction.py # Mock Discord interaction
├── helpers.py         # Test helpers
└── test_scheduler.py
```

## Test Structure

**Suite Organization (Python):**
```python
"""Tests for meeting service (create, calendar invites, reminders)."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock

class TestCreateMeetingsForGroup:
    """Test meeting record creation."""

    @pytest.mark.asyncio
    async def test_creates_correct_number_of_meetings(self):
        """Should create one meeting per week."""
        # Arrange
        with patch("core.meetings.get_transaction") as mock_tx:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(
                return_value=Mock(scalar_one=Mock(side_effect=[1, 2, 3]))
            )
            # ...setup...

            # Act
            meeting_ids = await create_meetings_for_group(...)

            # Assert
            assert len(meeting_ids) == 3
```

**Patterns:**
- Class-based organization by feature (group related tests)
- `@pytest.mark.asyncio` decorator for async test functions
- Method names describe the test case: `test_<action>_<expected_outcome>`
- Comment-based Arrange-Act-Assert sections (optional but common)

## Mocking

**Framework:**
- `unittest.mock` (Python standard library)
- `AsyncMock` for async functions
- `patch()` for replacing module-level objects

**Patterns:**
```python
# Mock async database connections
with patch("core.meetings.get_transaction") as mock_tx:
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=...)
    mock_tx.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_tx.return_value.__aexit__ = AsyncMock()

# Mock boolean checks
with patch("core.meetings.is_calendar_configured", return_value=True):
    # Test code here

# Verify mock was called correctly
assert mock_create_event.call_count == 2
call_args = mock_create_event.call_args_list[0]
assert call_args.kwargs["attendee_emails"] == [...]
```

**What to Mock:**
- External APIs (Google Calendar, Discord)
- Database connections (use mocks or test database)
- File I/O operations

**What NOT to Mock:**
- Business logic functions being tested
- Simple dataclass creation
- Enum values
- Timezone conversions (test these)

## Fixtures and Factories

**Test Data (Python):**
```python
# web_api/tests/conftest.py - Content cache fixture
@pytest.fixture(autouse=True)
def api_test_cache():
    """Set up a test cache with realistic course data."""
    modules = {
        "introduction": ParsedModule(
            slug="introduction",
            title="Introduction to AI Safety",
            sections=[
                VideoSection(source="...", segments=[]),
                ChatSection(instructions="..."),
            ],
        ),
    }

    courses = {
        "default": ParsedCourse(
            slug="default",
            title="AI Safety Fundamentals",
            progression=[
                ModuleRef(path="modules/introduction"),
                MeetingMarker(number=1),
            ],
        ),
    }

    cache = ContentCache(
        courses=courses,
        modules=modules,
        articles={},
        video_transcripts={},
        last_refreshed=datetime.now(),
    )
    set_cache(cache)
    yield cache
    clear_cache()
```

**Database Test Fixtures:**
```python
# discord_bot/tests/conftest.py - Database connection for tests
@pytest_asyncio.fixture
async def db_conn():
    """Provide a DB connection that rolls back after each test."""
    load_dotenv(".env.local")
    import os

    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, connect_args={"statement_cache_size": 0})

    async with engine.connect() as conn:
        txn = await conn.begin()
        try:
            yield conn
        finally:
            await txn.rollback()

    await engine.dispose()
```

**Test Helpers:**
```python
# discord_bot/tests/helpers.py - Factory functions
async def create_test_cohort(conn, name: str, course_slug: str = "default"):
    """Create a test cohort."""
    result = await conn.execute(...)
    return result.scalar_one()

async def create_test_user(conn, discord_id: str, nickname: str = None):
    """Create a test user."""
    result = await conn.execute(...)
    return result.scalar_one()
```

**Location:**
- Fixtures: `conftest.py` in each test directory (auto-discovered by pytest)
- Helpers: `helpers.py` (imported explicitly in tests)

## Coverage

**Requirements:** Not enforced (no coverage target found in config)

**View Coverage:**
```bash
pytest --cov=core --cov=web_api --cov=discord_bot --cov-report=html
# Open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Scope: Test individual functions in isolation
- Approach: Mock external dependencies (DB, APIs)
- Example: `test_create_correct_number_of_meetings()` in `core/tests/test_meetings.py`
- Pattern: Small inputs, deterministic outputs, fast (<100ms each)

**Integration Tests:**
- Scope: Test multiple components working together
- Approach: Use real or test database; mock only external APIs
- Example: `test_scheduling_e2e.py` in `discord_bot/tests/` (creates real Discord channels)
- Pattern: Larger setup, may have side effects (cleanup important)

**E2E Tests:**
- Framework: `discord_bot/tests/test_scheduling_e2e.py` (uses real Discord bot connection)
- Setup:
  ```python
  @pytest_asyncio.fixture
  async def bot():
      """Create a bot instance and connect to Discord."""
      intents = discord.Intents.default()
      bot = discord.Client(intents=intents)

      token = os.getenv("DISCORD_BOT_TOKEN")
      if not token:
          pytest.skip("DISCORD_BOT_TOKEN not set")

      asyncio.create_task(bot.start(token))

      # Wait for ready (30 retries, 0.5s each = 15s timeout)
      for _ in range(30):
          if bot.is_ready():
              break
          await asyncio.sleep(0.5)
      else:
          pytest.fail("Bot did not connect in time")

      yield bot
      await bot.close()
  ```
- Usage: Skip tests if env vars not set; useful for CI integration verification

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await my_async_function()
    assert result == expected

# For tests that need event loop setup
@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for all async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
```

**Error Testing:**
```python
def test_raises_on_missing_input():
    """Should raise ValueError when input is missing."""
    with pytest.raises(ValueError, match="Input required"):
        my_function(None)

@pytest.mark.asyncio
async def test_http_exception_on_not_found():
    """Should return 404 when resource not found."""
    response = client.get("/api/item/nonexistent")
    assert response.status_code == 404
```

**Parametrized Tests:**
```python
@pytest.mark.parametrize("day,expected", [
    ("M", 0),
    ("T", 1),
    ("W", 2),
])
def test_day_codes(day, expected):
    """Test day code mapping."""
    assert DAY_MAP[day] == expected
```

**Skipping Tests:**
```python
def test_api_endpoint():
    """Should return next module."""
    module_slug = get_first_module_before_meeting("default")
    if module_slug is None:
        pytest.skip("No module→meeting pattern in default course")

    response = client.get(f"/api/courses/default/next-module?current={module_slug}")
    assert response.status_code == 200
```

## API Testing

**Client:** `FastAPI.testclient.TestClient` for endpoint testing

**Pattern:**
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_courses():
    """Should return list of courses."""
    response = client.get("/api/courses")
    assert response.status_code == 200
    data = response.json()
    assert "courses" in data

def test_authenticated_endpoint():
    """Should return 401 when not authenticated."""
    response = client.get("/api/protected")
    assert response.status_code == 401
```

**Auth in Tests:**
- Use `get_optional_user()` dependency for endpoints that allow both auth and anon
- Mock auth by setting test cookies if needed (depends on implementation)

## Discord Bot Testing

**Fake Interaction:** Custom class in `discord_bot/tests/fake_interaction.py` for testing cogs

**Pattern:**
```python
from discord_bot.tests.fake_interaction import FakeInteraction
from discord_bot.cogs.groups_cog import GroupsCog

@pytest.mark.asyncio
async def test_group_creation():
    """Should create a group."""
    interaction = FakeInteraction(user_id=123, guild_id=456)
    cog = GroupsCog(bot)

    await cog.create_group(interaction)

    assert interaction.response.sent_message.content == "Group created"
```

## Test Data Strategies

**Hard-coded Fixtures:**
- Small, deterministic data sets for unit tests
- Example: `api_test_cache()` in `web_api/tests/conftest.py` defines static course structure

**Dynamic Data:**
- For integration tests: create via helper functions (see `helpers.py`)
- For DB tests: use transactional fixtures that roll back after each test

**Realistic Course Structure:**
- Test cache includes: modules → meeting markers → more modules
- Covers edge cases: optional modules, different section types (video, chat, article)
- Allows tests to dynamically discover patterns (e.g., "first module before meeting")

## Pre-commit and CI

**Local checks before push (from CLAUDE.md):**
```bash
# Frontend
cd web_frontend
npm run lint      # ESLint
npm run build     # TypeScript + Vite build

# Backend
ruff check .      # Python linting
ruff format --check .
pytest            # All tests
```

**CI Checks:** Same as above (enforced before merge)

---

*Testing analysis: 2026-01-21*
