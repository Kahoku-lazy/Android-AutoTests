from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["SopRunResult", "SopStepResult"]


@dataclass(frozen=True)
class SopStepResult:
    subject: str
    passed: bool
    attempts: int
    message: str = ""
    expected: str = ""


@dataclass(frozen=True)
class SopRunResult:
    phase: str
    steps: list[SopStepResult] = field(default_factory=list)
    report_path: Path | None = None
    log_path: Path | None = None
    model: str = ""
    tokens: dict = field(default_factory=dict)
    by_api_key_env: dict = field(default_factory=dict)
    usages: list = field(default_factory=list)
    cost_s: float = 0.0
