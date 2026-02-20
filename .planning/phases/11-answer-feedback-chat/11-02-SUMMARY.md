---
phase: 11-answer-feedback-chat
plan: 02
subsystem: api
tags: [fastapi, sse, llm, litellm, chat-sessions, tdd, feedback, uuid5]

# Dependency graph
requires:
  - phase: 09-ai-assessment
    provides: scoring module pattern (prompt builder, _resolve_question_details)
  - phase: 04-chat
    provides: chat_sessions infrastructure, SSE streaming pattern
provides:
  - core/modules/feedback.py with build_feedback_prompt and send_feedback_message
  - web_api/routes/feedback.py with POST /api/chat/feedback, GET /history, POST /archive
  - Alembic migration adding 'feedback' to chat_sessions content_type CHECK constraint
affects: [11-03-frontend-feedback-chat]

# Tech tracking
tech-stack:
  added: []
  patterns: [feedback prompt builder as pure function, UUID5 content_id derivation for deterministic session keying, find_active_feedback_session helper for archive endpoint]

key-files:
  created:
    - core/modules/feedback.py
    - web_api/routes/feedback.py
    - web_api/tests/test_feedback.py
    - alembic/versions/74fbfc5a473f_add_feedback_to_chat_sessions_content_.py
  modified:
    - core/__init__.py
    - core/tables.py
    - main.py
    - core/tests/test_feedback.py

key-decisions:
  - "UUID5(NAMESPACE_URL, questionId) for deterministic content_id derivation -- same question always maps to same session"
  - "feedback prompt returns string (not tuple) -- simpler than scoring since messages come from chat session"
  - "find_active_feedback_session as separate helper -- keeps archive endpoint clean and testable"
  - "Best-effort archive (always returns ok:true) -- no error on missing session since it could have been archived already"

patterns-established:
  - "Feedback prompt builder: pure function returning system prompt string with mode-based persona switching"
  - "UUID5 content_id: deterministic session keying for position-based question identifiers"

# Metrics
duration: 8min
completed: 2026-02-20
---

# Phase 11 Plan 02: Backend Feedback Module Summary

**TDD feedback module with prompt builder, SSE streaming endpoints, and chat_sessions persistence via UUID5-keyed feedback sessions**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-20T13:16:17Z
- **Completed:** 2026-02-20T13:24:56Z
- **Tasks:** 3 (RED + GREEN + REFACTOR)
- **Files modified:** 8

## Accomplishments
- 8 core tests for feedback prompt builder covering mode switching, optional fields, and return type
- 11 endpoint tests covering POST streaming, GET history, POST archive, auth, UUID5 derivation
- Feedback module (core/modules/feedback.py) with build_feedback_prompt pure function and send_feedback_message streaming handler
- Three API endpoints: POST /api/chat/feedback (SSE), GET /api/chat/feedback/history, POST /api/chat/feedback/archive
- Alembic migration adding 'feedback' to chat_sessions content_type CHECK constraint
- All 260 existing tests still passing (no regressions)

## Task Commits

Each task was committed atomically:

1. **RED: Failing tests** - `117c747` (test)
2. **GREEN: Implementation** - `e2428b8` (feat)
3. **REFACTOR: Cleanup** - `255275d` (refactor)

_TDD cycle: RED (import errors) -> GREEN (19/19 pass) -> REFACTOR (formatting)_

## Files Created/Modified
- `core/modules/feedback.py` - Feedback prompt builder (pure function) + streaming handler
- `web_api/routes/feedback.py` - POST /api/chat/feedback, GET /history, POST /archive endpoints
- `web_api/tests/test_feedback.py` - 11 tests for endpoint contracts
- `core/tests/test_feedback.py` - 8 tests for prompt builder (created in 11-01, verified here)
- `core/tables.py` - CHECK constraint updated to include 'feedback' content_type
- `core/__init__.py` - Exports for build_feedback_prompt, send_feedback_message
- `main.py` - Feedback router registration
- `alembic/versions/74fbfc5a473f_...py` - Migration for CHECK constraint change

## Decisions Made
- UUID5(NAMESPACE_URL, questionId) for deterministic content_id -- ensures same question always maps to same session without database lookup
- Feedback prompt returns a string (not tuple like scoring) -- simpler since messages come from chat session history
- find_active_feedback_session as separate helper function -- reusable and independently testable
- Best-effort archive endpoint (always returns ok:true) -- idempotent, no error on missing session
- Reuses _resolve_question_details from core/scoring.py for question context resolution

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Concurrent agent interference during RED phase commit caused file loss; resolved by restoring to correct jj operation point and recommitting cleanly.

## User Setup Required

None - no external service configuration required. Alembic migration must be run on staging/production database.

## Next Phase Readiness
- Backend feedback module complete with all three endpoints
- Frontend (Plan 03) can now wire up FeedbackChat component to POST /api/chat/feedback and GET /history
- Archive endpoint ready for answer reopen flow

## Self-Check: PASSED

All 6 created files verified on disk. All 3 commit hashes verified in jj log.

---
*Phase: 11-answer-feedback-chat*
*Completed: 2026-02-20*
