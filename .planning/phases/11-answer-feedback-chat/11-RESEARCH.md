# Phase 11: Answer Feedback Chat - Research

**Researched:** 2026-02-20
**Domain:** Post-answer AI feedback chat interface, SSE streaming, conversation persistence, content-driven feature flags
**Confidence:** HIGH

## Summary

Phase 11 adds a per-question AI feedback chat that appears after a student submits their answer. The entire flow is: student writes answer -> clicks Finish -> if `feedback:: true` is set on the question segment in markdown, a chat interface slides in below the completed answer -> the AI sends an initial feedback message (streamed via SSE) based on the question, learning outcome, and student's answer -> student can reply for multi-turn conversation.

The existing infrastructure covers nearly every piece needed. The SSE streaming pattern exists in `web_api/routes/module.py` (the module chat endpoint). The conversation persistence exists via `chat_sessions` table and `core/modules/chat_sessions.py`. The LLM integration exists via `core/modules/llm.py` (both `stream_chat` for streaming and `complete` for non-streaming). The `QuestionSegment` type needs only one new boolean field (`feedback`). The content processor's schema (`content-schema.ts`) needs `feedback` added as an optional boolean field for the `question` segment type. The scoring module (`core/scoring.py`) already demonstrates how to resolve question details from the content cache -- the feedback module can reuse `_resolve_question_details()` for building the feedback prompt.

The main new work is: (1) add `feedback` boolean field through the content processor pipeline to the frontend, (2) create a `FeedbackChat` component that renders below the completed AnswerBox, (3) create a backend endpoint that builds a feedback-specific system prompt (incorporating question text, learning outcome, student answer, and socratic/assessment mode) and streams a response, (4) wire up conversation persistence using the existing `chat_sessions` infrastructure with a new `content_type` value (e.g., `"feedback"`) and a `content_id` derived from the question position.

**Primary recommendation:** Reuse the existing SSE streaming pattern from `web_api/routes/module.py`, the existing `chat_sessions` persistence, and the existing `NarrativeChatSection` component UI as a template. The `FeedbackChat` component should be a simpler, lighter version of `NarrativeChatSection` (no stage transitions, no voice recording initially, just text chat with markdown rendering).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React 19 | 19.x | Frontend component | Already in use |
| Tailwind CSS v4 | ^4 | Styling | Already in use |
| FastAPI | (current) | SSE streaming endpoint | Existing pattern in `module.py` |
| LiteLLM | 1.81+ | LLM provider abstraction | Already integrated, `stream_chat` exists |
| SQLAlchemy Core | >=2.0 | Chat session persistence | Already used for `chat_sessions` table |
| ReactMarkdown | (current) | Rendering AI responses | Already used in `NarrativeChatSection` |
| remark-gfm | (current) | GFM markdown support | Already used in `NarrativeChatSection` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| content_processor (TypeScript) | local | Parse `feedback::` field | Content schema update |
| sentry-sdk | (installed) | Error tracking | Capture feedback endpoint failures |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom FeedbackChat | Reuse NarrativeChatSection directly | NarrativeChatSection has stage transition logic, scroll management for 85vh container, voice recording -- too much complexity. A simpler component is better. |
| chat_sessions table | New dedicated table | Unnecessary -- chat_sessions already supports any content_type and has user/anonymous token, archiving, claiming. Just use a distinct content_type/content_id. |
| Single shared endpoint | Separate feedback endpoint | A separate `/api/chat/feedback` endpoint is cleaner because the system prompt construction is completely different from the module chat (needs answer text, scoring context). |

**Installation:**
```bash
# No new dependencies needed -- everything is already installed
```

## Architecture Patterns

