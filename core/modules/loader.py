# core/modules/loader.py
"""Load module definitions from cache."""

from core.content import get_cache
from core.modules.markdown_parser import ParsedModule


class ModuleNotFoundError(Exception):
    """Raised when a module cannot be found."""

    pass


def load_narrative_module(module_slug: str) -> ParsedModule:
    """
    Load a narrative module by slug from the cache.

    Args:
        module_slug: The module slug

    Returns:
        ParsedModule dataclass

    Raises:
        ModuleNotFoundError: If module not in cache
    """
    cache = get_cache()

    if module_slug not in cache.modules:
        raise ModuleNotFoundError(f"Module not found: {module_slug}")

    return cache.modules[module_slug]


def get_available_modules() -> list[str]:
    """
    Get list of available module slugs.

    Returns:
        List of module slugs
    """
    cache = get_cache()
    return list(cache.modules.keys())


# Legacy function - redirect to narrative module
def load_module(module_slug: str) -> ParsedModule:
    """Load a module (legacy - redirects to narrative format)."""
    return load_narrative_module(module_slug)
