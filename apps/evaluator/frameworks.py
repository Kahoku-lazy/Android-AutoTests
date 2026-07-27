"""Evaluator framework adapters — placeholder.

Extend this module when integrating with evaluation frameworks
(e.g. evalscope, deepeval, etc.). Currently returns empty defaults
so that the views do not crash with ImportError.
"""

available_frameworks = []


def get_adapter(name):
    """Return an adapter instance for the given framework name, or None."""
    return None
