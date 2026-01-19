"""Webhook handling for GitHub content updates."""

import asyncio
import hmac
import hashlib
import logging
import os
from typing import Optional

from .github_fetcher import incremental_refresh

logger = logging.getLogger(__name__)

# Fetch locking state
_fetch_lock = asyncio.Lock()
_refetch_pending = False
_pending_commit_sha: Optional[str] = None


class WebhookSignatureError(Exception):
    """Raised when webhook signature verification fails."""

    pass


def verify_webhook_signature(payload: bytes, signature_header: str | None) -> None:
    """Verify GitHub webhook signature.

    Args:
        payload: Raw request body bytes
        signature_header: Value of X-Hub-Signature-256 header

    Raises:
        WebhookSignatureError: If signature is invalid or secret not configured
    """
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret:
        raise WebhookSignatureError("GITHUB_WEBHOOK_SECRET not configured")

    if not signature_header or not signature_header.startswith("sha256="):
        raise WebhookSignatureError("Invalid signature header format")

    expected_sig = signature_header[7:]  # Remove "sha256=" prefix

    computed_sig = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, computed_sig):
        raise WebhookSignatureError("Signature verification failed")


async def handle_content_update(commit_sha: str) -> dict:
    """Handle a content update request with fetch locking.

    If a fetch is in progress:
        - Sets refetch_pending flag
        - Returns immediately (current fetch will handle it)

    If no fetch in progress:
        - Acquires lock
        - Performs incremental refresh
        - Loops while refetch_pending is set

    Returns:
        Status dict with refresh details
    """
    global _refetch_pending, _pending_commit_sha

    if _fetch_lock.locked():
        _refetch_pending = True
        _pending_commit_sha = commit_sha
        logger.info(f"Refresh already in progress, queued commit {commit_sha[:8]}")
        return {"status": "queued", "message": "Refresh already in progress, queued"}

    async with _fetch_lock:
        current_sha = commit_sha
        refreshes = 0

        while True:
            _refetch_pending = False
            logger.info(f"Starting refresh for commit {current_sha[:8]}")
            await incremental_refresh(current_sha)
            refreshes += 1

            if not _refetch_pending:
                break

            # Another webhook came in, use its SHA
            current_sha = _pending_commit_sha or current_sha
            logger.info(f"Pending refresh detected, continuing with {current_sha[:8]}")

        return {
            "status": "ok",
            "message": f"Cache refreshed ({refreshes} refresh(es))",
            "commit_sha": current_sha,
        }


def _reset_fetch_state() -> None:
    """Reset fetch locking state. For testing only."""
    global _refetch_pending, _pending_commit_sha
    _refetch_pending = False
    _pending_commit_sha = None
