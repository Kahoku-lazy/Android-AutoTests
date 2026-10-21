"""只读聚合：把可见 Task 填进 GET /api/reports 的平铺信封。"""

from __future__ import annotations

import json

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q

from apps.ai_assistant.api import filter_agents_for_user, resolve_assistant_name
from apps.ai_assistant.models import AIAgent
from apps.task_list.api import list_task_attachments
from apps.task_list.models import Task, TaskAttachment, TaskEvent
from engines.agents.workflow.case_file import validate_platform_yaml

PASS_STATUSES = frozenset({"completed", "success"})
FAIL_STATUSES = frozenset({"failed"})
ALLOWED_CHART_RANGES = (7, 30, 90)


def parse_chart_range(raw: str | None) -> int:
    try:
        days = int((raw or "30").strip())
    except ValueError:
        days = 30
    if days not in ALLOWED_CHART_RANGES:
        days = 30
    return days


def empty_trend(range_days: int) -> dict:
    end = date.today()
    start = end - timedelta(days=range_days - 1)
    dates: list[str] = []
    labels: list[str] = []
    zeros: list[int] = []
    cursor = start
    while cursor <= end:
        dates.append(cursor.isoformat())
        labels.append(f"{cursor.month:02d}-{cursor.day:02d}")
        zeros.append(0)
        cursor += timedelta(days=1)
    return {
        "range_days": range_days,
        "dates": dates,
        "labels": labels,
        "pass": list(zeros),
        "fail": list(zeros),
        "rate": list(zeros),
    }


def format_duration(started_at, finished_at) -> str:
    if not started_at or not finished_at:
        return "—"
    total = int((finished_at - started_at).total_seconds())
    if total < 0:
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _iso(dt) -> str:
    return dt.isoformat() if dt else ""


def _pass_rate(n_pass: int, n_fail: int) -> float:
    terminal = n_pass + n_fail
    if terminal == 0:
        return 0.0
    return round(100.0 * n_pass / terminal, 1)


def _device_display(task: Task) -> str:
    label = (task.device_label or "").strip()
    if label:
        return label
    return (task.device_serial or "").strip()


def build_report_list(
    user_id: str | None,
    *,
    range_days: int = 30,
    start_date: str = "",
    end_date: str = "",
    run_id: str = "",
    task_name: str = "",
    device_serial: str = "",
    creator: str = "",
) -> dict:
    """组装 {status, summary, trend, runs}；不写库。"""
    trend = empty_trend(range_days)
    empty = {
        "status": True,
        "summary": {
            "total_runs": 0,
            "total_iterations": 0,
            "total_pass": 0,
            "total_fail": 0,
            "pass_rate": 0.0,
        },
        "bug_summary": {},
        "trend": trend,
        "runs": [],
    }
    if not user_id:
        return empty
    try:
        int(user_id)
    except (ValueError, TypeError):
        return empty

    agents = filter_agents_for_user(AIAgent.objects.all(), user_id)
    qs = Task.objects.filter(agent__in=agents).select_related("agent").order_by("-created_at")
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)
    if run_id:
        try:
            qs = qs.filter(pk=int(run_id))
        except ValueError:
            qs = qs.none()
    if task_name:
        qs = qs.filter(title__icontains=task_name)
    if device_serial:
        qs = qs.filter(
            Q(device_label__icontains=device_serial) | Q(device_serial__icontains=device_serial)
        )

    date_index = {d: i for i, d in enumerate(trend["dates"])}
    creator_q = creator.strip().lower()
    runs: list[dict] = []
    n_pass = 0
    n_fail = 0
    for task in qs:
        assistant = resolve_assistant_name(getattr(task, "agent", None))
        if creator_q and creator_q not in assistant.lower():
            continue
        status_key = (task.status or "").lower()
        if status_key in PASS_STATUSES:
            n_pass += 1
        elif status_key in FAIL_STATUSES:
            n_fail += 1
        created = task.created_at.date().isoformat() if task.created_at else ""
        idx = date_index.get(created)
        if idx is not None:
            if status_key in PASS_STATUSES:
                trend["pass"][idx] += 1
            elif status_key in FAIL_STATUSES:
                trend["fail"][idx] += 1
        started = task.started_at or task.created_at
        runs.append(
            {
                "run_id": str(task.id),
                "device_serial": _device_display(task),
                "task_name": task.title or "",
                "creator": assistant,
                "status": task.status or "",
                "duration": format_duration(task.started_at, task.finished_at),
                "started_at": _iso(started),
            }
        )

    for i, (p_count, f_count) in enumerate(zip(trend["pass"], trend["fail"])):
        trend["rate"][i] = _pass_rate(p_count, f_count)

    return {
        "summary": {
            "total_runs": len(runs),
            "total_iterations": 0,
            "total_pass": n_pass,
            "total_fail": n_fail,
            "pass_rate": _pass_rate(n_pass, n_fail),
        },
        "bug_summary": {},
        "trend": trend,
        "runs": runs,
    }


