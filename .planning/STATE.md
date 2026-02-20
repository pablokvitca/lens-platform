# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Students can engage with course content and demonstrate understanding while the platform collects data to improve both teaching and measurement.
**Current focus:** v3.0 Prompt Lab — Phase 6: Chat Evaluation

## Current Position

Phase: 6 of 7 (Chat Evaluation)
Plan: 4 of 5
Status: Executing
Last activity: 2026-02-20 — Completed 06-03 Prompt Lab frontend page & fixture browser

Progress: [██████░░░░] 60%

## Milestone Summary

**v1.0 Mobile Responsiveness:**
- 5 phases, 13 plans completed
- 29/29 requirements satisfied
- 2 days from start to ship
- Tagged: v1.0

## Performance Metrics

**Velocity:**
- Total plans completed: 3 (v3.0)
- Average duration: 6min
- Total execution time: 18min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 06-chat-evaluation | 3/5 | 18min | 6min |

## Accumulated Context

### Decisions

- Fixtures stored as JSON in repo, not database (version-controlled, curated)
- Prompt Lab calls llm.py directly via core/promptlab/ — does not modify chat.py or scoring.py
- Manual fixture extraction via Claude Code (small dataset, no UI needed)
- ChatMarkdown exported as default export for simple import syntax
- Fixture loading is synchronous (small local JSON files, no async needed)
- Fixtures sorted by name in list_fixtures() for deterministic ordering
- Thinking mode bypasses stream_chat() and calls acompletion() directly with thinking parameter
- continue_conversation() delegates to regenerate_response() (functionally identical)
- X-Accel-Buffering: no header on SSE responses for reverse proxy compatibility
- FixtureBrowser uses select dropdown for module filtering (not text search)
- PromptLab view placeholder shows fixture info when selected (Plan 04 replaces with full UI)

### Pending Todos

1 todo in `.planning/todos/pending/`:
- Collapse references section on mobile

### Blockers/Concerns

- Phase 7 (Assessment Evaluation) blocked until ws3 merges `complete()` function and `SCORE_SCHEMA`

## Session Continuity

Last session: 2026-02-20
Stopped at: Completed 06-03-PLAN.md
Resume file: None
