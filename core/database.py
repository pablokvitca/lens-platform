"""
Supabase database client for the AI Safety Course Platform.
"""
import os
from supabase import create_client, Client


_client: Client | None = None


def get_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(url, key)
    return _client


def is_configured() -> bool:
    """Check if Supabase credentials are configured."""
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"))
