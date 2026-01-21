"""Tests for module session management."""

import pytest
from core.modules.sessions import (
    create_session,
    get_session,
    add_message,
    advance_stage,
    claim_session,
    SessionNotFoundError,
    SessionAlreadyClaimedError,
)


@pytest.mark.asyncio
async def test_create_session(test_user_id):
    """Should create a new module session."""
    session = await create_session(
        user_id=test_user_id, module_slug="intro-to-ai-safety"
    )
    assert session["module_slug"] == "intro-to-ai-safety"
    assert session["current_stage_index"] == 0
    assert session["messages"] == []


@pytest.mark.asyncio
async def test_get_session(test_user_id):
    """Should retrieve an existing session."""
    created = await create_session(
        user_id=test_user_id, module_slug="intro-to-ai-safety"
    )
    session = await get_session(created["session_id"])
    assert session["module_slug"] == "intro-to-ai-safety"


@pytest.mark.asyncio
async def test_add_message(test_user_id):
    """Should add a message to session history."""
    session = await create_session(
        user_id=test_user_id, module_slug="intro-to-ai-safety"
    )
    updated = await add_message(session["session_id"], role="user", content="Hello!")
    assert len(updated["messages"]) == 1
    assert updated["messages"][0]["role"] == "user"


@pytest.mark.asyncio
async def test_advance_stage(test_user_id):
    """Should increment stage index."""
    session = await create_session(
        user_id=test_user_id, module_slug="intro-to-ai-safety"
    )
    updated = await advance_stage(session["session_id"])
    assert updated["current_stage_index"] == 1


# --- New claim_session tests ---


@pytest.mark.asyncio
async def test_create_anonymous_session():
    """Can create a session without a user_id."""
    session = await create_session(user_id=None, module_slug="test-module")

    assert session["user_id"] is None
    assert session["module_slug"] == "test-module"
    assert session["session_id"] is not None


@pytest.mark.asyncio
async def test_claim_unclaimed_session(test_user_id, another_test_user_id):
    """Claiming an unclaimed session assigns it to the user."""
    # Create anonymous session
    session = await create_session(user_id=None, module_slug="test-module")
    assert session["user_id"] is None

    # Claim it
    claimed = await claim_session(session["session_id"], another_test_user_id)

    assert claimed["user_id"] == another_test_user_id
    assert claimed["session_id"] == session["session_id"]


@pytest.mark.asyncio
async def test_claim_already_claimed_session_fails(test_user_id, another_test_user_id):
    """Cannot claim a session that already has a user."""
    # Create session with user
    session = await create_session(user_id=test_user_id, module_slug="test-module")

    # Try to claim it
    with pytest.raises(SessionAlreadyClaimedError):
        await claim_session(session["session_id"], another_test_user_id)


@pytest.mark.asyncio
async def test_claim_nonexistent_session_fails(test_user_id):
    """Cannot claim a session that doesn't exist."""
    with pytest.raises(SessionNotFoundError):
        await claim_session(99999, test_user_id)