### Recommended Project Structure
```
content_processor/src/
  content-schema.ts          # MODIFY: add 'feedback' to question optional/boolean fields
  index.ts                   # MODIFY: add feedback field to QuestionSegment interface
  parser/lens.ts             # MODIFY: parse feedback field in question segment conversion
  flattener/index.ts         # MODIFY: pass feedback field through in question case

web_frontend/src/
  types/module.ts            # MODIFY: add feedback?: boolean to QuestionSegment
  components/module/
    AnswerBox.tsx             # MODIFY: accept feedback prop, render FeedbackChat when completed
    FeedbackChat.tsx          # NEW: post-answer chat component
  api/
    assessments.ts            # MODIFY: add sendFeedbackMessage() and getFeedbackHistory()

core/
  modules/
    feedback.py              # NEW: feedback prompt builder + stream handler
  scoring.py                 # REFERENCE: reuse _resolve_question_details pattern

web_api/routes/
  assessments.py             # MODIFY: add feedback chat endpoint (or new file)
```

### Pattern 1: SSE Streaming for Feedback (reuse existing pattern)
**What:** The existing module chat uses `StreamingResponse` with `text/event-stream` media type and yields `data: {json}\n\n` formatted events.
**When to use:** For streaming the AI feedback response to the frontend.
**Existing code** (`web_api/routes/module.py` lines 48-128):
```python
async def event_generator(...):
    """Generate SSE events from chat interaction."""
    # Get or create chat session
    async with get_connection() as conn:
        session = await get_or_create_chat_session(conn, ...)
        # Save user message
        await add_chat_message(conn, session_id=session_id, role="user", content=message)

    # Stream response
    assistant_content = ""
    async for chunk in send_module_message(llm_messages, stage, ...):
        if chunk.get("type") == "text":
            assistant_content += chunk.get("content", "")
        yield f"data: {json.dumps(chunk)}\n\n"

    # Save assistant response
    async with get_connection() as conn:
        await add_chat_message(conn, session_id=session_id, role="assistant", content=assistant_content)
```
The feedback endpoint follows this exact pattern but with a different system prompt.

### Pattern 2: Feedback System Prompt Construction
**What:** Build a prompt that includes the question, learning outcome, student answer, and mode (socratic vs assessment).
**When to use:** For the initial AI feedback message and follow-up exchanges.
**Example:**
```python
def _build_feedback_prompt(
    *,
    answer_text: str,
    user_instruction: str,
    assessment_prompt: str | None,
    learning_outcome_name: str | None,
    mode: str,  # "socratic" or "assessment"
) -> str:
    if mode == "socratic":
        system = (
            "You are a supportive tutor providing feedback on a student's response. "
            "Focus on what the student understood well, gently point out gaps, and "
            "ask Socratic questions to deepen their understanding. "
            "Be encouraging and constructive."
        )
    else:
        system = (
            "You are an educational assessor providing feedback on a student's response. "
            "Evaluate the response against the rubric. Point out strengths and weaknesses "
            "with specific references to the student's answer. "
            "Suggest concrete improvements."
        )

    system += f"\n\nQuestion: {user_instruction}"
    if learning_outcome_name:
        system += f"\nLearning Outcome: {learning_outcome_name}"
    if assessment_prompt:
        system += f"\nRubric:\n{assessment_prompt}"
    system += f"\n\nStudent's answer:\n{answer_text}"

    return system
```
**Key difference from scoring:** Feedback is conversational (streaming, multi-turn), scoring is structured (non-streaming, single-shot JSON).

### Pattern 3: Content-Driven Feature Flag via `feedback::` Field
**What:** A boolean field in the question segment markdown that enables/disables the feedback chat.
**When to use:** Content authors control per-question whether feedback is available.
**Example content:**
```markdown
#### Question
user-instruction:: Explain the key risks of advanced AI systems.
feedback:: true
assessment-prompt:: Look for understanding of existential risk, alignment problems, and concrete examples.
```
The field flows through: content-schema.ts -> lens.ts parser -> flattener -> API response -> frontend QuestionSegment type -> AnswerBox component.

