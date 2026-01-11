# Quick Wins Code Review Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all minor code quality issues identified in the 2026-01-09 code review (dead code, bare except clauses, unused imports, sys.path fixes).

**Architecture:** Pure refactoring with no behavioral changes. Each fix is isolated and can be verified with existing tests or simple manual verification.

**Tech Stack:** Python 3.11+, pytest, React/TypeScript

---

## Task 1: Fix Bare `except:` Clauses in `core/timezone.py`

**Files:**
- Modify: `core/timezone.py:25-26, 54-55`
- Create: `core/tests/test_timezone.py`

**Step 1: Write the failing test**

Create `core/tests/test_timezone.py`:

```python
"""Tests for timezone conversion utilities."""

import pytest
import pytz
from core.timezone import local_to_utc_time, utc_to_local_time


class TestLocalToUtcTime:
    """Tests for local_to_utc_time function."""

    def test_valid_timezone_conversion(self):
        """Valid timezone should convert correctly."""
        # Monday 9am in New York -> Monday 2pm UTC (EST is UTC-5)
        day, hour = local_to_utc_time("Monday", 9, "America/New_York")
        assert day == "Monday"
        assert hour == 14  # 9 + 5 = 14

    def test_invalid_timezone_falls_back_to_utc(self):
        """Invalid timezone string should fall back to UTC (no offset)."""
        day, hour = local_to_utc_time("Monday", 9, "Invalid/Timezone")
        assert day == "Monday"
        assert hour == 9  # No conversion since UTC

    def test_invalid_timezone_raises_correct_exception_type(self):
        """Verify we catch pytz.UnknownTimeZoneError, not bare except."""
        # This test documents the expected exception type
        with pytest.raises(pytz.UnknownTimeZoneError):
            pytz.timezone("Invalid/Timezone")


class TestUtcToLocalTime:
    """Tests for utc_to_local_time function."""

    def test_valid_timezone_conversion(self):
        """Valid timezone should convert correctly."""
        # Monday 14:00 UTC -> Monday 9:00 EST
        day, hour = utc_to_local_time("Monday", 14, "America/New_York")
        assert day == "Monday"
        assert hour == 9

    def test_invalid_timezone_falls_back_to_utc(self):
        """Invalid timezone string should fall back to UTC."""
        day, hour = utc_to_local_time("Monday", 14, "Invalid/Timezone")
        assert day == "Monday"
        assert hour == 14
```

**Step 2: Run test to verify it passes (documenting existing behavior)**

