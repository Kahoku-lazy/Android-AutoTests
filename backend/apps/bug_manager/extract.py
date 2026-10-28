"""Pure extraction rules: task terminal errors -> classified BUG drafts.

The module deliberately knows nothing about Django models or the database. It reads
only the public task snapshot attributes (id/title/task_kind/status/result/agent) and
returns immutable drafts, so the same rules drive automatic recording and historical
backfill.
"""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from typing import Any

from backend.models.constants import BugCategory, TaskKind, TaskStatus

_TITLE_LIMIT = 500
_UI_FAILURE = "UI 自动化失败"
_UI_TASK_FAILURE = "UI 自动化任务失败"
_UI_TASK_INTERRUPTED = "UI 自动化任务中断"
_CASE_FAILURE = "测试用例编写未通过"
_CASE_INTERRUPTED = "测试用例编写中断"
_CASE_IMPORT_FAILURE = "测试用例入库失败"


@dataclass(frozen=True, slots=True)
class BugDraft:
    """A BUG record ready to be persisted for one task source."""

    category: str
    source_ref: str
    title: str
    detail: str


def build_bug_drafts(task: Any) -> list[BugDraft]:
    """
    Build BUG drafts from a task-like object.

    Args:
        task: Object exposing ``id``, ``title``, ``task_kind``, ``status``,
            ``result``, ``agent_id`` and ``created_by`` attributes.

    Returns:
        Zero or more drafts. Cancelled/running/pending tasks yield an empty list.
    """
    status = _status(task)
    kind = _task_kind(task)
    payload = _parse_result(getattr(task, "result", ""))
    if status in {
        TaskStatus.PENDING,
        TaskStatus.RUNNING,
        TaskStatus.CANCELLED,
    }:
        return []
    if kind == TaskKind.CASE_AUTHORING:
        return _case_drafts(task, status, payload)
    return _ui_drafts(task, status, payload)


def _ui_drafts(task: Any, status: str, payload: dict) -> list[BugDraft]:
    """UI automation: one ticket per failed case, else one task-level ticket."""
    if status not in {TaskStatus.FAILED, TaskStatus.INTERRUPTED}:
        return []
    failed_cases = _failed_case_titles(payload)
    if status == TaskStatus.FAILED and failed_cases:
        return [
            _draft(
                task,
                BugCategory.UI_AUTOMATION,
                f"case:{_case_ref(case)}",
                f"{_UI_FAILURE}：{case}",
                _ui_case_detail(task, payload, case, failed_cases),
            )
            for case in failed_cases
        ]
    prefix = _UI_TASK_INTERRUPTED if status == TaskStatus.INTERRUPTED else _UI_TASK_FAILURE
    return [
        _draft(
            task,
            BugCategory.UI_AUTOMATION,
            "task",
            f"{prefix}：{_task_title(task)}",
            _ui_task_detail(task, payload, failed_cases),
        )
    ]


def _case_drafts(task: Any, status: str, payload: dict) -> list[BugDraft]:
    """Case authoring: verification failure, interruption, or case-import failure."""
    if status == TaskStatus.FAILED:
        return [
            _draft(
                task,
                BugCategory.CASE_AUTHORING,
                "task",
                f"{_CASE_FAILURE}：{_task_title(task)}",
                _case_verification_detail(task, payload),
            )
        ]
    if status == TaskStatus.INTERRUPTED:
        return [
            _draft(
                task,
                BugCategory.CASE_AUTHORING,
                "task",
                f"{_CASE_INTERRUPTED}：{_task_title(task)}",
                _case_verification_detail(task, payload, interrupted=True),
            )
        ]
    imported = payload.get("case_import")
    if status == TaskStatus.COMPLETED and isinstance(imported, dict):
        if str(imported.get("status") or "").lower() == "failed":
            return [
                _draft(
                    task,
                    BugCategory.CASE_AUTHORING,
                    "import",
                    f"{_CASE_IMPORT_FAILURE}：{_task_title(task)}",
                    _case_import_detail(task, payload, imported),
                )
            ]
    return []


def _ui_task_detail(task: Any, payload: dict, failed_cases: list[str]) -> str:
    """Task-level UI failure body with reason, summary and failed-case titles."""
    lines = _common_lines(task)
    if failed_cases:
        _append(lines, "失败用例：" + "；".join(failed_cases))
    _append(lines, "失败原因：" + _text(payload.get("reason")))
    _append(lines, "任务结果：" + _text(payload.get("summary")))
    return "\n".join(lines)


