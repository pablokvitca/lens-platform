"""Auth code generation for Discord-to-Web flow."""

import secrets
from datetime import datetime, timedelta, timezone

from .database import get_client


def get_or_create_user(
    discord_id: str,
    discord_username: str | None = None,
    email: str | None = None,
) -> dict:
    """
    Get or create a user by Discord ID.

    If user exists and new fields are provided, updates them.
    If user doesn't exist, creates with provided fields.

    Args:
        discord_id: The Discord user ID
        discord_username: Optional username to set/update
        email: Optional email to set/update

    Returns:
        The user record from the database
    """
    from datetime import datetime, timezone

    supabase = get_client()

    # Try to get existing user
    result = supabase.table("users").select("*").eq("discord_id", discord_id).execute()

    if result.data:
        user = result.data[0]
        # Update if new fields provided
        updates = {}
        if discord_username and discord_username != user.get("discord_username"):
            updates["discord_username"] = discord_username
        if email and email != user.get("email"):
            updates["email"] = email
        if updates:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("users").update(updates).eq("discord_id", discord_id).execute()
            # Re-fetch to return updated record
            result = supabase.table("users").select("*").eq("discord_id", discord_id).execute()
        return result.data[0]

    # Create new user record
    new_user = {
        "discord_id": discord_id,
        "discord_username": discord_username or f"User_{discord_id[:8]}",
    }
    if email:
        new_user["email"] = email

    result = supabase.table("users").insert(new_user).execute()
    return result.data[0]


def create_auth_code(discord_id: str, expires_minutes: int = 5) -> str:
    """
    Create a temporary auth code for a Discord user.

    Args:
        discord_id: The Discord user ID
        expires_minutes: How long the code is valid (default 5 minutes)

    Returns:
        The generated code string (to be sent to user in a link)
    """
    # Ensure user exists first (auth_codes.user_id is NOT NULL)
    user = get_or_create_user(discord_id)

    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    supabase = get_client()
    supabase.table("auth_codes").insert(
        {
            "code": code,
            "user_id": user["user_id"],
            "discord_id": discord_id,
            "expires_at": expires_at.isoformat(),
        }
    ).execute()

    return code
