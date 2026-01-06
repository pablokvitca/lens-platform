# web_api/tests/test_lessons_api.py
"""Tests for lesson API endpoints."""

import sys
from pathlib import Path

# Ensure we import from root main.py, not web_api/main.py
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


client = TestClient(app)


# --- Task 4: Claim Endpoint Tests ---


def test_claim_session_success():
    """Authenticated user can claim an anonymous session."""
    # Mock the auth to return a user
    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.return_value = {"sub": "test_discord_123", "username": "testuser"}

        # Mock get_or_create_user to return a user
        with patch("web_api.routes.lessons.get_or_create_user") as mock_get_user:
            mock_get_user.return_value = {"user_id": 42, "discord_id": "test_discord_123"}

            # Mock claim_session
            with patch("web_api.routes.lessons.claim_session") as mock_claim:
                mock_claim.return_value = {
                    "session_id": 1,
                    "user_id": 42,
                    "lesson_id": "test",
                    "messages": [],
                }

                response = client.post("/api/lesson-sessions/1/claim")

                assert response.status_code == 200
                assert response.json()["claimed"] is True
                mock_claim.assert_called_once_with(1, 42)


def test_claim_session_requires_auth():
    """Cannot claim a session without authentication."""
    from fastapi import HTTPException

    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.side_effect = HTTPException(status_code=401, detail="Not authenticated")

        response = client.post("/api/lesson-sessions/1/claim")

        # Should fail auth
        assert response.status_code == 401


def test_claim_already_claimed_session():
    """Cannot claim a session that's already claimed."""
    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.return_value = {"sub": "test_discord_123", "username": "testuser"}

        with patch("web_api.routes.lessons.get_or_create_user") as mock_get_user:
            mock_get_user.return_value = {"user_id": 42, "discord_id": "test_discord_123"}

            with patch("web_api.routes.lessons.claim_session") as mock_claim:
                from core.lessons import SessionAlreadyClaimedError
                mock_claim.side_effect = SessionAlreadyClaimedError("Already claimed")

                response = client.post("/api/lesson-sessions/1/claim")

                assert response.status_code == 403


def test_claim_nonexistent_session():
    """Cannot claim a session that doesn't exist."""
    with patch("web_api.routes.lessons.get_current_user") as mock_auth:
        mock_auth.return_value = {"sub": "test_discord_123", "username": "testuser"}

        with patch("web_api.routes.lessons.get_or_create_user") as mock_get_user:
            mock_get_user.return_value = {"user_id": 42, "discord_id": "test_discord_123"}

            with patch("web_api.routes.lessons.claim_session") as mock_claim:
                from core.lessons import SessionNotFoundError
                mock_claim.side_effect = SessionNotFoundError("Session not found")

                response = client.post("/api/lesson-sessions/1/claim")

                assert response.status_code == 404
