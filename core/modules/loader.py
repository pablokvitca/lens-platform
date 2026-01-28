# core/modules/loader.py
"""Load module definitions from cache."""

from core.content import get_cache
from core.modules.flattened_types import FlattenedModule


class ModuleNotFoundError(Exception):
    """Raised when a module cannot be found."""

    pass


def load_flattened_module(module_slug: str) -> FlattenedModule:
    """
    Load a flattened module by slug from the cache.

    Args:
        module_slug: The module slug

    Returns:
        FlattenedModule dataclass with resolved sections

    Raises:
        ModuleNotFoundError: If module not in cache
    """
    cache = get_cache()

    if module_slug not in cache.flattened_modules:
        raise ModuleNotFoundError(f"Module not found: {module_slug}")

    return cache.flattened_modules[module_slug]


def get_available_modules() -> list[str]:
    """
    Get list of available module slugs.

    Returns:
        List of module slugs
    """
    cache = get_cache()
    return list(cache.flattened_modules.keys())


# Legacy aliases
def load_narrative_module(module_slug: str) -> FlattenedModule:
    """Load a module (legacy name - redirects to load_flattened_module)."""
    return load_flattened_module(module_slug)


def load_module(module_slug: str) -> FlattenedModule:
    """Load a module (legacy name - redirects to load_flattened_module)."""
    return load_flattened_module(module_slug)
