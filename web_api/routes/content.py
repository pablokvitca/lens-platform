"""
Content management API routes.

Endpoints:
- POST /api/content/webhook - Handle GitHub push webhook to refresh cache
- POST /api/content/refresh - Manual refresh for development
"""

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, Header

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.content import refresh_cache
from core.content.github_fetcher import get_content_branch
from core.content.webhook_handler import (
    handle_content_update,
    verify_webhook_signature,
    WebhookSignatureError,
)

router = APIRouter(prefix="/api/content", tags=["content"])

logger = logging.getLogger(__name__)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    """
    Handle GitHub push webhook to refresh content cache.

    Called by GitHub when content repo is pushed to.
    Verifies signature, checks branch, then triggers incremental refresh.
    """
    # Verify signature
    body = await request.body()
    try:
        verify_webhook_signature(body, x_hub_signature_256)
    except WebhookSignatureError as e:
        logger.warning(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))

    # Only handle push events
    if x_github_event != "push":
        return {
            "status": "ignored",
            "message": f"Event type '{x_github_event}' ignored",
        }

    # Parse payload for commit SHA and branch
    payload = await request.json()
    commit_sha = payload.get("after")  # SHA of the head commit after push

    if not commit_sha:
        raise HTTPException(
            status_code=400, detail="Missing 'after' commit SHA in payload"
        )

    # Check branch matches configured branch
    ref = payload.get("ref", "")  # e.g., "refs/heads/staging"
    expected_branch = get_content_branch()
    if not ref.endswith(f"/{expected_branch}"):
        return {
            "status": "ignored",
            "message": f"Push to '{ref}' ignored (watching '{expected_branch}')",
        }

    # Handle the update with fetch locking
    try:
        result = await handle_content_update(commit_sha)
        logger.info(f"Webhook processed: {result}")
        return result
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache refresh failed: {e}")


@router.post("/refresh")
async def manual_refresh():
    """
    Manually refresh the content cache.

    For local development when webhooks aren't available.
    TODO: Add admin authentication
    """
    logger.info("Manual cache refresh requested...")

    try:
        await refresh_cache()
        logger.info("Content cache refreshed successfully via manual request")
        return {"status": "ok", "message": "Cache refreshed"}
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache refresh failed: {e}")
