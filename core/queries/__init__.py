"""Query layer for database operations using SQLAlchemy Core."""

from .auth import create_auth_code, validate_auth_code
from .users import create_user, get_or_create_user, get_user_by_discord_id, update_user

__all__ = [
    # Users
    "get_user_by_discord_id",
    "create_user",
    "update_user",
    "get_or_create_user",
    # Auth
    "create_auth_code",
    "validate_auth_code",
]
