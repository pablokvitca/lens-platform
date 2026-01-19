# web_api/routes/courses.py
"""Course API routes."""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from core.modules.course_loader import (
    load_course,
    get_next_module,
    CourseNotFoundError,
    _extract_slug_from_path,
)
from core.modules.markdown_parser import ModuleRef, MeetingMarker
from core.modules import (
    load_module,
    get_user_module_progress,
    ModuleNotFoundError,
)
from core.modules.markdown_parser import (
    VideoSection,
    ArticleSection,
    TextSection,
    ChatSection,
)
from web_api.auth import get_optional_user
from core import get_or_create_user

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/{course_slug}/next-module")
async def get_next_module_endpoint(
    course_slug: str,
    current: str = Query(..., description="Current module slug"),
):
    """Get what comes after the current module.

    Returns:
        - 200 with {nextModuleSlug, nextModuleTitle} if next item is a module
        - 200 with {completedUnit: N} if next item is a meeting (unit boundary)
        - 204 No Content if end of course
    """
    try:
        result = get_next_module(course_slug, current)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_slug}")

    if result is None:
        return Response(status_code=204)

    if result["type"] == "unit_complete":
        return {"completedUnit": result["unit_number"]}

    # result["type"] == "module"
    return {
        "nextModuleSlug": result["slug"],
        "nextModuleTitle": result["title"],
    }


@router.get("/{course_slug}/progress")
async def get_course_progress(course_slug: str, request: Request):
    """Get course structure with user progress.

    Returns course modules, lessons, and stages with completion status.
    """
    # Get user if authenticated
    user_jwt = await get_optional_user(request)
    user_id = None
    if user_jwt:
        discord_id = user_jwt["sub"]
        user = await get_or_create_user(discord_id)
        user_id = user["user_id"]

    # Load course structure
    try:
        course = load_course(course_slug)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_slug}")

    # Get user's progress
    progress = await get_user_module_progress(user_id)

    # Build units by splitting progression on MeetingMarker objects
    units = []
    current_modules = []
    current_meeting_number = None

    for item in course.progression:
        if isinstance(item, MeetingMarker):
            # When we hit a meeting, save the current unit if it has modules
            if current_modules:
                units.append(
                    {
                        "meetingNumber": item.number,
                        "modules": current_modules,
                    }
                )
                current_modules = []
            current_meeting_number = item.number
        elif isinstance(item, ModuleRef):
            # Extract module slug from path (e.g., "modules/introduction" -> "introduction")
            module_slug = _extract_slug_from_path(item.path)

            # Load module details
            try:
                module = load_module(module_slug)
            except ModuleNotFoundError:
                continue

            module_progress = progress.get(
                module_slug,
                {
                    "status": "not_started",
                    "current_stage_index": None,
                    "session_id": None,
                },
            )

            # Build sections info (named "stages" for API compatibility)
            stages = []
            for section in module.sections:
                # Get section title based on type
                if isinstance(section, (VideoSection, ArticleSection)):
                    title = (
                        section.source.split("/")[-1]
                        .replace(".md", "")
                        .replace("-", " ")
                        .title()
                    )
                elif isinstance(section, TextSection):
                    title = "Text"
                elif isinstance(section, ChatSection):
                    title = "Discussion"
                else:
                    title = section.type.title()

                stages.append(
                    {
                        "type": section.type,
                        "title": title,
                        "duration": None,  # Duration calculation not available for new format
                        "optional": getattr(section, "optional", False),
                    }
                )

            current_modules.append(
                {
                    "slug": module.slug,
                    "title": module.title,
                    "optional": item.optional,
                    "stages": stages,
                    "status": module_progress["status"],
                    "currentStageIndex": module_progress["current_stage_index"],
                    "sessionId": module_progress["session_id"],
                }
            )

    # Handle any remaining modules after the last meeting (or if no meetings)
    if current_modules:
        # If there were no meetings at all, use meeting number 1 as default
        meeting_num = (current_meeting_number + 1) if current_meeting_number else 1
        units.append(
            {
                "meetingNumber": meeting_num,
                "modules": current_modules,
            }
        )

    return {
        "course": {
            "slug": course.slug,
            "title": course.title,
        },
        "units": units,
    }
