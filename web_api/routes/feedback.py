"""
Feedback chat API routes.

Endpoints:
- POST /api/chat/feedback - Send message and stream AI feedback response
- GET /api/chat/feedback/history - Get feedback conversation history for a question
- POST /api/chat/feedback/archive - Archive stale feedback session
"""

import json
import logging
import uuid as uuid_mod
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.database import get_connection
from core.modules.chat_sessions import (
    add_chat_message,
    archive_chat_session,
    get_or_create_chat_session,
)
from core.modules.feedback import send_feedback_message
from core.scoring import _resolve_question_details
from core.tables import chat_sessions
from sqlalchemy import select, and_
from web_api.auth import get_user_or_anonymous

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat/feedback", tags=["feedback"])


# --- Pydantic models ---


class FeedbackChatRequest(BaseModel):
    """Request body for feedback chat."""

    questionId: str
    moduleSlug: str
    answerText: str
    message: str


class FeedbackArchiveRequest(BaseModel):
    """Request body for archiving a feedback session."""

    questionId: str


class FeedbackHistoryResponse(BaseModel):
    """Response for feedback history endpoint."""

    sessionId: int
    messages: list[dict]


# --- Helpers ---


def _make_content_id(question_id: str) -> UUID:
    """Derive a deterministic UUID from a questionId string.

    Uses UUID5 with NAMESPACE_URL for reproducible, collision-free IDs.
    """
    return uuid_mod.uuid5(uuid_mod.NAMESPACE_URL, question_id)


async def find_active_feedback_session(
    conn,
    *,
    user_id: int | None,
    anonymous_token: UUID | None,
    content_id: UUID,
) -> dict | None:
    """Find active (non-archived) feedback session for user + question.

    Returns session dict if found, None otherwise.
    """
    conditions = [
        chat_sessions.c.content_type == "feedback",
        chat_sessions.c.content_id == content_id,
        chat_sessions.c.archived_at.is_(None),
    ]

    if user_id is not None:
        conditions.append(chat_sessions.c.user_id == user_id)
    elif anonymous_token is not None:
        conditions.append(chat_sessions.c.anonymous_token == anonymous_token)
    else:
        return None

    result = await conn.execute(select(chat_sessions).where(and_(*conditions)))
    row = result.fetchone()
    return dict(row._mapping) if row else None


# --- SSE event generator ---


async def feedback_event_generator(
    user_id: int | None,
    anonymous_token: UUID | None,
    request: FeedbackChatRequest,
):
    """Generate SSE events from feedback chat interaction."""
    content_id = _make_content_id(request.questionId)

    # Resolve question details from content cache
    question_details = _resolve_question_details(
        module_slug=request.moduleSlug,
        question_id=request.questionId,
    )

    # Get or create chat session
    async with get_connection() as conn:
        session = await get_or_create_chat_session(
            conn,
            user_id=user_id,
            anonymous_token=anonymous_token,
            content_id=content_id,
            content_type="feedback",
        )
        session_id = session["session_id"]
        existing_messages = session.get("messages", [])

        # Save user message
        if request.message:
            await add_chat_message(
                conn,
                session_id=session_id,
                role="user",
                content=request.message,
            )

    # Build messages for LLM (existing history + new message)
    llm_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in existing_messages
        if m["role"] in ("user", "assistant")
    ]
    if request.message:
        llm_messages.append({"role": "user", "content": request.message})

    # Stream response
    assistant_content = ""
    try:
        async for chunk in send_feedback_message(
            messages=llm_messages,
            question_context=question_details,
            answer_text=request.answerText,
        ):
            if chunk.get("type") == "text":
                assistant_content += chunk.get("content", "")
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        logger.error("Feedback streaming error: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # Save assistant response
    if assistant_content:
        async with get_connection() as conn:
            await add_chat_message(
                conn,
                session_id=session_id,
                role="assistant",
                content=assistant_content,
            )


# --- Endpoints ---


@router.post("")
async def feedback_chat(
    request: FeedbackChatRequest,
    auth: tuple[int | None, UUID | None] = Depends(get_user_or_anonymous),
) -> StreamingResponse:
    """
    Send a message and stream AI feedback response.

    Auth: JWT cookie or X-Anonymous-Token header.

    Request body:
    - questionId: Position-based question identifier (moduleSlug:sectionIdx:segmentIdx)
    - moduleSlug: Module identifier
    - answerText: The student's completed answer
    - message: User's follow-up message (empty string for initial trigger)

    Returns SSE stream with:
    - {"type": "text", "content": "..."} for text chunks
    - {"type": "done"} when complete
    - {"type": "error", "message": "..."} on error
    """
    user_id, anonymous_token = auth

    return StreamingResponse(
        feedback_event_generator(
            user_id=user_id,
            anonymous_token=anonymous_token,
            request=request,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/history", response_model=FeedbackHistoryResponse)
async def get_feedback_history(
    questionId: str,
    auth: tuple[int | None, UUID | None] = Depends(get_user_or_anonymous),
):
    """
    Get feedback conversation history for a question.

    Auth: JWT cookie or X-Anonymous-Token header.

    Query params:
    - questionId: Position-based question identifier

    Returns:
    - sessionId: Chat session ID (0 if no session exists)
    - messages: List of {role, content} message dicts
    """
    user_id, anonymous_token = auth
    content_id = _make_content_id(questionId)

    async with get_connection() as conn:
        session = await get_or_create_chat_session(
            conn,
            user_id=user_id,
            anonymous_token=anonymous_token,
            content_id=content_id,
            content_type="feedback",
        )

    return FeedbackHistoryResponse(
        sessionId=session["session_id"],
        messages=session.get("messages", []),
    )


@router.post("/archive")
async def archive_feedback(
    request: FeedbackArchiveRequest,
    auth: tuple[int | None, UUID | None] = Depends(get_user_or_anonymous),
):
    """
    Archive the active feedback session for a question.

    Best-effort: always returns {ok: true} whether or not a session existed.

    Auth: JWT cookie or X-Anonymous-Token header.
    """
    user_id, anonymous_token = auth
    content_id = _make_content_id(request.questionId)

    async with get_connection() as conn:
        session = await find_active_feedback_session(
            conn,
            user_id=user_id,
            anonymous_token=anonymous_token,
            content_id=content_id,
        )
        if session:
            await archive_chat_session(
                conn,
                session_id=session["session_id"],
            )

    return {"ok": True}
