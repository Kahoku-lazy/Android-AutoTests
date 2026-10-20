"""端口监测参数。波特率不在这里，检测和接收都不用它。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_LINE_LIMIT = 4096
DEFAULT_RETRY_SECONDS = 3.0


@dataclass(frozen=True)
class PortParams:
    """一次端口监测要用的参数。"""

    host: str
    port: int
    sku: str
    line_limit: int = DEFAULT_LINE_LIMIT
    retry_seconds: float = DEFAULT_RETRY_SECONDS
    log_directory: Path | None = None
