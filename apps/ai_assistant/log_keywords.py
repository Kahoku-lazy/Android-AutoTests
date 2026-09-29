"""日志关键词对照表的只读目录（AI 工具箱「日志关键词」来源）。

「串口日志关键词 → 功能模块 / 功能点」对照表既是证据等级判定的依据，也是只读日志
查询工具还原功能点的依据。本模块只做**读取与组装**，供只读端点使用：

1. 采集正在运行（进程内已有日志总线）时取**运行中的关键词索引**——那是判定真正在用的那份；
2. 否则直读配置文件（`settings.DEVICE_LOG_KEYWORD_FILE`），使面板在采集未启动时也能看；
3. 两者都取不到时返回空列表与可读说明，MUST NOT 抛错。

**只读**：MUST NOT 写文件、MUST NOT 写库、MUST NOT 启停任何端口。
关键词保持**表内顺序**（分组与排序由前端按此顺序派生）。
"""

from __future__ import annotations

import logging

from datetime import datetime
from pathlib import Path

from django.conf import settings

from engines.device.logbus import KeywordIndex, get_log_bus

logger = logging.getLogger("ai_assistant")

__all__ = ["collect_keywords"]

_ORIGIN_RUNTIME = "runtime"
_ORIGIN_FILE = "file"
_ORIGIN_NONE = "none"


def _keyword_file() -> str:
    return str(getattr(settings, "DEVICE_LOG_KEYWORD_FILE", "") or "").strip()


def _updated_at(path: str) -> str:
    """对照表文件的最后修改时间（北京时间，秒精度）；取不到给空串。"""
    if not path:
        return ""
    try:
        stamp = Path(path).stat().st_mtime
    except OSError:
        return ""
    return datetime.fromtimestamp(stamp).strftime("%Y-%m-%d %H:%M:%S")


def _rows(mapping: dict) -> list[dict]:
    """对照表 → 逐关键词的条目（保持表内顺序，功能点原样带出）。"""
    rows: list[dict] = []
    for keyword, features in mapping.items():
        items = [item for item in (features or []) if isinstance(item, dict)]
        rows.append({"keyword": str(keyword), "features": items})
    return rows


def _feature_count(rows: list[dict]) -> int:
    """功能点数按「模块 + 编号 + 名称」去重（同一功能点可能挂在多个关键词下）。"""
    seen: set[tuple] = set()
    for row in rows:
        for item in row["features"]:
            seen.add(
                (str(item.get("module") or ""), item.get("id"), str(item.get("feature") or ""))
            )
    return len(seen)


def collect_keywords() -> dict:
    """当前关键词对照表：关键词 → 功能点，附计数、取值来源与文件更新时间。

    Returns:
        {keywords, keyword_count, feature_count, origin, keyword_file, updated_at, note}
    """
    path = _keyword_file()
    bus = get_log_bus()
    mapping = bus.keywords.mapping if bus is not None else None
    origin = _ORIGIN_RUNTIME
    note = ""
    if not mapping:
        origin = _ORIGIN_FILE
        mapping = KeywordIndex.from_file(path).mapping if path else {}
    if not mapping:
        origin = _ORIGIN_NONE
        note = (
            f"关键词表不可用：未找到或无法解析 {path}"
            if path
            else "未配置关键词表文件（DEVICE_LOG_KEYWORD_FILE 为空）"
        )
        logger.warning("device log keyword catalog is empty: %s", note)
    rows = _rows(mapping)
    return {
        "keywords": rows,
        "keyword_count": len(rows),
        "feature_count": _feature_count(rows),
        "origin": origin,
        "keyword_file": path,
        "updated_at": _updated_at(path),
        "note": note,
    }