_PHASE_TITLE = {
    "开始": "开始",
    "推理": "推理阶段",
    "执行": "执行阶段",
    "结束": "结束",
}

_EVENT_LABEL = {
    "ReplyStartEvent": "生命周期事件：智能体开始新的回复",
    "ModelCallStartEvent": "模型调用事件：模型 API 调用开始",
    "TextBlockStartEvent": "文本流式事件：新的文本块开始",
    "TextBlockDeltaEvent": "文本流式事件：增量文本内容到达",
    "TextBlockEndEvent": "文本流式事件：文本块完成",
    "ThinkingBlockEndEvent": "思考块完成",
    "DataBlockStartEvent": "数据流式事件：新的数据块开始",
    "DataBlockDeltaEvent": "数据流式事件：增量二进制数据到达",
    "DataBlockEndEvent": "数据流式事件：数据块完成",
    "ToolCallStartEvent": "工具调用流式事件：智能体开始一次工具调用",
    "ToolCallDeltaEvent": "工具调用流式事件：增量工具参数到达",
    "ToolCallEndEvent": "工具调用流式事件：工具调用参数完成",
    "ModelCallEndEvent": "模型调用事件：模型 API 调用完成",
    "ToolResultStartEvent": "工具结果流式事件：工具开始执行",
    "ToolResultTextDeltaEvent": "工具结果流式事件：增量文本输出到达",
    "ToolResultDataDeltaEvent": "工具结果流式事件：增量二进制数据到达",
    "ToolResultEndEvent": "工具结果流式事件：工具执行完成",
    "ReplyEndEvent": "生命周期事件：智能体完成回复",
}

_DETAIL_LIMIT = 240


def _clip(text: object) -> str:
    raw = str(text or "").replace("\r", " ").strip()
    if len(raw) <= _DETAIL_LIMIT:
        return raw
    return raw[:_DETAIL_LIMIT] + "…"


def _money(value) -> str:
    return f"{Decimal(value or 0):.8f}"


def _visible_task(user_id: str | None, task_id: str):
    if not user_id:
        return None
    try:
        pk = int(task_id)
    except (TypeError, ValueError):
        return None
    agents = filter_agents_for_user(AIAgent.objects.all(), user_id)
    return Task.objects.filter(pk=pk, agent__in=agents).select_related("agent").first()


