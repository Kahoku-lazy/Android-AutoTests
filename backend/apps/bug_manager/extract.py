from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from typing import Any

from backend.models.constants import BugCategory, TaskKind, TaskStatus
from utils.logs import backend_log

_TITLE_LIMIT = 500
_UI_FAILURE = "UI 自动化失败"
_UI_TASK_FAILURE = "UI 自动化任务失败"
_UI_TASK_INTERRUPTED = "UI 自动化任务中断"
_CASE_FAILURE = "测试用例编写未通过"
_CASE_INTERRUPTED = "测试用例编写中断"
_CASE_IMPORT_FAILURE = "测试用例入库失败"


@dataclass(frozen=True, slots=True)
class BugDraft:
    category: str
    source_ref: str
    title: str
    detail: str
    failure: dict | None = None


def build_bug_drafts(task: Any) -> list[BugDraft]:
    status = _status(task)
    kind = _task_kind(task)
    payload = _parse_result(getattr(task, "result", ""))
    if status in {
        TaskStatus.PENDING,
        TaskStatus.RUNNING,
        TaskStatus.CANCELLED,
    }:
        return []
    frozen = str(getattr(task, "kind", "") or "")
    if frozen == "requirement_breakdown":
        return _requirement_drafts(task, status, payload)
    if frozen == "case_authoring" or kind == TaskKind.CASE_AUTHORING:
        return _case_drafts(task, status, payload)
    if frozen == "ui_automation":
        return (
            [_workflow_draft(task, status, payload)]
            if status
            in {
                TaskStatus.FAILED,
                TaskStatus.INTERRUPTED,
            }
            else []
        )
    if kind == TaskKind.ASSISTANT_SOP and _failed_steps(payload):
        return [_workflow_draft(task, status, payload)]
    return _ui_drafts(task, status, payload)


_KIND_LABEL = {
    "verdict": "步骤未通过",
    "provider": "模型拒绝",
    "device": "设备命令失败",
    "platform": "平台错误",
    "interrupted": "已中断",
}


def _workflow_draft(task: Any, status: str, payload: dict) -> BugDraft:
    steps = _failed_steps(payload)
    first = steps[0]
    name = str(first.get("name") or "未记录")
    kind = str(first.get("kind") or "")
    if kind == "verdict":
        title = f"步骤未通过：{name}"
    elif status == TaskStatus.INTERRUPTED or kind == "interrupted":
        title = f"任务中断：{_task_title(task)}"
    else:
        title = f"{_KIND_LABEL.get(kind, _UI_TASK_FAILURE)}：{_task_title(task)}"
    lines = [
        *_common_lines(task),
        f"出错步骤：第 {first.get('seq') or 1} 步 {name}",
        f"原因类别：{_KIND_LABEL.get(kind, kind or '未记录')}",
        f"期望结果：{first.get('expected') or '未记录'}",
        f"实际结果：{first.get('actual') or '未记录'}",
    ]
    if len(steps) > 1:
        lines.append(
            "其他失败步骤：" + "；".join(str(item.get("name") or "未记录") for item in steps[1:])
        )
    return _draft(
        task,
        BugCategory.UI_AUTOMATION,
        "task",
        title,
        "\n".join(lines),
        {"steps": steps},
    )


def _failed_steps(payload: dict) -> list[dict]:
    raw = payload.get("failed_steps")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _ui_drafts(task: Any, status: str, payload: dict) -> list[BugDraft]:
    if status not in {TaskStatus.FAILED, TaskStatus.INTERRUPTED}:
        return []
    drafts: list[BugDraft] = []
    reason, step = _interrupt_reason(task)
    if reason:
        drafts.append(
            _draft(
                task,
                BugCategory.UI_AUTOMATION,
                "task:log-interrupt",
                f"设备日志中断：{_task_title(task)}",
                "\n".join(
                    [
                        *_common_lines(task),
                        f"中断步骤：第 {step} 步" if step else "中断步骤：—",
                        f"中断原因：{reason}",
                        "说明：事件流因设备日志被判为空/时间不满足而中断，这一步没有完成，"
                        "不是模型判错；请检查串口采集与灯具连接后重跑。",
                    ]
                ),
            )
        )
    kind = str(payload.get("failure_kind") or "")
    if status == TaskStatus.FAILED and kind in {"provider", "device", "platform"}:
        drafts.append(
            _draft(
                task,
                BugCategory.UI_AUTOMATION,
                f"task:{kind}",
                f"{_UI_TASK_FAILURE}：{_task_title(task)}",
                _ui_task_detail(task, payload, []),
            )
        )
        return drafts
    failed_cases = _failed_case_titles(payload)
    if status == TaskStatus.FAILED and failed_cases:
        drafts.extend(
            _draft(
                task,
                BugCategory.UI_AUTOMATION,
                f"case:{_case_ref(case)}",
                f"{_UI_FAILURE}：{case}",
                _ui_case_detail(task, payload, case, failed_cases),
            )
            for case in failed_cases
        )
        return drafts
    prefix = _UI_TASK_INTERRUPTED if status == TaskStatus.INTERRUPTED else _UI_TASK_FAILURE
    drafts.append(
        _draft(
            task,
            BugCategory.UI_AUTOMATION,
            "task",
            f"{prefix}：{_task_title(task)}",
            _ui_task_detail(task, payload, failed_cases),
        )
    )
    return drafts