Run: `pytest core/tests/test_timezone.py -v`
Expected: PASS (existing behavior works, we're just documenting it)

**Step 3: Fix bare except clauses**

In `core/timezone.py`, change lines 23-26 from:
```python
    try:
        tz = pytz.timezone(user_tz_str)
    except:
        tz = pytz.UTC
```
to:
```python
    try:
        tz = pytz.timezone(user_tz_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.UTC
```

And change lines 52-55 similarly.

**Step 4: Run test to verify it still passes**

Run: `pytest core/tests/test_timezone.py -v`
Expected: PASS

**Step 5: Commit**

```bash
jj describe -m "fix: replace bare except with pytz.UnknownTimeZoneError in timezone.py"
```

---

## Task 2: Fix Bare `except:` Clauses in `core/cohorts.py`

**Files:**
- Modify: `core/cohorts.py:124-129, 144-149`
- Create: `core/tests/test_cohorts.py`

**Step 1: Write the failing test**

Create `core/tests/test_cohorts.py`:

```python
"""Tests for cohort utilities."""

import pytest
import pytz
from core.cohorts import format_local_time, get_timezone_abbrev


class TestFormatLocalTime:
    """Tests for format_local_time function."""

    def test_valid_timezone(self):
        """Valid timezone should format correctly."""
        day, time_str = format_local_time("Monday", 14, "America/New_York")
        assert day == "Monday"
        assert "9:00" in time_str or "10:00" in time_str  # Depends on DST

    def test_invalid_timezone_uses_raw_name(self):
        """Invalid timezone should use raw timezone name."""
        day, time_str = format_local_time("Monday", 14, "Invalid/Timezone")
        assert day == "Monday"
        assert "Invalid/Timezone" in time_str


class TestGetTimezoneAbbrev:
    """Tests for get_timezone_abbrev function."""

    def test_valid_timezone(self):
        """Valid timezone should return abbreviation."""
        abbrev = get_timezone_abbrev("America/New_York")
        assert abbrev in ("EST", "EDT")

    def test_invalid_timezone_returns_raw(self):
        """Invalid timezone should return the raw string."""
        abbrev = get_timezone_abbrev("Invalid/Timezone")
        assert abbrev == "Invalid/Timezone"
```

**Step 2: Run test to verify it passes**

Run: `pytest core/tests/test_cohorts.py -v`
Expected: PASS

**Step 3: Fix bare except clauses**

In `core/cohorts.py`, change lines 124-129 from:
```python
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(pytz.UTC)
        abbrev = now.astimezone(tz).strftime('%Z')
    except:
        abbrev = tz_name
```
to:
```python
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.now(pytz.UTC)
        abbrev = now.astimezone(tz).strftime('%Z')
    except pytz.UnknownTimeZoneError:
        abbrev = tz_name
```

And change lines 144-149 similarly.

**Step 4: Run test to verify it still passes**

Run: `pytest core/tests/test_cohorts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
jj describe -m "fix: replace bare except with pytz.UnknownTimeZoneError in cohorts.py"
```

---

## Task 3: Fix Bare `except:` in Discord Bot Cogs

**Files:**
- Modify: `discord_bot/cogs/breakout_cog.py:189`
- Modify: `discord_bot/cogs/stampy_cog.py:263`

**Step 1: Fix breakout_cog.py**

Change lines 187-190 from:
```python
                try:
                    await channel.delete()
                except:
                    pass
```
to:
```python
                try:
                    await channel.delete()
                except discord.HTTPException:
                    pass  # Channel may already be deleted
```

**Step 2: Fix stampy_cog.py**

Change lines 261-264 from:
```python
            try:
                await message.reply(f"Error: {e}")
            except:
                pass
```
to:
```python
            try:
                await message.reply(f"Error: {e}")
            except discord.HTTPException:
                pass  # Channel may be deleted or permissions changed
```

**Step 3: Verify no syntax errors**

Run: `python -m py_compile discord_bot/cogs/breakout_cog.py discord_bot/cogs/stampy_cog.py`
Expected: No output (success)

**Step 4: Commit**

```bash
jj describe -m "fix: replace bare except with discord.HTTPException in bot cogs"
```

---

## Task 4: Fix Import Organization in `discord_bot/main.py`

**Files:**
- Modify: `discord_bot/main.py:75`

**Step 1: Move import to top of file**

Add `import traceback` to the imports section (around line 12):
```python
import os
import traceback
import discord
from discord.ext import commands
```

**Step 2: Remove inline import**

Remove the `import traceback` from line 75 (inside the exception handler).

**Step 3: Verify no syntax errors**

Run: `python -m py_compile discord_bot/main.py`
Expected: No output (success)

**Step 4: Commit**

```bash
jj describe -m "style: move traceback import to module level in discord_bot/main.py"
```

---

## Task 5: Fix `core/__init__.py` Issues

**Files:**
- Modify: `core/__init__.py:6-7, 59-60`

**Step 1: Remove duplicate comment**

Remove line 8 (the duplicate `# Database (SQLAlchemy)` comment).

Before:
```python
# Database (SQLAlchemy) - user data migrated to database, courses removed

# Database (SQLAlchemy)
from .database import get_connection, get_transaction, get_engine, close_engine, is_configured
```

After:
```python
# Database (SQLAlchemy) - user data migrated to database, courses removed
from .database import get_connection, get_transaction, get_engine, close_engine, is_configured
```

**Step 2: Fix absolute imports to relative**

Change lines 59-60 from:
```python
from core import stampy
from core import lesson_chat
```
to:
```python
from . import stampy
from . import lesson_chat
```

**Step 3: Verify module still imports correctly**

Run: `python -c "from core import stampy, lesson_chat; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
jj describe -m "style: remove duplicate comment and use relative imports in core/__init__.py"
```

---

## Task 6: Remove Unused Imports

**Files:**
- Modify: `core/queries/groups.py:10` - remove `GroupUserRole`
- Modify: `discord_bot/tests/fake_interaction.py:9` - remove `MagicMock`
- Modify: `web_api/auth.py:14` - remove `Request`
- Modify: `web_frontend/src/api/lessons.ts:5` - remove `Lesson`

**Step 1: Fix core/queries/groups.py**

Change line 10 from:
```python
from ..enums import GroupUserRole
```
to simply removing this line entirely.

**Step 2: Fix discord_bot/tests/fake_interaction.py**

Change line 9 from:
```python
from unittest.mock import MagicMock
```
to simply removing this line entirely.

**Step 3: Fix web_api/auth.py**

Change line 14 from:
```python
from fastapi import HTTPException, Request, Response
```
to:
```python
from fastapi import HTTPException, Response
```

**Step 4: Fix web_frontend/src/api/lessons.ts**

Change line 5 from:
```typescript
import type { Lesson, SessionState } from "../types/unified-lesson";
```
to:
```typescript
import type { SessionState } from "../types/unified-lesson";
```

**Step 5: Verify no import errors**

Run: `python -c "from core.queries.groups import create_group; print('OK')"`
Run: `python -c "from web_api.auth import create_jwt; print('OK')"`
Expected: Both print `OK`

**Step 6: Commit**

```bash
jj describe -m "style: remove unused imports across codebase"
```

---

## Task 7: Fix sys.path Issues in Web API Routes

**Files:**
- Modify: `web_api/routes/users.py:17`
- Modify: `web_api/routes/cohorts.py:14`

**Step 1: Fix users.py**

Change line 17 from:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```
to:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**Step 2: Fix cohorts.py**

Change line 14 from:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```
to:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**Step 3: Verify imports work**

Run: `python -c "from web_api.routes.users import router; print('OK')"`
Run: `python -c "from web_api.routes.cohorts import router; print('OK')"`
Expected: Both print `OK`

**Step 4: Commit**

```bash
jj describe -m "fix: correct sys.path.insert depth in web_api routes"
```

---

## Task 8: Fix React Fragment Key in ScheduleSelector.tsx

**Files:**
- Modify: `web_frontend/src/components/schedule/ScheduleSelector.tsx:136-164`

**Step 1: Add key to React Fragment**

Change lines 136-164 from:
```tsx
        {slots.map((slot) => (
          <>
            {/* Time label ... */}
            <div
              key={`label-${slot}`}
```
to:
```tsx
        {slots.map((slot) => (
          <React.Fragment key={`row-${slot}`}>
            {/* Time label ... */}
            <div
              className="sticky left-0 text-right pr-2 text-xs text-gray-500 flex items-start justify-end relative"
```

And change the closing tag from `</>` to `</React.Fragment>`.

Also add `import React from 'react';` if not already present.

**Step 2: Remove redundant key from child div**

The `key={`label-${slot}`}` on the inner div is no longer needed since the Fragment now has the key.

**Step 3: Build to verify no TypeScript errors**

Run: `cd web_frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
jj describe -m "fix: add key to React.Fragment in ScheduleSelector.tsx"
```

---

## Summary

| Task | Severity | Files Changed | Test Required |
|------|----------|---------------|---------------|
| 1. Bare except in timezone.py | Important | 1 | Yes |
| 2. Bare except in cohorts.py | Important | 1 | Yes |
| 3. Bare except in bot cogs | Important | 2 | No (compile check) |
| 4. Import organization in main.py | Minor | 1 | No (compile check) |
| 5. core/__init__.py cleanup | Minor | 1 | No (import check) |
| 6. Remove unused imports | Minor | 4 | No (import check) |
| 7. Fix sys.path depth | Important | 2 | No (import check) |
| 8. React Fragment key | Important | 1 | No (build check) |

**Total: 8 tasks, 13 files, ~30 minutes**

---

## Execution

After completing all tasks, run the full test suite:

```bash
pytest discord_bot/tests/ -v
```

And verify the frontend builds:

```bash
cd web_frontend && npm run build
```