### Pattern 4: Chat Session Keying for Feedback
**What:** Use the existing `chat_sessions` table with a distinct `content_type` and position-based `content_id`.
**When to use:** For persisting and restoring feedback conversations.
**Strategy:** Use `content_type="feedback"` and generate a deterministic UUID from the questionId string (e.g., `uuid5(NAMESPACE_URL, questionId)`). This ensures each question-user pair gets exactly one active feedback session.

### Anti-Patterns to Avoid
- **Sharing chat state between module chat and feedback chat:** They are independent conversations with different system prompts. Never share messages state between them.
- **Blocking answer submission on feedback availability:** Feedback is post-completion only. The answer submission flow (auto-save, markComplete) must not change.
- **Auto-triggering the feedback on page load for completed answers:** Only trigger feedback chat when the user first completes the answer in the current session. On return visits, show the existing conversation but don't auto-trigger a new AI message.
- **Including the score data in the feedback prompt:** Scores are hidden from users. The feedback AI should independently assess the answer, not reference internal scores.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE streaming | Custom WebSocket or polling | FastAPI `StreamingResponse` + `text/event-stream` | Already works, battle-tested in module chat |
| Chat persistence | New table or localStorage | `chat_sessions` table + `get_or_create_chat_session` | Already handles race conditions, anonymous+auth, claiming |
| Markdown rendering | Custom parser | `ReactMarkdown` + `remark-gfm` + `ChatMarkdown` component | Already styled for chat context in `NarrativeChatSection.tsx` |
| SSE client parsing | Custom fetch+parse | Existing `sendMessage` async generator pattern from `api/modules.ts` | Already handles chunked reading, JSON parsing, error handling |
| Question context resolution | Custom lookup | `_resolve_question_details` from `core/scoring.py` | Already handles position-based ID parsing, section/segment lookup, mode detection |
| Content field parsing | Manual regex | Content processor `content-schema.ts` + `lens.ts` | Standardized field-level parsing with validation and typo detection |

**Key insight:** This phase is primarily a composition exercise -- assembling existing pieces (SSE, chat sessions, LLM streaming, markdown rendering) with a new system prompt and a new UI trigger point. The only truly new code is the feedback prompt builder and the FeedbackChat component.

## Common Pitfalls

### Pitfall 1: Chat Session Key Collision
**What goes wrong:** If the feedback chat uses the same `content_id` as the module's main chat session, messages get mixed.
**Why it happens:** Both use `chat_sessions` table, and the module chat already uses `content_id = module.content_id`.
**How to avoid:** Use `content_type="feedback"` with a question-specific content_id (derived from questionId). The `chat_sessions` table's unique constraint is on `(user_id, content_id, archived_at IS NULL)`, so a different content_id guarantees a separate session.
**Warning signs:** Feedback messages appearing in the module chat, or vice versa.

### Pitfall 2: Initial Feedback Message Duplication
**What goes wrong:** Refreshing the page after completing an answer triggers a new initial feedback message each time.
**Why it happens:** The frontend sees `isCompleted && feedback === true` and sends an auto-trigger.
**How to avoid:** Check if the feedback session already has messages before sending the initial trigger. On mount, load the feedback history first. Only auto-trigger the initial AI message if the session has zero messages.
**Warning signs:** Multiple "Here's my feedback on your answer..." messages stacking up.

### Pitfall 3: Feedback for Reopened Answers
**What goes wrong:** When a student clicks "Answer again", the old feedback conversation becomes stale (it references the previous answer text).
**Why it happens:** The answer text changes but the feedback session still has the old conversation.
**How to avoid:** When `reopenAnswer()` is called, archive the existing feedback session. When the student completes the new answer, a fresh feedback session starts.
**Warning signs:** AI referencing content from a previous answer attempt in a new feedback conversation.

