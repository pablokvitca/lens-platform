"""Auth-related database queries using SQLAlchemy Core."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from ..tables import auth_codes


async def create_auth_code(
    conn: AsyncConnection,
    user_id: int,
    discord_id: str,
    code: str,
    expires_minutes: int = 5,
) -> dict[str, Any]:
    """Create a new auth code for a user."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    result = await conn.execute(
        insert(auth_codes)
        .values(
            code=code,
            user_id=user_id,
            discord_id=discord_id,
            expires_at=expires_at,
        )
        .returning(auth_codes)
    )
    row = result.mappings().first()
    return dict(row)


async def validate_auth_code(
    conn: AsyncConnection,
    code: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Validate an auth code and mark it as used.

    Returns:
        Tuple of (auth_code_record, error_string).
        If valid, returns (record, None).
        If invalid, returns (None, error_string).
    """
    # Look up the code (must be unused)
    result = await conn.execute(
        select(auth_codes)
        .where(auth_codes.c.code == code)
        .where(auth_codes.c.used_at.is_(None))
    )
    row = result.mappings().first()

    if not row:
        return None, "invalid_code"

    auth_code = dict(row)

    # Check if expired
    expires_at = auth_code["expires_at"]
    # Handle timezone-aware comparison
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        return None, "expired_code"

    # Mark code as used
    await conn.execute(
        update(auth_codes)
        .where(auth_codes.c.code_id == auth_code["code_id"])
        .values(used_at=datetime.now(timezone.utc))
    )

    return auth_code, None
