"""
User profile routes.

Endpoints:
- PATCH /api/users/me - Update current user's profile
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_supabase():
    """Get Supabase client."""
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


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
    supabase = get_supabase()
    discord_id = user["sub"]

    # Build update dict with only non-None values
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if updates.first_name is not None:
        update_data["first_name"] = updates.first_name
    if updates.last_name is not None:
        update_data["last_name"] = updates.last_name
    if updates.timezone is not None:
        update_data["timezone"] = updates.timezone
    if updates.availability_utc is not None:
        update_data["availability_utc"] = updates.availability_utc

    # Update in database
    result = (
        supabase.table("users")
        .update(update_data)
        .eq("discord_id", discord_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(404, "User not found")

    return {"status": "updated", "user": result.data[0]}
