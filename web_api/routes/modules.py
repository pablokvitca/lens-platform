"""
Module API routes.

Endpoints:
- GET /api/modules - List available modules
- GET /api/modules/{slug} - Get module definition (flattened)
- GET /api/modules/{slug}/progress - Get module progress
"""

import sys
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.modules import (
    get_available_modules,
    ModuleNotFoundError,
)
from core.modules.loader import load_flattened_module
from core.modules.flattened_types import (
    FlattenedModule,
    FlatSection,
    FlatPageSection,
    FlatLensVideoSection,
    FlatLensArticleSection,
)
from core.modules.progress import get_module_progress
from core.modules.chat_sessions import get_or_create_chat_session
from core.database import get_connection
from web_api.auth import get_optional_user


router = APIRouter(prefix="/api", tags=["modules"])


# --- Serialization Helpers ---


def serialize_flat_section(section: FlatSection) -> dict:
    """Serialize a flat section to JSON for the API response."""
    if isinstance(section, FlatPageSection):
        return {
            "type": "page",
            "contentId": str(section.content_id) if section.content_id else None,
            "meta": {"title": section.title},
            "segments": section.segments,
        }
    elif isinstance(section, FlatLensVideoSection):
        return {
            "type": "lens-video",
            "contentId": str(section.content_id),
            "learningOutcomeId": (
                str(section.learning_outcome_id)
                if section.learning_outcome_id
                else None
            ),
            "videoId": section.video_id,
            "meta": {"title": section.title, "channel": section.channel},
            "segments": section.segments,
            "optional": section.optional,
        }
    elif isinstance(section, FlatLensArticleSection):
        return {
            "type": "lens-article",
            "contentId": str(section.content_id),
            "learningOutcomeId": (
                str(section.learning_outcome_id)
                if section.learning_outcome_id
                else None
            ),
            "meta": {
                "title": section.title,
                "author": section.author,
                "sourceUrl": section.source_url,
            },
            "segments": section.segments,
            "optional": section.optional,
        }
    return {}


def serialize_flattened_module(module: FlattenedModule) -> dict:
    """Serialize a flattened module to JSON for the API response."""
    return {
        "slug": module.slug,
        "title": module.title,
        "sections": [serialize_flat_section(s) for s in module.sections],
    }


# --- Module Definition Endpoints ---


@router.get("/modules")
async def list_modules():
    """List available modules."""
    module_slugs = get_available_modules()
    modules = []
    for slug in module_slugs:
        try:
            module = load_flattened_module(slug)
            modules.append({"slug": module.slug, "title": module.title})
        except ModuleNotFoundError:
            pass  # Skip modules that fail to load
    return {"modules": modules}


@router.get("/modules/{module_slug}")
async def get_module(module_slug: str):
    """Get a module definition with flattened sections."""
    try:
        module = load_flattened_module(module_slug)
        return serialize_flattened_module(module)
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail="Module not found")


@router.get("/modules/{module_slug}/progress")
async def get_module_progress_endpoint(
    module_slug: str,
    request: Request,
    x_anonymous_token: str | None = Header(None),
):
    """Get detailed progress for a single module.

    Returns lens-level completion status, time spent, and chat session info.
    """
    # Get user or session token
    user = await get_optional_user(request)
    user_id = user["user_id"] if user else None
    anonymous_token = None
    if not user_id and x_anonymous_token:
        try:
            anonymous_token = UUID(x_anonymous_token)
        except ValueError:
            pass

    if not user_id and not anonymous_token:
        raise HTTPException(401, "Authentication required")

    # Load module
    try:
        module = load_flattened_module(module_slug)
    except ModuleNotFoundError:
        raise HTTPException(404, "Module not found")

    # Collect content IDs from flattened sections
    content_ids = [s.content_id for s in module.sections if s.content_id]

    async with get_connection() as conn:
        # Get progress for all lenses/sections
        progress_map = await get_module_progress(
            conn,
            user_id=user_id,
            anonymous_token=anonymous_token,
            lens_ids=content_ids,
        )

        # Get chat session
        chat_session = await get_or_create_chat_session(
            conn,
            user_id=user_id,
            anonymous_token=anonymous_token,
            content_id=module.content_id,
            content_type="module",
        )

    # Build lens list with completion status
    lenses = []
    for section in module.sections:
        lens_data = {
            "id": str(section.content_id) if section.content_id else None,
            "title": section.title,
            "type": section.type,
            "optional": getattr(section, "optional", False),
            "completed": False,
            "completedAt": None,
            "timeSpentS": 0,
        }
        if section.content_id and section.content_id in progress_map:
            prog = progress_map[section.content_id]
            lens_data["completed"] = prog.get("completed_at") is not None
            lens_data["completedAt"] = (
                prog["completed_at"].isoformat() if prog.get("completed_at") else None
            )
            lens_data["timeSpentS"] = prog.get("total_time_spent_s", 0)
        lenses.append(lens_data)

    # Calculate module status
    required_lenses = [lens for lens in lenses if not lens["optional"]]
    completed_count = sum(1 for lens in required_lenses if lens["completed"])
    total_count = len(required_lenses)

    if completed_count == 0:
        status = "not_started"
    elif completed_count >= total_count:
        status = "completed"
    else:
        status = "in_progress"

    return {
        "module": {
            "id": str(module.content_id) if module.content_id else None,
            "slug": module.slug,
            "title": module.title,
        },
        "status": status,
        "progress": {"completed": completed_count, "total": total_count},
        "lenses": lenses,
        "chatSession": {
            "sessionId": chat_session["session_id"],
            "hasMessages": len(chat_session.get("messages", [])) > 0,
        },
    }