def _requirement_drafts(task: Any, status: str, payload: dict) -> list[BugDraft]:
    if payload.get("passed") or payload.get("modules"):
        return []
    if status not in {TaskStatus.FAILED, TaskStatus.INTERRUPTED}:
        return []
    return [
        _draft(
            task,
            BugCategory.REQUIREMENT_BREAKDOWN,
            "task",
            f"需求拆解未形成模块：{_task_title(task)}",
            "\n".join(
                [*_common_lines(task), f"原因：{payload.get('reason') or '未形成合法模块清单'}"]
            ),
        )
    ]


def _case_drafts(task: Any, status: str, payload: dict) -> list[BugDraft]:
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
    lines = _common_lines(task)
    if failed_cases:
        _append(lines, "失败用例：" + "；".join(failed_cases))
    _append(lines, "失败原因：" + _text(payload.get("reason")))
    _append(lines, "任务结果：" + _text(payload.get("summary")))
    return "\n".join(lines)


def _ui_case_detail(task: Any, payload: dict, case_title: str, failed_cases: list[str]) -> str:
    lines = _common_lines(task)
    _append(lines, f"失败用例：{case_title}")
    others = [case for case in failed_cases if case != case_title]
    if others:
        _append(lines, "同任务其他失败用例：" + "；".join(others))
    _append(lines, "失败原因：" + _text(payload.get("reason")))
    _append(lines, "任务结果：" + _text(payload.get("summary")))
    return "\n".join(lines)


def _case_verification_detail(task: Any, payload: dict, *, interrupted: bool = False) -> str:
    lines = _common_lines(task)
    if interrupted:
        _append(
            lines,
            "中断原因："
            + (
                _text(payload.get("reason"))
                or _text(payload.get("summary"))
                or "进程退出时任务仍在执行"
            ),
        )
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
    lines = _common_lines(task)
    _append(lines, "入库状态：" + (_text(imported.get("status")) or "failed"))
    _append(lines, "入库失败原因：" + _text(imported.get("message")))
    _append(lines, "验收结论：" + _text(payload.get("summary")))
    _append(lines, "未通过原因：" + _text(payload.get("reason")))
    return "\n".join(lines)


def _interrupt_reason(task: Any) -> tuple[str, int]:
    task_id = int(getattr(task, "id", 0) or 0)
    if not task_id:
        return "", 0
    try:
        from backend.apps.task_list.models import TaskEvent

        row = (
            TaskEvent.objects.filter(task_id=task_id, event_type="StepInterruptedEvent")
            .order_by("-seq")
            .only("payload", "step_seq")
            .first()
        )
    except Exception as exc:  # noqa: BLE001 - 台账只做补充说明，读不到就当没有
        backend_log.warning(f"读取中断事件失败：{exc}")
        return "", 0
    if row is None:
        return "", 0
    payload = row.payload if isinstance(row.payload, dict) else {}
    return str(payload.get("reason") or "").strip(), int(row.step_seq or 0)


def _common_lines(task: Any) -> list[str]:
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
    failure: dict | None = None,
) -> BugDraft:
    return BugDraft(
        category=category,
        source_ref=source_ref,
        title=_title(title),
        detail=detail,
        failure=failure,
    )


def _failed_case_titles(payload: dict) -> list[str]:
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
    raw = payload.get("verdicts")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _failed_modules(payload: dict) -> list[dict]:
    raw = payload.get("modules")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict) and item.get("passed") is False]


def _case_ref(case_title: str) -> str:
    normalized = " ".join(str(case_title or "").split()).lower()
    if not normalized:
        normalized = "untitled"
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def _parse_result(raw: Any) -> dict:
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
    return str(getattr(task, "task_kind", "") or TaskKind.DEVICE_CONTROL)


def _status(task: Any) -> str:
    return str(getattr(task, "status", "") or "").strip().lower()


def _task_title(task: Any) -> str:
    return _text(getattr(task, "title", "")) or "未命名任务"


def _title(value: str) -> str:
    text = _text(value)
    return text[:_TITLE_LIMIT]


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _append(lines: list[str], value: str) -> None:
    text = _text(value)
    if text and text not in lines:
        lines.append(text)