def _args(payload: dict) -> dict:
    raw = payload.get("args")
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _passed(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _conclusion(task: Task, events: list[TaskEvent]) -> dict:
    """从验收结构化输出取出判决。不读文本日志。"""
    verdicts: list[dict] = []
    delivery = ""
    for event in events:
        if event.event_type != "ToolCallEndEvent":
            continue
        payload = event.payload if isinstance(event.payload, dict) else {}
        args = _args(payload)
        if payload.get("tool_name") == "GenerateStructuredOutput" and "passed" in args:
            verdicts.append(
                {
                    "passed": _passed(args.get("passed")),
                    "message": str(args.get("message") or ""),
                    "role_name": event.role_name or "",
                    "step_seq": event.step_seq,
                    "attempt": event.attempt,
                }
            )
        elif args.get("handover"):
            delivery = str(args.get("handover") or "")
    status = (task.status or "").lower()
    if status in {"failed", "cancelled", "stopped"}:
        outcome = "FAIL"
    elif verdicts and verdicts[-1]["passed"] and status in {"completed", "success"}:
        outcome = "PASS"
    elif verdicts and not verdicts[-1]["passed"]:
        outcome = "FAIL"
    else:
        outcome = ""
    return {"outcome": outcome, "verdicts": verdicts, "delivery": delivery}


def _detail(event: TaskEvent, payload: dict) -> str:
    kind = event.event_type
    if kind == "ReplyStartEvent":
        role = event.role_name or str(payload.get("role") or "")
        model = event.model or str(payload.get("model") or "")
        return _clip(" · ".join(part for part in (role, model) if part and part != "-"))
    if kind in ("TextBlockEndEvent", "ThinkingBlockEndEvent"):
        text = _clip(payload.get("text"))
        count = payload.get("delta_count")
        if count:
            return _clip(f"{text}（{count} 段增量）")
        return text
    if kind == "ToolCallEndEvent":
        return _clip(f"{payload.get('tool_name') or '-'} · {payload.get('args') or ''}")
    if kind == "ModelCallEndEvent":
        return (
            f"输入 {event.input_tokens} · 缓存 {event.cache_input_tokens} · "
            f"输出 {event.output_tokens} · 费用 {_money(event.cost_total)}"
        )
    if kind == "DataBlockEndEvent":
        return _clip(payload.get("media_type") or "")
    if kind == "ToolResultEndEvent":
        return _clip(
            f"{payload.get('tool_name') or '-'} · {payload.get('status') or ''} · "
            f"{payload.get('result') or ''}"
        )
    if kind == "ReplyEndEvent":
        reason = str(payload.get("finished_reason") or "")
        return _clip(f"{reason} · {event.duration_ms} ms · 费用 {_money(event.cost_total)}")
    return ""


def _thumb(event: TaskEvent) -> str:
    media = event.media
    if media is None or not media.thumb_b64:
        return ""
    kind = (media.media_type or "image/jpeg").split(";")[0]
    return f"data:{kind};base64,{media.thumb_b64}"


def _item(event: TaskEvent, count: int) -> dict:
    payload = event.payload if isinstance(event.payload, dict) else {}
    moment = event.ended_at or event.started_at or event.called_at
    row = {
        "seq": event.seq,
        "event_type": event.event_type,
        "label": _EVENT_LABEL.get(event.event_type, event.event_type),
        "detail": _detail(event, payload),
        "time": _iso(moment),
        "count": count,
        "step_seq": event.step_seq,
        "attempt": event.attempt,
        "role_name": event.role_name or "",
        "role_kind": event.role_kind or "",
        "model": event.model or "",
        "thumb": _thumb(event) if count == 1 else "",
    }
    if event.event_type == "ToolCallEndEvent":
        args = _args(payload)
        if args.get("handover"):
            row["handover"] = str(args.get("handover") or "")
        if payload.get("tool_name") == "GenerateStructuredOutput" and "passed" in args:
            row["verdict"] = {
                "passed": _passed(args.get("passed")),
                "message": str(args.get("message") or ""),
            }
    return row


def _grouped(events: list[TaskEvent]) -> list[tuple[dict, str]]:
    """连续的同一类增量并成一条，阶段取该组第一条。"""
    grouped: list[tuple[dict, str]] = []
    index = 0
    while index < len(events):
        event = events[index]
        count = 1
        if event.is_delta:
            cursor = index + 1
            while (
                cursor < len(events)
                and events[cursor].is_delta
                and events[cursor].event_type == event.event_type
                and events[cursor].step_seq == event.step_seq
                and events[cursor].attempt == event.attempt
            ):
                count += 1
                cursor += 1
            index = cursor
        else:
            index += 1
        grouped.append((_item(event, count), event.phase or ""))
    return grouped


_ROLE_LABEL = {
    "executor": "执行",
    "verifier": "验收",
    "planner": "规划",
}


def _role_kind(item: dict) -> str:
    kind = str(item.get("role_kind") or "")
    if kind in _ROLE_LABEL:
        return kind
    name = str(item.get("role_name") or "").lower()
    if "verif" in name:
        return "verifier"
    if "plan" in name:
        return "planner"
    if "execut" in name:
        return "executor"
    return ""


def _task_cases(task: Task):
    """按执行顺序取出要跑的用例。指定了用例标题时只留那一条。"""
    config = next(
        (row for row in list_task_attachments(task) if row.kind == TaskAttachment.KIND_CONFIG),
        None,
    )
    if config is None or not (config.body or "").strip():
        return []
    cases, reason = validate_platform_yaml(config.body)
    if reason or not cases:
        return []
    wanted = (task.case_title or "").strip()
    if wanted:
        return [case for case in cases if case.title == wanted]
    return list(cases)


def _duty(kind: str, step_seq, attempt, steps) -> str:
    """这一轮在做的事：带上步骤序号。执行者用动作，验收者用要达成的结果。"""
    label = _ROLE_LABEL.get(kind, "")
    text = ""
    if steps and step_seq:
        index = int(step_seq) - 1
        if 0 <= index < len(steps):
            step = steps[index]
            text = step.expected if kind == "verifier" else step.action
    if label and attempt and int(attempt) > 1:
        label = f"第 {int(attempt)} 次{label}"
    if label and text:
        action = f"{label}：{text}"
    elif label and step_seq:
        action = label
    else:
        action = ""
    head = f"步骤 {int(step_seq)}" if step_seq else ""
    return " · ".join(part for part in (head, action) if part)


def _rounds(grouped: list[tuple[dict, str]]) -> list[dict]:
    """按时间把事件放进图片上的阶段；阶段切换才新开一块。"""
    rounds: list[dict] = []
    current: dict | None = None
    for item, phase in grouped:
        if current is None or item["event_type"] == "ReplyStartEvent":
            current = {
                "role": "",
                "role_name": "",
                "model": "",
                "duty": "",
                "step_seq": None,
                "_kind": "",
                "_attempt": None,
                "blocks": [],
            }
            rounds.append(current)
        kind = _role_kind(item)
        if kind and not current["_kind"]:
            current["_kind"] = kind
        if item.get("role_name") and not current["role"]:
            current["role"] = item["role_name"]
        if item.get("step_seq") and current["step_seq"] is None:
            current["step_seq"] = item["step_seq"]
            current["_attempt"] = item.get("attempt")
        if item.get("model") and not current["model"]:
            current["model"] = item["model"]
        if item["event_type"] == "ReplyStartEvent":
            current["role_name"] = item["detail"]
        title = _PHASE_TITLE.get(phase, phase or "其它")
        blocks = current["blocks"]
        if not blocks or blocks[-1]["phase"] != phase:
            blocks.append({"phase": phase, "title": title, "items": []})
        blocks[-1]["items"].append(item)
    return rounds


def _split_round_groups(rounds: list[dict]) -> list[list[dict]]:
    """步骤序号倒退表示下一条用例开始。同一用例内的重试序号不会变小。"""
    groups: list[list[dict]] = []
    current: list[dict] = []
    last = 0
    for entry in rounds:
        step = int(entry.get("step_seq") or 0)
        if current and step and last and step < last:
            groups.append(current)
            current = []
            last = 0
        current.append(entry)
        if step:
            last = step
    if current:
        groups.append(current)
    return groups


def _verdict_maps(events: list[TaskEvent]) -> list[dict]:
    """每条用例一张表：步骤序号 → 该步最后一次判决是否通过。"""
    maps: list[dict] = []
    current: dict = {}
    last = 0
    saw = False
    for event in events:
        step = int(event.step_seq or 0)
        if step and last and step < last:
            maps.append(current)
            current = {}
            last = 0
        if step:
            last = step
            saw = True
        if event.event_type != "ToolCallEndEvent" or not step:
            continue
        payload = event.payload if isinstance(event.payload, dict) else {}
        args = _args(payload)
        if payload.get("tool_name") == "GenerateStructuredOutput" and "passed" in args:
            current[step] = _passed(args.get("passed"))
    if saw or current:
        maps.append(current)
    return maps


def _step_outcome(passed, seq: int, group: list[dict]) -> str:
    if passed is True:
        return "PASS"
    if passed is False:
        return "FAIL"
    reached = any(int(entry.get("step_seq") or 0) == seq for entry in group)
    return "未完成" if reached else "未执行"


def _case_outcome(steps: list[dict], started: bool) -> str:
    if not started:
        return "未执行"
    if not steps:
        return "未完成"
    marks = [step["outcome"] for step in steps]
    if all(mark == "PASS" for mark in marks):
        return "PASS"
    if any(mark == "FAIL" for mark in marks):
        return "FAIL"
    return "未完成"


def _subject(kind: str, step_seq, steps) -> str:
    if not steps or not step_seq:
        return ""
    index = int(step_seq) - 1
    if not 0 <= index < len(steps):
        return ""
    step = steps[index]
    return step.expected if kind == "verifier" else step.action


def _lift_note(entry: dict, key: str):
    found = None
    for block in entry.get("blocks") or []:
        for item in block.get("items") or []:
            value = item.pop(key, None)
            if value:
                found = value
    return found


def _annotate(group: list[dict], steps) -> list[dict]:
    for entry in group:
        kind = entry.pop("_kind", "")
        attempt = entry.pop("_attempt", None)
        entry["role_kind"] = kind
        entry["attempt"] = attempt
        entry["subject"] = _subject(kind, entry.get("step_seq"), steps)
        entry["verdict"] = _lift_note(entry, "verdict")
        entry["handover"] = _lift_note(entry, "handover") or ""
        entry["duty"] = _duty(kind, entry.get("step_seq"), attempt, steps)
    return group


def _flow_cases(task: Task, events: list[TaskEvent], rounds: list[dict]) -> list[dict]:
    """把轮次按用例切开，并给出每条用例、每一步的结果。"""
    specs = _task_cases(task)
    groups = _split_round_groups(rounds)
    verdicts = _verdict_maps(events)
    total = max(len(specs), len(groups), 0)
    if not specs and not groups:
        return []
    packed = []
    for index in range(total):
        spec = specs[index] if index < len(specs) else None
        group = groups[index] if index < len(groups) else []
        verdict = verdicts[index] if index < len(verdicts) else {}
        step_defs = list(spec.steps) if spec else []
        steps = []
        if step_defs:
            for seq, step in enumerate(step_defs, start=1):
                steps.append(
                    {
                        "seq": seq,
                        "action": step.action,
                        "expected": step.expected,
                        "outcome": _step_outcome(verdict.get(seq), seq, group),
                    }
                )
        else:
            seen = sorted({int(entry["step_seq"]) for entry in group if entry.get("step_seq")})
            for seq in seen:
                steps.append(
                    {
                        "seq": seq,
                        "action": "",
                        "expected": "",
                        "outcome": _step_outcome(verdict.get(seq), seq, group),
                    }
                )
        title = spec.title if spec else (task.case_title or f"用例 {index + 1}")
        packed.append(
            {
                "title": title,
                "outcome": _case_outcome(steps, bool(group)),
                "steps": steps,
                "rounds": _annotate(group, step_defs),
            }
        )
    return packed


def build_task_flow(user_id: str | None, task_id: str) -> dict | None:
    """可见任务的事件流程。看不见或编号无效时返回 None。"""
    task = _visible_task(user_id, task_id)
    if task is None:
        return None
    events = list(TaskEvent.objects.filter(task_id=task.id).select_related("media").order_by("seq"))
    rounds = _rounds(_grouped(events))
    return {
        "task": {
            "id": task.id,
            "title": task.title or "",
            "case_title": task.case_title or "",
            "status": task.status or "",
            "device": _device_display(task),
            "assistant": resolve_assistant_name(getattr(task, "agent", None)),
            "started_at": _iso(task.started_at or task.created_at),
            "finished_at": _iso(task.finished_at),
            "cost_total": _money(task.cost_total),
            "result": _clip(task.result),
        },
        "conclusion": _conclusion(task, events),
        "rounds": rounds,
        "cases": _flow_cases(task, events, rounds),
    }
