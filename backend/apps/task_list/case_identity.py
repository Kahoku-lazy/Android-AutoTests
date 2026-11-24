"""
模块功能：➡️ 用例身份（标签与身份行）：任务与 BUG 单共用同一口径 🏁
Python 调试：➡️ python -m backend.apps.task_list.case_identity 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 task_list 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

_MILESTONE = "milestone"
_UNTITLED = "未命名用例"


def case_identity_label(identity: object) -> str:
    """
    把用例身份收成与任务清单、BUG 单、仪表盘共用的一句文案。

    Args:
        identity: 任务上冻结的字典。旧任务是空对象。

    Returns:
        空身份返回空串；里程碑返回「里程碑」；一条返回标题；多条返回「第一条 · 共 N 条」。
    """
    if not isinstance(identity, dict) or not identity:
        return ""
    if identity.get("source") == _MILESTONE:
        return "里程碑"
    rows = _rows(identity)
    if not rows:
        return ""
    first = _title(rows[0])
    if len(rows) == 1:
        return first
    return f"{first} · 共 {len(rows)} 条"


def case_identity_rows(identity: object) -> list[dict]:
    """
    取出冻结的行，保持提交时的选择顺序。

    Args:
        identity: 任务上冻结的字典。

    Returns:
        每行含 project、id、title。非平台身份返回空列表。
    """
    if not isinstance(identity, dict) or identity.get("source") == _MILESTONE:
        return []
    return _rows(identity)


def _rows(identity: dict) -> list[dict]:
    """只保留带标题的行，空标题写成「未命名用例」。"""
    raw = identity.get("rows")
    if not isinstance(raw, list):
        return []
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "project": " ".join(str(item.get("project") or "").split()),
                "id": str(item.get("id") or ""),
                "title": _title(item),
            }
        )
    return rows


def _title(row: dict) -> str:
    """行标题。空白写成「未命名用例」，避免单元格空白。"""
    text = " ".join(str(row.get("title") or "").split())
    return text or _UNTITLED
