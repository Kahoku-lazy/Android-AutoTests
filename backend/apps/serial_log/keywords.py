"""日志关键词对照表的只读目录（串口日志页「日志关键词」Tab）。

「串口日志关键词 → 功能模块 / 功能点」对照表既是证据等级判定的依据，也是只读日志
查询工具还原功能点的依据。本模块只做**读取与组装**，供只读端点使用：

1. 条目一律取自数据库关键词表（`sl_log_keywords`，经本 App 的 `api.py`）；
2. 表为空或不可用时返回空列表与可读说明，MUST NOT 抛错。

**只读**：MUST NOT 写文件、MUST NOT 写库、MUST NOT 启停任何端口。
关键词保持**表内登记顺序**（sort_order；分组与排序由前端按此顺序派生）。
"""

from __future__ import annotations

from datetime import timedelta, timezone

from django.db import Error as DBError

from utils.logs import backend_log

from . import api

__all__ = ["collect_keywords", "row_payload"]

_ORIGIN_DB = "db"
_ORIGIN_NONE = "none"

# 平台时间口径：固定 UTC+8（不依赖 tzdata），与采集时间戳一致。
_BEIJING = timezone(timedelta(hours=8))


def row_payload(row) -> dict:
    """单条关键词行 → 接口载荷（row_id 供编辑 / 删除定位）。"""
    return {
        "row_id": row.pk,
        "keyword": row.keyword,
        "feature_id": row.feature_id,
        "module": row.module,
        "feature": row.feature,
        "scope": row.scope,
        "sort_order": row.sort_order,
    }


def _rows(objects: list) -> list[dict]:
    """DB 行 → 逐关键词条目（保持登记行序，功能点带主键 / 编号 / 模块 / 名称 / 范围）。"""
    grouped: dict[str, list[dict]] = {}
    for row in objects:
        grouped.setdefault(row.keyword, []).append(
            {
                "row_id": row.pk,
                "id": row.feature_id,
                "module": row.module,
                "feature": row.feature,
                "scope": row.scope,
            }
        )
    return [{"keyword": keyword, "features": features} for keyword, features in grouped.items()]


def _feature_count(rows: list[dict]) -> int:
    """功能点数按「模块 + 编号 + 名称」去重（同一功能点可能挂在多个关键词下；范围不参与去重）。"""
    seen: set[tuple] = set()
    for row in rows:
        for item in row["features"]:
            seen.add(
                (str(item.get("module") or ""), item.get("id"), str(item.get("feature") or ""))
            )
    return len(seen)


def _updated_at(objects: list) -> str:
    """表内最近一次写入时间（北京时间，秒精度）；表为空给空串。"""
    stamps = [row.updated_at for row in objects if row.updated_at is not None]
    if not stamps:
        return ""
    latest = max(stamps)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=_BEIJING)
    return latest.astimezone(_BEIJING).strftime("%Y-%m-%d %H:%M:%S")


def collect_keywords() -> dict:
    """当前关键词对照表：关键词 → 功能点（带范围），附计数、取值来源与最近写入时间。

    Returns:
        {keywords, keyword_count, feature_count, origin, updated_at, note}；
        origin 为 "db"（有条目）或 "none"（空表 / 不可用，note 给可读原因）。
    """
    try:
        objects = api.list_keyword_rows()
    except DBError as exc:
        backend_log.warning("device log keyword catalog unavailable: %s", exc)
        return {
            "keywords": [],
            "keyword_count": 0,
            "feature_count": 0,
            "origin": _ORIGIN_NONE,
            "updated_at": "",
            "note": f"关键词表不可用：{exc}",
        }
    rows = _rows(objects)
    note = ""
    if not rows:
        note = "关键词表暂无条目：请经维护入口登记（sl_log_keywords）"
        backend_log.warning("device log keyword catalog is empty")
    return {
        "keywords": rows,
        "keyword_count": len(rows),
        "feature_count": _feature_count(rows),
        "origin": _ORIGIN_DB if rows else _ORIGIN_NONE,
        "updated_at": _updated_at(objects),
        "note": note,
    }
