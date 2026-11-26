from __future__ import annotations

from pathlib import Path

__all__ = ["ASSISTANT_LOG_ROOT", "REPORT_ROOT"]

_REPO_ROOT = Path(__file__).resolve().parents[3]

REPORT_ROOT = _REPO_ROOT / "logs" / "agents" / "backend_bridge"

ASSISTANT_LOG_ROOT = _REPO_ROOT / "logs" / "agents" / "assistants"


if __name__ == "__main__":
    print(REPORT_ROOT)  # noqa: T201 - 模块自测入口