### Pitfall 4: Scroll Position After Feedback Appears
**What goes wrong:** When the feedback chat appears below a completed answer, the user doesn't see it because it renders below the viewport.
**Why it happens:** The AnswerBox switches to "completed" state (short display), then feedback chat renders, but no scroll happens.
**How to avoid:** After the feedback chat mounts and the initial AI message starts streaming, scroll the feedback chat into view with `scrollIntoView({ behavior: 'smooth', block: 'start' })`.
**Warning signs:** Users don't notice the feedback chat because it's off-screen.

### Pitfall 5: Content Processor Schema Not Updated
**What goes wrong:** Adding `feedback:: true` to content markdown produces a "Unknown field" validation warning, or the field is silently dropped.
**Why it happens:** `content-schema.ts` SEGMENT_SCHEMAS must include `feedback` in the question segment's optional and boolean fields.
**How to avoid:** Update all four locations: `content-schema.ts` (schema), `index.ts` (QuestionSegment interface), `parser/lens.ts` (convertSegment for question type), `flattener/index.ts` (convertSegment pass-through). Also update frontend `types/module.ts`.
**Warning signs:** `feedback:: true` in markdown but `segment.feedback` is undefined in the frontend.

### Pitfall 6: Anonymous User Token Not Passed to Feedback Endpoint
**What goes wrong:** Anonymous users can't persist feedback conversations.
**Why it happens:** Forgetting to include `X-Anonymous-Token` header in the feedback API calls.
**How to avoid:** Follow the same pattern as `api/modules.ts` `sendMessage()` which includes `getAnonymousToken()` header, and `api/assessments.ts` `getAuthHeaders()`.
**Warning signs:** 401 errors or missing sessions for anonymous users.

## Code Examples

### Frontend: FeedbackChat Component Structure
```typescript
// web_frontend/src/components/module/FeedbackChat.tsx
interface FeedbackChatProps {
  questionId: string;      // e.g., "moduleSlug:0:2"
  moduleSlug: string;
  sectionIndex: number;
  segmentIndex: number;
  answerText: string;      // The student's completed answer
  isAuthenticated: boolean;
}

// Component loads history on mount, auto-triggers initial AI message if empty,
// renders messages with ChatMarkdown, provides input for follow-up messages.
```

### Frontend: Integrating into AnswerBox
```typescript
// In AnswerBox.tsx completed state, after the "Completed" indicator:
{isCompleted && segment.feedback && (
  <FeedbackChat
    questionId={questionId}
    moduleSlug={moduleSlug}
    sectionIndex={sectionIndex}
    segmentIndex={segmentIndex}
    answerText={text}
    isAuthenticated={isAuthenticated}
  />
)}
```

### Backend: Feedback Endpoint
```python
# web_api/routes/assessments.py or new file
@router.post("/feedback")
async def feedback_chat(request: FeedbackChatRequest, auth=Depends(get_user_or_anonymous)):
    """Stream AI feedback for a completed answer."""
    return StreamingResponse(
        feedback_event_generator(user_id, anonymous_token, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

### Backend: Feedback Prompt (core/modules/feedback.py)
```python
async def send_feedback_message(
    messages: list[dict],
    question_context: dict,  # from _resolve_question_details
    answer_text: str,
    provider: str | None = None,
) -> AsyncIterator[dict]:
    system = _build_feedback_prompt(
        answer_text=answer_text,
        user_instruction=question_context["user_instruction"],
        assessment_prompt=question_context.get("assessment_prompt"),
        learning_outcome_name=question_context.get("learning_outcome_name"),
        mode=question_context["mode"],
    )
    async for event in stream_chat(messages=messages, system=system, provider=provider, max_tokens=1024):
        yield event
```

### Content: Markdown Syntax
```markdown
#### Question
user-instruction:: What are the main challenges in AI alignment?
feedback:: true
assessment-prompt:: Look for understanding of the alignment problem, inner alignment vs outer alignment, and concrete technical challenges.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate scoring + no feedback | Scoring (Phase 9) + user-facing feedback (Phase 11) | Phase 11 | Students get actionable feedback, not just hidden scores |
| Module chat for everything | Specialized feedback chat per question | Phase 11 | Chat context is question-specific, not module-wide |