def _ui_case_detail(task: Any, payload: dict, case_title: str, failed_cases: list[str]) -> str:
    """One failed UI case body, keeping other failed cases for context."""
    lines = _common_lines(task)
    _append(lines, f"失败用例：{case_title}")
    others = [case for case in failed_cases if case != case_title]
    if others:
        _append(lines, "同任务其他失败用例：" + "；".join(others))
    _append(lines, "失败原因：" + _text(payload.get("reason")))
    _append(lines, "任务结果：" + _text(payload.get("summary")))
    return "\n".join(lines)


def _case_verification_detail(task: Any, payload: dict, *, interrupted: bool = False) -> str:
    """Case-authoring verification body: summary, verdicts and failed modules."""
    lines = _common_lines(task)
    if interrupted:
        _append(lines, "中断原因：" + (_text(payload.get("summary")) or "服务重启导致任务线程终止"))
    _append(lines, "验收结论：" + _text(payload.get("summary")))
    _append(lines, "未通过原因：" + _text(payload.get("reason")))
    for index, verdict in enumerate(_verdicts(payload), start=1):
        if isinstance(verdict, dict):
            message = _text(verdict.get("message"))
            passed = verdict.get("passed")
            if message:
                label = "通过" if passed is True else "驳回"
                _append(lines, f"验收意见 {index}（{label}）：{message}")
    for module in _failed_modules(payload):
        name = _text(module.get("name")) or _text(module.get("key")) or "未知模块"
        _append(lines, f"模块「{name}」：" + (_text(module.get("message")) or "未通过"))
    return "\n".join(lines)


def _case_import_detail(task: Any, payload: dict, imported: dict) -> str:
    """Case-import failure body: import message and verification context."""
    lines = _common_lines(task)
    _append(lines, "入库状态：" + (_text(imported.get("status")) or "failed"))
    _append(lines, "入库失败原因：" + _text(imported.get("message")))
    _append(lines, "验收结论：" + _text(payload.get("summary")))
    _append(lines, "未通过原因：" + _text(payload.get("reason")))
    return "\n".join(lines)


def _common_lines(task: Any) -> list[str]:
    """Header lines shared by every draft: task snapshot and status."""
    task_id = int(getattr(task, "id", 0) or 0)
    status = _status(task) or "—"
    lines = [f"来源任务：#{task_id} {_task_title(task)}", f"任务状态：{status}"]
    return lines


def _draft(
    task: Any,
    category: str,
    source_ref: str,
    title: str,
    detail: str,
) -> BugDraft:
    """Build a draft and clamp the title to the model limit."""
    return BugDraft(
        category=category,
        source_ref=source_ref,
        title=_title(title),
        detail=detail,
    )


def _failed_case_titles(payload: dict) -> list[str]:
    """Read failed case titles from result.failed, tolerating dict rows and duplicates."""
    raw = payload.get("failed")
    if not isinstance(raw, list):
        return []
    titles: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if isinstance(item, dict):
            text = _text(item.get("title") or item.get("item") or item.get("reason"))
        else:
            text = _text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        titles.append(text)
    return titles


def _verdicts(payload: dict) -> list[dict]:
    """Return verdict rows that are dictionaries."""
    raw = payload.get("verdicts")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _failed_modules(payload: dict) -> list[dict]:
    """Return module rows explicitly marked as not passed."""
    raw = payload.get("modules")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict) and item.get("passed") is False]


def _case_ref(case_title: str) -> str:
    """Stable 16-char source key for a failed case title."""
    normalized = " ".join(str(case_title or "").split()).lower()
    if not normalized:
        normalized = "untitled"
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def _parse_result(raw: Any) -> dict:
    """Parse Task.result JSON, wrapping plain text as ``{"summary": text}``."""
    if isinstance(raw, dict):
        return raw
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return {"summary": text}
    if isinstance(parsed, dict):
        return parsed
    return {"summary": str(parsed)}


def _task_kind(task: Any) -> str:
    """Task kind normalized to a string; defaults to device control."""
    return str(getattr(task, "task_kind", "") or TaskKind.DEVICE_CONTROL)


def _status(task: Any) -> str:
    """Task status normalized to lowercase."""
    return str(getattr(task, "status", "") or "").strip().lower()


def _task_title(task: Any) -> str:
    """Task title for display, never empty."""
    return _text(getattr(task, "title", "")) or "未命名任务"


def _title(value: str) -> str:
    """Clamp a BUG title to the database column limit."""
    text = _text(value)
    return text[:_TITLE_LIMIT]


def _text(value: Any) -> str:
    """Collapse whitespace and strip a value for a compact display field."""
    return " ".join(str(value or "").split())


def _append(lines: list[str], value: str) -> None:
    """Append a non-empty line unless the same line already exists."""
    text = _text(value)
    if text and text not in lines:
        lines.append(text)
