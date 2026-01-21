# Codebase Concerns

**Analysis Date:** 2026-01-21

## Tech Debt

**Incomplete Module Progress Notification Logic:**
- Issue: Conditional reminder system has placeholder implementation
- Files: `core/notifications/scheduler.py:227`
- Impact: Module progress nudges never execute; condition check always returns `True`
- Fix approach: Implement actual progress checking in `_check_condition()` - query database for module completion status per user

**Manual Content Refresh Missing Admin Authentication:**
- Issue: `/api/content/refresh` endpoint has no auth protection
- Files: `web_api/routes/content.py:94`
- Impact: Any user can trigger expensive content refreshes, potential DoS vector
- Fix approach: Add `@require_admin` decorator to `manual_refresh()` endpoint and implement admin role check

**Debug Flag in Production Chat:**
- Issue: DEBUG environment variable can expose system prompts in live chat responses
- Files: `core/modules/chat.py:165-167`
- Impact: Confidential LLM system instructions leaked to users if DEBUG=1 set in production
- Fix approach: Restrict DEBUG mode to development only; raise error if enabled in production (`RAILWAY_ENVIRONMENT`)

**Inconsistent Error Handling and Logging:**
- Issue: Mixed `print()` calls (57 occurrences) vs structured logging (23 occurrences)
- Files: Core modules across multiple files
- Impact: Production logs difficult to parse; missing structured fields for alerting
- Fix approach: Standardize on `logging` module with proper log levels; remove `print()` calls; add request tracking IDs

**UTC to Local Time Conversion Stub:**
- Issue: Scheduled event messages show UTC time to all users regardless of timezone
- Files: `discord_bot/cogs/groups_cog.py:406`
- Impact: Users see meeting times in wrong timezone, confusion during group formation
- Fix approach: Use user timezone from database to convert `recurring_meeting_time_utc` to local time per member

**Missing Webhook Signature Verification:**
- Issue: GitHub webhook secret not validated before cache refresh
- Files: `web_api/routes/content.py` calls `verify_webhook_signature()` but...
- Impact: If secret is misconfigured, silent failures; no fallback if signature check disabled
- Fix approach: Add explicit validation that `GITHUB_WEBHOOK_SECRET` is set at startup; log verify attempts

## Known Bugs

**Old Lesson Content Modal Unimplemented:**
- Symptoms: Content preview modal renders nothing for new module system
- Files: `web_frontend/src/components/course/ContentPreviewModal.tsx:4`
- Trigger: Click preview button on course overview page
- Workaround: Use course sidebar to view actual module content instead

**Enrollment Cog Management Functions Misplaced:**
- Symptoms: Code comments suggest functions should be renamed or moved
- Files: `discord_bot/cogs/enrollment_cog.py:37`, `discord_bot/cogs/enrollment_cog.py:66`
- Trigger: Reviewing enrollment cog structure
- Workaround: None; documentation comments only; functionality works as-is

## Security Considerations

**Development Test User Creates Authentication Bypass:**
- Risk: Any unauthenticated user in DEV_MODE gets database record as `dev_test_user_123`
- Files: `web_api/routes/modules.py:112-114`
- Current mitigation: Dev mode check before assignment; won't happen in production
- Recommendations: Add explicit `if not os.getenv("RAILWAY_ENVIRONMENT"):` guard; log test user creation; consider using fixed test Discord ID instead of magic string

**JWT Secret Missing in Development:**
- Risk: `JWT_SECRET` not enforced in dev, auth could fail silently
- Files: `web_api/auth.py:21-24`
- Current mitigation: Only enforces in production (`RAILWAY_ENVIRONMENT`)
- Recommendations: Generate random JWT_SECRET at startup if missing; store in `.env.local` (gitignored); warn prominently if running in dev without secret

**Window Location Redirect Without Validation:**
- Risk: OAuth flow encodes current path/origin into redirect URL without sanitization
- Files: `web_frontend/src/hooks/useAuth.ts:141-143`, `web_frontend/src/views/Auth.tsx:34,79-80`
- Current mitigation: Values are encodeURIComponent'd, origin comes from `window.location.origin`
- Recommendations: Validate redirect target against whitelist of safe paths; prevent redirects to external domains

