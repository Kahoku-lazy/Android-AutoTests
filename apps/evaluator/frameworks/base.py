"""Abstract base adapter for external evaluation frameworks."""

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("evaluator")


@dataclass
class AdapterResult:
    """Standardized result from any evaluation framework."""

    ok: bool = True
    error: str = ""

    # Overall scores (0-100 or 1-5 scale, normalized)
    total_score: float = 0.0
    scores: dict[str, float] = field(default_factory=dict)  # dimension -> value

    # Per-question results
    items: list[dict] = field(default_factory=list)

    # Framework-specific raw output
    raw: dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """Unified interface that every external framework adapter must implement.

    Subclasses register via the ``@register(key)`` decorator and provide:
    - ``name`` / ``description`` class attrs for the UI
    - ``is_available()`` to probe whether the package is installed
    - ``run(agent_config, questions, **kwargs) -> AdapterResult``
    """

    name: str = ""
    description: str = ""

    @staticmethod
    @abstractmethod
    def is_available() -> bool:
        """Return True if the framework package is installed and importable."""
        ...

    @abstractmethod
    async def run(
        self,
        agent_config: dict,
        questions: list[dict],
        **kwargs,
    ) -> AdapterResult:
        """Execute evaluation.

        Args:
            agent_config: dict with keys:
                model_provider, model_name, api_key, base_url,
                system_prompt, temperature
            questions: list of {"content": str, "expected_keywords": str, "category": str}

        Returns:
            ``AdapterResult`` with scores and per-item details.
        """
        ...
