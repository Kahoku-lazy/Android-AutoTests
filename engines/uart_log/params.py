from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_LINE_LIMIT = 4096
DEFAULT_RETRY_SECONDS = 3.0


@dataclass(frozen=True)
class PortParams:
    host: str
    port: int
    sku: str
    line_limit: int = DEFAULT_LINE_LIMIT
    retry_seconds: float = DEFAULT_RETRY_SECONDS
    log_directory: Path | None = None
