from __future__ import annotations

from datetime import timedelta, timezone

from django.db import Error as DBError

from utils.logs import backend_log

from . import api

__all__ = ["collect_keywords", "row_payload"]

_ORIGIN_DB = "db"
_ORIGIN_NONE = "none"

_BEIJING = timezone(timedelta(hours=8))


def row_payload(row) -> dict:
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
    seen: set[tuple] = set()
    for row in rows:
        for item in row["features"]:
            seen.add(
                (str(item.get("module") or ""), item.get("id"), str(item.get("feature") or ""))
            )
    return len(seen)


def _updated_at(objects: list) -> str:
    stamps = [row.updated_at for row in objects if row.updated_at is not None]
    if not stamps:
        return ""
    latest = max(stamps)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=_BEIJING)
    return latest.astimezone(_BEIJING).strftime("%Y-%m-%d %H:%M:%S")


def collect_keywords() -> dict:
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