**CORS Misconfiguration in Development:**
- Risk: Localhost variants for multiple workspaces (8000-8003) hardcoded
- Files: `core/config.py:47-61`
- Current mitigation: Only applies in dev; production uses explicit `FRONTEND_URL`
- Recommendations: Generate CORS origins dynamically from `API_PORT`; remove hardcoded port list

**Missing Rate Limiting on Content Webhook:**
- Risk: GitHub webhook endpoint has no rate limiting; repeated requests trigger expensive refreshes
- Files: `web_api/routes/content.py:30-85`
- Current mitigation: Lock-based deduplication queues rapid webhooks
- Recommendations: Add explicit rate limiting per IP; implement backpressure if refresh takes >60s

## Performance Bottlenecks

**Scheduler Module Size and Complexity:**
- Problem: Single 525-line file handles entire scheduling algorithm
- Files: `core/scheduling.py`
- Cause: Scheduling logic combines person dataclasses, cohort persistence, ungroupable tracking in one file
- Improvement path: Break into `scheduling/algorithm.py`, `scheduling/persistence.py`, `scheduling/analysis.py`

**No Query Optimization for Group Realization:**
- Problem: Discord group creation queries database for each member separately
- Files: `discord_bot/cogs/groups_cog.py:100-300`
- Cause: Sequential `get_user_by_discord_id()` calls in loops instead of bulk fetch
- Improvement path: Batch load all users in one query; create single transaction for channel permissions

**Missing Database Connection Pool Tuning:**
- Problem: Pool size fixed at 5, may be too small for concurrent requests
- Files: `core/database.py:52-53`
- Cause: No profiling of concurrent request patterns
- Improvement path: Monitor pool exhaustion in production; auto-tune based on load (consider HikariCP-style adaptive pooling)

**Calendar Invites Not Batched:**
- Problem: Each group member gets individual calendar API call
- Files: `core/meetings.py:96-103`
- Cause: Loop-based invite sending
- Improvement path: Batch create invites where possible; consider async concurrent requests with rate limiting

## Fragile Areas

**LLM Integration without Fallback:**
- Files: `core/modules/llm.py`, `core/modules/chat.py`
- Why fragile: Single point of failure - if LiteLLM provider unavailable, module chat completely broken; no graceful degradation
- Safe modification: Wrap calls in try-except with timeout; return "Temporarily unavailable" message to user
- Test coverage: No unit tests for provider failure scenarios; only happy path tested

**APScheduler Job Persistence with Silent Fallback:**
- Files: `core/notifications/scheduler.py:68-89`
- Why fragile: If database unavailable at startup, silently switches to in-memory mode; jobs lost on restart
- Safe modification: Always check database connectivity before accepting jobs; reject with 503 if DB unavailable
- Test coverage: No tests for persistence recovery after DB reconnection

**Markdown Parser with No Validation:**
- Files: `core/modules/markdown_parser.py`, `core/modules/markdown_validator.py`
- Why fragile: If YAML frontmatter malformed, parser may silently skip sections
- Safe modification: Add strict parsing mode; raise exception on malformed content instead of defaults
- Test coverage: Validator tests exist but parser tests focus on happy path

**Discord Member Not-In-Guild Handling:**
- Files: `discord_bot/cogs/groups_cog.py:143-284`
- Why fragile: Silently skips members not in guild; no notification to admin that groups are incomplete
- Safe modification: Collect all skip reasons; block group realization if >X% of members skipped; require explicit confirmation
- Test coverage: No tests for member skipping scenarios

**Auth Code Flow with Local Overrides:**
- Files: `web_api/routes/auth.py`, `.env.local` (gitignored)
- Why fragile: `.env.local` overrides can cause local-only bugs that don't reproduce in CI
- Safe modification: Warn on startup if `.env.local` differs from `.env`; sync critical vars automatically
- Test coverage: No tests simulating `.env.local` overrides

## Scaling Limits

**Database Connection Pool (Current: 5, Overflow: 10):**
- Current capacity: 5 concurrent queries + 10 in queue = 15 max
- Limit: Exceeding 15 concurrent DB operations blocks with timeout
- Scaling path: Profile production traffic; adjust `pool_size` and `max_overflow` based on peak concurrency (Railway tier supports ~50 connections)

**APScheduler In-Memory Job Store:**
- Current capacity: Depends on available system memory; unclear limit
- Limit: Running thousands of scheduled notifications may cause memory leak if not monitored
- Scaling path: Migrate all jobs to database jobstore (currently SQLAlchemy-backed but fallback is in-memory)

