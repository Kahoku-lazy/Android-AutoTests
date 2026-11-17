"""停机超时名单：run.py 在杀进程前写下任务编号，清扫读完即删。"""

from __future__ import annotations

import json

from datetime import datetime
from pathlib import Path

MARK = Path(__file__).resolve().parents[3] / "temps" / "stop-timeout-tasks.json"


def write_stop_timeout_ids(ids: list[int]) -> None:
    """写下仍在跑的任务编号。目录不存在时创建。"""
    MARK.parent.mkdir(parents=True, exist_ok=True)
    MARK.write_text(
        json.dumps(
            {"ids": [int(item) for item in ids], "written_at": datetime.now().isoformat()},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def read_stop_timeout_ids() -> set[int]:
    """读名单。文件没有或坏了就当空，不抛给清扫循环。"""
    try:
        data = json.loads(MARK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return set()
    raw = data.get("ids") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return set()
    found: set[int] = set()
    for item in raw:
        try:
            found.add(int(item))
        except (TypeError, ValueError):
            continue
    return found


def clear_stop_timeout_ids() -> None:
    """清扫用过之后删掉，避免下次误套。"""
    MARK.unlink(missing_ok=True)
