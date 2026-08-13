"""Framework adapters — unified interface for external eval frameworks."""

from .base import AdapterResult, BaseAdapter

# Registry: framework_key -> adapter class (lazy import)
_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(key: str):
    """Decorator to register a framework adapter."""

    def _decorator(cls):
        _REGISTRY[key] = cls
        return cls

    return _decorator


def get_adapter(key: str) -> "BaseAdapter | None":
    """Get an adapter instance by framework key."""
    cls = _REGISTRY.get(key)
    if cls is None:
        return None
    return cls()


def available_frameworks() -> list[dict]:
    """List all registered frameworks with availability status."""
    result = []
    for key, cls in _REGISTRY.items():
        result.append(
            {
                "key": key,
                "name": cls.name,
                "description": cls.description,
                "available": cls.is_available(),
            }
        )
    return result


# Import adapters to trigger registration
from . import (
    deepeval_adapter,  # noqa: E402, F401
    evalscope_adapter,  # noqa: E402, F401
    maseval_adapter,  # noqa: E402, F401
)