**Content Cache Without Size Management:**
- Current capacity: No limit on cache size; uses filesystem
- Limit: If educational content repo grows large, cache refresh takes increasingly long
- Scaling path: Implement incremental cache with LRU eviction; add cache size metrics

**Discord API Rate Limits:**
- Current capacity: No explicit rate limiting on Discord API calls
- Limit: Group realization sends many permission/message/event calls; easily hits 10 req/sec limits
- Scaling path: Implement exponential backoff; batch Discord operations; use queue-based processing

## Dependencies at Risk

**Cohort Scheduler Package:**
- Risk: External package controls scheduling algorithm; no vendored copy
- Impact: Update breaking changes require codebase refactor; no algorithm visibility
- Migration plan: If issues arise, implement custom scheduling or switch to `ortools`

**APScheduler with SQLAlchemy Backend:**
- Risk: APScheduler requires sync SQLAlchemy; platform uses async SQLAlchemy (asyncpg)
- Impact: Sync adapter creates potential deadlocks; database URL conversion needed (`postgresql+asyncpg://` → `postgresql://`)
- Migration plan: Monitor for deadlock issues; consider migrating to `APScheduler 4.0` with async support when available

**LiteLLM Abstraction Layer:**
- Risk: LiteLLM adds HTTP request overhead for every LLM call; single point of failure if LiteLLM goes down
- Impact: Chat responses slow if LiteLLM service unavailable; no built-in fallback
- Migration plan: Add direct Anthropic SDK integration as fallback; implement caching of frequently asked responses

**Vike Framework (v0.4):**
- Risk: Vike is pre-v1; breaking changes possible; migration from Next.js ongoing
- Impact: Vike-specific routing and prerendering may not work as expected; SSG prerendering unfinished
- Migration plan: Monitor Vike releases; have rollback plan to Next.js if issues arise

## Missing Critical Features

**Test User Management:**
- Problem: Test users for Discord bot testing are hardcoded; no test data seeding
- Blocks: CI/CD cannot test full bot flows without real Discord account
- Approach: Create `scripts/seed-test-users.py` to populate test Discord IDs in database; use deterministic test data

**Webhook Signature Verification for All Integrations:**
- Problem: Only GitHub webhook has signature verification; email/Sentry webhooks don't
- Blocks: Security audit requires all webhooks signed
- Approach: Add signature verification to all external webhooks; document secret management

**Graceful Degradation for Missing Integrations:**
- Problem: Google Calendar, SendGrid, etc. failures crash endpoints
- Blocks: Platform unavailable if single integration down
- Approach: Wrap integration calls in try-except; return partial results with warnings instead of 500

**Module Content Preloading:**
- Problem: Module content loaded on-demand per request
- Blocks: Scaling to many users causes repeated file I/O
- Approach: Preload common modules at startup; add content cache with TTL

## Test Coverage Gaps

**LLM Provider Failure Scenarios:**
- What's not tested: Timeout, rate limiting, invalid response from LiteLLM
- Files: `core/modules/llm.py`, `core/modules/chat.py`
- Risk: Users can hit timeout errors in chat with no error message
- Priority: High

**Database Connection Failures:**
- What's not tested: Database reconnection after timeout; connection pool exhaustion
- Files: `core/database.py`
- Risk: Unknown behavior if database flaps; connection leak possible
- Priority: High

**Scheduler Persistence Recovery:**
- What's not tested: Job recovery after scheduler restart; orphaned jobs in database
- Files: `core/notifications/scheduler.py`
- Risk: Jobs may be lost or duplicated if scheduler crashes mid-execution
- Priority: Medium

**Discord Group Realization Edge Cases:**
- What's not tested: Member not in guild; permission errors; partial failures
- Files: `discord_bot/cogs/groups_cog.py`
- Risk: Groups partially created with no rollback; inconsistent state
- Priority: Medium

**OAuth Redirect Validation:**
- What's not tested: Open redirect attacks; malformed `next`/`origin` parameters
- Files: `web_api/routes/auth.py`
- Risk: Users redirected to malicious sites after login
- Priority: Critical

**Markdown Content Injection:**
- What's not tested: XSS via markdown in article/video content
- Files: `core/modules/markdown_parser.py`
- Risk: Malicious content from GitHub repo could execute client-side
- Priority: Critical

---

*Concerns audit: 2026-01-21*