## Open Questions

1. **Should feedback use the same LLM provider as scoring or chat?**
   - What we know: SCORING_PROVIDER defaults to DEFAULT_PROVIDER but can be set independently. Module chat uses DEFAULT_PROVIDER.
   - What's unclear: Should feedback have its own provider env var, or reuse one of the existing ones?
   - Recommendation: Use DEFAULT_PROVIDER (same as chat). Feedback is conversational like chat, not structured like scoring. If a separate provider is needed later, it's a one-line env var change.

2. **Should the initial feedback message include the score data from Phase 9?**
   - What we know: Scores are hidden from users. Scoring runs asynchronously and may not be complete when feedback triggers.
   - What's unclear: Could the feedback prompt benefit from seeing the structured score?
   - Recommendation: Do NOT include score data. Feedback should be independently generated. The AI already sees the answer text and rubric, which is sufficient. Including scores creates a timing dependency and might leak score info to users.

3. **Max conversation length for feedback?**
   - What we know: Module chat has no explicit limit (bounded by session lifetime). Token cost per conversation is significant.
   - What's unclear: Should feedback be limited to N turns to control costs?
   - Recommendation: Start without an explicit turn limit. The AI's system prompt can include guidance like "keep the conversation focused, typically 2-4 exchanges." Monitor token usage and add limits if needed.

4. **Should voice recording be available in feedback chat?**
   - What we know: `useVoiceRecording` hook exists and is used in both `NarrativeChatSection` and `AnswerBox`.
   - Recommendation: Omit voice recording from v1 of FeedbackChat to keep it simple. Add later if users request it. The hook is already extracted and reusable.

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** - Read and analyzed all relevant source files:
  - `core/modules/chat.py` - Module chat and system prompt building
  - `core/modules/chat_sessions.py` - Chat session CRUD with race condition handling
  - `core/modules/llm.py` - LiteLLM `stream_chat` and `complete` functions
  - `core/scoring.py` - Scoring module with `_resolve_question_details`
  - `core/tables.py` - `chat_sessions`, `assessment_responses`, `assessment_scores` table definitions
  - `web_api/routes/module.py` - SSE streaming endpoint pattern
  - `web_api/routes/assessments.py` - Assessment submission and scoring trigger
  - `web_frontend/src/components/module/AnswerBox.tsx` - Answer box component
  - `web_frontend/src/components/module/NarrativeChatSection.tsx` - Chat UI component
  - `web_frontend/src/components/module/TestSection.tsx` - Test section container
  - `web_frontend/src/hooks/useAutoSave.ts` - Auto-save hook with complete/reopen
  - `web_frontend/src/api/modules.ts` - SSE client-side parsing (`sendMessage` async generator)
  - `web_frontend/src/api/assessments.ts` - Assessment API client
  - `web_frontend/src/types/module.ts` - Frontend type definitions
  - `web_frontend/src/views/Module.tsx` - Module view with segment rendering
  - `content_processor/src/content-schema.ts` - Content field schema definitions
  - `content_processor/src/index.ts` - QuestionSegment type definition
  - `content_processor/src/parser/lens.ts` - Question segment parsing
  - `content_processor/src/flattener/index.ts` - Segment conversion and pass-through

### Secondary (MEDIUM confidence)
- Phase 7 (Answer Box) and Phase 9 (AI Assessment) research documents - established patterns and prior decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed and in use
- Architecture: HIGH - pattern directly follows existing module chat infrastructure
- Pitfalls: HIGH - identified from direct code reading and understanding of data flow
- Content pipeline: HIGH - traced the exact code path for adding a new field to question segments

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (stable stack, no external dependencies changing)
