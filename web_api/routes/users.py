"""
User profile routes.

Endpoints:
- PATCH /api/users/me - Update current user's profile
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update as sql_update

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_transaction
from core.tables import users
from web_api.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    first_name: str | None = None
    last_name: str | None = None
    timezone: str | None = None
    availability_utc: str | None = None


@router.patch("/me")
async def update_my_profile(
    updates: UserProfileUpdate,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Update the current user's profile.

    Only allows updating specific fields: first_name, last_name, timezone, availability_utc
    """
    discord_id = user["sub"]

    # Build update dict with only non-None values
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}

    if updates.first_name is not None:
        update_data["first_name"] = updates.first_name
    if updates.last_name is not None:
        update_data["last_name"] = updates.last_name
    if updates.timezone is not None:
        update_data["timezone"] = updates.timezone
    if updates.availability_utc is not None:
        update_data["availability_utc"] = updates.availability_utc

    # Update in database
    async with get_transaction() as conn:
        result = await conn.execute(
            sql_update(users)
            .where(users.c.discord_id == discord_id)
            .values(**update_data)
            .returning(users)
        )
        row = result.mappings().first()

    if not row:
        raise HTTPException(404, "User not found")

    return {"status": "updated", "user": dict(row)}
