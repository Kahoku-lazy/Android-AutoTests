from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["UiRunResult"]


@dataclass(frozen=True)
class UiRunResult:
    final_text: str
    report_path: Path
    log_path: Path
    model: str = ""
    tokens: dict = field(default_factory=dict)
    by_api_key_env: dict = field(default_factory=dict)
    usages: list = field(default_factory=list)
    cost_s: float = 0.0
