"""只读聚合：把可见 Task 填进 GET /api/reports 的平铺信封。"""

from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Case, F, JSONField, Max, Q, Value, When
from django.db.models.functions import Coalesce

from backend.apps.ai_assistant.api import filter_agents_for_user, resolve_assistant_name
from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.api import list_task_attachments, parse_task_result
from backend.apps.task_list.models import Task, TaskAttachment, TaskEvent
from backend.models.constants import TaskKind
from engines.agents.workflow.case_file import validate_platform_yaml

# 分组只需要这 6 列；阶段、展示、明细与起止时间只补给每组的第一行。
_SLIM_COLUMNS = ("seq", "event_type", "is_delta", "step_seq", "attempt", "delta_count")
_DISPLAY_COLUMNS = ("role_name", "role_kind", "model", "media_id", "phase")
_DETAIL_COLUMNS = (
    "duration_ms",
    "started_at",
    "ended_at",
    "input_tokens",
    "cache_input_tokens",
    "output_tokens",
    "cost_total",
)


@dataclass(slots=True)
class _EventRow:
    """聚合用的事件行：先只有分组字段，代表行再补展示、明细与起止时间字段。"""

    seq: int
    event_type: str
    is_delta: bool
    step_seq: int | None
    attempt: int | None
    delta_count: int = 1
    phase: str = ""
    role_name: str = ""
    role_kind: str = ""
    model: str = ""
    media_id: int | None = None
    moment: object = None
    payload: dict | None = None
    duration_ms: int = 0
    started_at: object = None
    ended_at: object = None
    input_tokens: int = 0
    cache_input_tokens: int = 0
    output_tokens: int = 0
    cost_total: object = 0


def _load_details(task_id: int, seqs: list[int]) -> dict[int, dict]:
    """
    按 seq 批量取代表行的展示与明细字段；增量行的 payload 在库内即置空。

    Args:
        task_id: 任务编号。
        seqs: 每组第一行的事件序号。

    Returns:
        序号到字段字典的映射；空列表时返回空映射。
    """
    if not seqs:
        return {}
    rows = (
        TaskEvent.objects.filter(task_id=task_id, seq__in=seqs)
        .annotate(
            moment=Coalesce(F("ended_at"), F("started_at"), F("called_at")),
            report_payload=Case(
                When(is_delta=False, then=F("payload")),
                default=Value(None, output_field=JSONField()),
                output_field=JSONField(),
            ),
        )
        .values("seq", *_DISPLAY_COLUMNS, "moment", "report_payload", *_DETAIL_COLUMNS)
    )
    return {row["seq"]: row for row in rows}


def _load_events(task_id: int) -> list[_EventRow]:
    """
    加载报告所需事件：先取分组列，再只给每组第一行补展示与明细。

    流式增量的 payload 全程不读——报告只用它们计数。

    Args:
        task_id: 任务编号。

    Returns:
        按 seq 升序的事件行；非代表行的展示字段为默认值。
    """
    rows = list(TaskEvent.objects.filter(task_id=task_id).values_list(*_SLIM_COLUMNS))
    rows.sort(key=lambda row: row[0])
    events = [_EventRow(*row) for row in rows]
    spans = _spans(events)
    details = _load_details(task_id, [events[start].seq for start, _ in spans])
    for start, _ in spans:
        event = events[start]
        detail = details.get(event.seq)
        if detail is None:
            continue
        event.role_name = detail["role_name"]
        event.role_kind = detail["role_kind"]
        event.model = detail["model"]
        event.media_id = detail["media_id"]
        event.phase = detail["phase"]
        event.moment = detail["moment"]
        event.payload = detail["report_payload"]
        event.duration_ms = detail["duration_ms"]
        event.started_at = detail["started_at"]
        event.ended_at = detail["ended_at"]
        event.input_tokens = detail["input_tokens"]
        event.cache_input_tokens = detail["cache_input_tokens"]
        event.output_tokens = detail["output_tokens"]
        event.cost_total = detail["cost_total"]
    return events


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
                "task_kind": task.task_kind,
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
    "SOP_STEP_STARTED": "SOP 步骤开始",
    "HintBlockEvent": "运行时注入提醒",
    "ExceedMaxItersEvent": "模型推理轮次用尽",
    "ModelRetryEvent": "模型调用重试",
    "ModelFallbackEvent": "模型回退到备用模型",
}

# 任务头部的 result 只下发摘要；事件明细走 _text，全文不截断。
_RESULT_LIMIT = 240


def _text(text: object) -> str:
    """去掉回车与首尾空白，供事件明细全文展示。"""
    return str(text or "").replace("\r", " ").strip()


def _result_summary(text: object) -> str:
    """任务结果只给摘要，避免报告头部随长文本膨胀。"""
    raw = _text(text)
    if len(raw) <= _RESULT_LIMIT:
        return raw
    return raw[:_RESULT_LIMIT] + "…"


def _money(value) -> str:
    return f"{Decimal(value or 0):.8f}"


def report_cache_meta(user_id: str | None, task_id: str) -> tuple[str, int] | None:
    """
    缓存判定所需的轻量元信息：任务状态与该任务最大事件序号。

    Args:
        user_id: 当前用户编号。
        task_id: 任务编号。

    Returns:
        (状态, 最大 seq)；任务不可见或编号非法时返回 None。
    """
    task = _visible_task(user_id, task_id)
    if task is None:
        return None
    max_seq = TaskEvent.objects.filter(task_id=task.id).aggregate(top=Max("seq"))["top"] or 0
    return (task.status or "").strip().lower(), int(max_seq)


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


def _conclusion(task: Task, events: list[_EventRow]) -> dict:
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


def _detail(event: _EventRow, payload: dict) -> str:
    kind = event.event_type
    if kind == "ReplyStartEvent":
        role = event.role_name or str(payload.get("role") or "")
        model = event.model or str(payload.get("model") or "")
        return _text(" · ".join(part for part in (role, model) if part and part != "-"))
    if kind in ("TextBlockEndEvent", "ThinkingBlockEndEvent"):
        text = _text(payload.get("text"))
        count = payload.get("delta_count")
        if count:
            return _text(f"{text}（{count} 段增量）")
        return text
    if kind == "ToolCallEndEvent":
        return _text(f"{payload.get('tool_name') or '-'} · {payload.get('args') or ''}")
    if kind == "ModelCallEndEvent":
        return (
            f"输入 {event.input_tokens} · 缓存 {event.cache_input_tokens} · "
            f"输出 {event.output_tokens} · 费用 {_money(event.cost_total)}"
        )
    if kind == "DataBlockEndEvent":
        return _text(payload.get("media_type") or "")
    if kind == "ToolResultEndEvent":
        return _text(
            f"{payload.get('tool_name') or '-'} · {payload.get('status') or ''} · "
            f"{payload.get('result') or ''}"
        )
    if kind == "ReplyEndEvent":
        reason = str(payload.get("finished_reason") or "")
        return _text(f"{reason} · {event.duration_ms} ms · 费用 {_money(event.cost_total)}")
    if kind == "SOP_STEP_STARTED":
        step_text = _text(payload.get("step"))
        attempt = int(payload.get("attempt") or 0)
        return _text(f"{step_text} · 第 {attempt} 次尝试") if attempt else step_text
    if kind == "HintBlockEvent":
        return _text(payload.get("hint"))
    if kind == "ExceedMaxItersEvent":
        return "推理轮次用尽，模型被强制收尾"
    if kind == "ModelRetryEvent":
        attempt = int(payload.get("attempt") or 0)
        total = int(payload.get("attempts") or 0)
        delay_ms = int(payload.get("delay_ms") or 0)
        reason = _text(payload.get("reason"))
        head = f"{event.model or '-'} · 第 {attempt}/{total} 次"
        if delay_ms:
            head += f" · {delay_ms} ms 后重试"
        return _text(f"{head} · {reason}") if reason else head
    if kind == "ModelFallbackEvent":
        source = _text(payload.get("from_model")) or "-"
        target = _text(payload.get("to_model")) or "-"
        return _text(f"{source} → {target} · 主模型重试用尽")
    return ""


def _media_ref(event: _EventRow) -> int | None:
    """事件关联的截图编号。图片字节走 /api/tasks/{id}/media/{media_id}/。"""
    return event.media_id


def _item(event: _EventRow, count: int) -> dict:
    payload = event.payload if isinstance(event.payload, dict) else {}
    moment = event.moment
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
        "status": str(payload.get("status") or ""),
        "media_id": _media_ref(event) if count == 1 else None,
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


def _spans(events: list[_EventRow]) -> list[tuple[int, int]]:
    """连续的同一类增量并成一段，返回每段的起始下标与条数。"""
    spans: list[tuple[int, int]] = []
    index = 0
    total = len(events)
    while index < total:
        event = events[index]
        cursor = index + 1
        if event.is_delta:
            while (
                cursor < total
                and events[cursor].is_delta
                and events[cursor].event_type == event.event_type
                and events[cursor].step_seq == event.step_seq
                and events[cursor].attempt == event.attempt
            ):
                cursor += 1
        spans.append((index, cursor - index))
        index = cursor
    return spans


def _grouped(events: list[_EventRow]) -> list[tuple[dict, str]]:
    """连续的同一类增量并成一条，阶段取该组第一条，次数取组内 delta_count 之和。"""
    grouped: list[tuple[dict, str]] = []
    for start, length in _spans(events):
        count = sum(events[start + offset].delta_count for offset in range(length))
        grouped.append((_item(events[start], count), events[start].phase or ""))
    return grouped


_ROLE_LABEL = {
    "executor": "执行",
    "verifier": "验收",
    "planner": "规划",
    "case_writer": "编写",
}


def _role_kind(item: dict) -> str:
    kind = str(item.get("role_kind") or "")
    if kind in _ROLE_LABEL:
        return kind
    name = str(item.get("role_name") or "").lower()
    if "verif" in name:
        return "verifier"
    if "writer" in name:
        return "case_writer"
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


def _event_end(started, ended, duration_ms: int):
    """
    代表事件的结束时刻。

    折叠增量的代表行只带首条增量的 ended_at，用 ``started_at + duration_ms``
    兜住流式尾巴（duration_ms 由 event_store 在折叠时算出）。

    Args:
        started: 开始时刻，可能为空。
        ended: 结束时刻，可能为空。
        duration_ms: 该事件（或该段增量）的持续毫秒数。

    Returns:
        结束时刻；无法确定时返回 None。
    """
    if ended is not None:
        return ended
    if started is not None and duration_ms:
        return started + timedelta(milliseconds=int(duration_ms))
    return None


def _span_ms(start, end) -> int:
    """两个时刻之间的毫秒数；任一为空或为负时返回 0。"""
    if start is None or end is None:
        return 0
    return max(int((end - start).total_seconds() * 1000), 0)


def _fold_round_time(span: dict, item: dict, times: dict[int, "_EventRow"]) -> None:
    """
    把一条代表事件的时间累加进它所在轮次的跨度。

    Args:
        span: 该轮的跨度字典（`start` / `end` / `model_ms` / `has_end`）。
        item: `_grouped()` 产出的条目，取 `seq` 与 `event_type`。
        times: 代表行序号到事件行的映射，用于取起止时间与时长。
    """
    event = times.get(item.get("seq"))
    if event is None:
        return
    if event.started_at is not None:
        if span["start"] is None or event.started_at < span["start"]:
            span["start"] = event.started_at
    if event.ended_at is not None:
        span["has_end"] = True
    end = _event_end(event.started_at, event.ended_at, event.duration_ms)
    if end is not None and (span["end"] is None or end > span["end"]):
        span["end"] = end
    if item.get("event_type") == "ModelCallEndEvent":
        span["model_ms"] += int(event.duration_ms or 0)
    elif item.get("event_type") == "ToolResultEndEvent":
        span["tool_ms"] += int(event.duration_ms or 0)


def _rounds(
    grouped: list[tuple[dict, str]], times: dict[int, "_EventRow"]
) -> tuple[list[dict], dict[int, dict]]:
    """按时间把事件放进图片上的阶段；阶段切换才新开一块。

    Args:
        grouped: `_grouped()` 的产出（条目与阶段）。
        times: 代表行序号到事件行的映射，供跨度累加使用。

    Returns:
        (轮次列表, 轮次编号 → 起止与模型耗时)。
    """
    rounds: list[dict] = []
    spans: dict[int, dict] = {}
    current: dict | None = None
    for item, phase in grouped:
        if current is None or item["event_type"] in ("ReplyStartEvent", "SOP_STEP_STARTED"):
            current = {
                "round_id": len(rounds),
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
            spans[current["round_id"]] = {
                "start": None,
                "end": None,
                "model_ms": 0,
                "tool_ms": 0,
                "has_end": False,
            }
        _fold_round_time(spans[current["round_id"]], item, times)
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
    return rounds, spans


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


def _verdict_maps(events: list[_EventRow]) -> list[dict]:
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


def _interrupt_maps(events: list[_EventRow]) -> list[dict]:
    """每条用例一张表：步骤序号 → 该步被打断的原因（没有则不记）。

    打断事件由引擎在事件流异常结束时写入（例如设备日志为空、日志没盖满 5 秒），
    报告据此在步骤上标注「日志中断」，供人一眼看出失败不是模型判错。
    """
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
        if event.event_type != "StepInterruptedEvent":
            continue
        payload = event.payload if isinstance(event.payload, dict) else {}
        reason = str(payload.get("reason") or "").strip()
        if step and reason:
            current[step] = reason
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


def _group_span(group: list[dict], spans: dict[int, dict]) -> tuple[object, object, bool]:
    """
    一组轮次的墙钟跨度与运行标记。

    Args:
        group: 同一用例（或同一步骤）下的轮次字典。
        spans: 轮次编号 → 起止与模型耗时。

    Returns:
        (最早开始, 最晚结束, 是否有轮次尚未结束)；没有时间戳时为 (None, None, False)。
    """
    start = None
    end = None
    running = False
    for row in group:
        span = spans.get(row.get("round_id"))
        if span is None:
            continue
        if span["start"] is not None and (start is None or span["start"] < start):
            start = span["start"]
        if span["end"] is not None and (end is None or span["end"] > end):
            end = span["end"]
        if span["start"] is not None and not span["has_end"]:
            running = True
    return start, end, running


def _step_span(group: list[dict], seq: int, spans: dict[int, dict]) -> dict:
    """
    某一步骤在该用例内的耗时构成与运行标记。

    Args:
        group: 该用例的全部轮次。
        seq: 步骤序号。
        spans: 轮次编号 → 起止、模型耗时与工具耗时。

    Returns:
        含 `duration_ms`（步骤墙钟）、`model_ms`（该步模型调用合计）、
        `tool_ms`（该步工具返回合计）、`idle_ms`（墙钟减去两者，不为负）与
        `running` 的字段字典；该步没有轮次时各项为 0。
    """
    rows = [row for row in group if int(row.get("step_seq") or 0) == int(seq)]
    start, end, running = _group_span(rows, spans)
    duration = _span_ms(start, end)
    model = sum(int((spans.get(row.get("round_id")) or {}).get("model_ms") or 0) for row in rows)
    tool = sum(int((spans.get(row.get("round_id")) or {}).get("tool_ms") or 0) for row in rows)
    return {
        "duration_ms": duration,
        "model_ms": model,
        "tool_ms": tool,
        "idle_ms": max(duration - model - tool, 0),
        "running": running,
    }


def _annotate(group: list[dict], steps, spans: dict[int, dict]) -> list[dict]:
    for entry in group:
        kind = entry.pop("_kind", "")
        attempt = entry.pop("_attempt", None)
        span = spans.get(entry.get("round_id")) or {}
        entry["role_kind"] = kind
        entry["attempt"] = attempt
        entry["subject"] = _subject(kind, entry.get("step_seq"), steps)
        entry["verdict"] = _lift_note(entry, "verdict")
        entry["handover"] = _lift_note(entry, "handover") or ""
        entry["duty"] = _duty(kind, entry.get("step_seq"), attempt, steps)
        # 轮级给纯模型时长；该轮没有模型调用事件时回退为轮次墙钟
        entry["model_ms"] = int(span.get("model_ms") or 0) or _span_ms(
            span.get("start"), span.get("end")
        )
        # 存量事件没有任何时间戳时不判运行中，避免老任务一直显示「进行中」
        entry["running"] = (not span.get("has_end")) and span.get("start") is not None
    return group


def _flow_cases(
    task: Task, events: list[_EventRow], rounds: list[dict], spans: dict[int, dict]
) -> list[dict]:
    """把轮次按用例切开，并给出每条用例、每一步的结果与耗时。"""
    specs = _task_cases(task)
    groups = _split_round_groups(rounds)
    verdicts = _verdict_maps(events)
    interrupts = _interrupt_maps(events)
    total = max(len(specs), len(groups), 0)
    if not specs and not groups:
        return []
    packed = []
    for index in range(total):
        spec = specs[index] if index < len(specs) else None
        group = groups[index] if index < len(groups) else []
        verdict = verdicts[index] if index < len(verdicts) else {}
        interrupt = interrupts[index] if index < len(interrupts) else {}
        step_defs = list(spec.steps) if spec else []
        case_start, case_end, case_running = _group_span(group, spans)
        steps = []
        if step_defs:
            for seq, step in enumerate(step_defs, start=1):
                steps.append(
                    {
                        "seq": seq,
                        "action": step.action,
                        "expected": step.expected,
                        "outcome": _step_outcome(verdict.get(seq), seq, group),
                        "interrupt": interrupt.get(seq, ""),
                        **_step_span(group, seq, spans),
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
                        "interrupt": interrupt.get(seq, ""),
                        **_step_span(group, seq, spans),
                    }
                )
        title = spec.title if spec else (task.case_title or f"用例 {index + 1}")
        annotated = _annotate(group, step_defs, spans)
        packed.append(
            {
                "title": title,
                "outcome": _case_outcome(steps, bool(group)),
                "steps": steps,
                "round_ids": [entry["round_id"] for entry in annotated],
                "duration_ms": _span_ms(case_start, case_end),
                "running": case_running,
            }
        )
    return packed


def _case_events(events: list[_EventRow]) -> list[dict]:
    """把用例编写任务的事件收成可读时间线。

    Args:
        events: 该任务的事件行，按 seq 升序。

    Returns:
        事件行列表。思考/文本等详情保留全文；结构化交付正文不在事件流里重复。
    """
    rows: list[dict] = []
    for event in events:
        row = _item(event, max(1, int(event.delta_count or 1)))
        handover = row.pop("handover", "")
        row["role_kind"] = _role_kind(row)
        if handover:
            row["detail"] = "结构化交付（完整文档不在此展开）"
        rows.append(row)
    return rows


def _case_authoring_flow(task: Task) -> dict:
    """用例编写任务的报告：入库结果 + 验收判决 + 模型事件流。

    Args:
        task: 用例编写任务。

    Returns:
        与设备任务同信封的流程数据，额外带 case_import、documents 与 events。
    """
    payload = parse_task_result(task.result)
    passed = payload.get("passed")
    status = (task.status or "").strip().lower()
    if passed is True:
        outcome = "PASS"
    elif passed is False or status in {"failed", "cancelled", "stopped"}:
        outcome = "FAIL"
    else:
        outcome = ""
    case_import = payload.get("case_import")
    if not isinstance(case_import, dict):
        case_import = None
    verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), list) else []
    artifact = payload.get("artifact") if isinstance(payload.get("artifact"), dict) else {}
    counts = artifact.get("counts")
    if not isinstance(counts, dict):
        counts = {
            key: len(artifact.get(key) or [])
            for key in ("states", "transitions", "scenarios", "cases")
        }
    facts = payload.get("facts") if isinstance(payload.get("facts"), dict) else {}
    documents = [
        {"filename": row.filename}
        for row in list_task_attachments(task)
        if row.kind == TaskAttachment.KIND_DOCUMENT
    ]
    events = _load_events(task.id)
    return {
        "task": {
            "id": task.id,
            "title": task.title or "",
            "task_kind": TaskKind.CASE_AUTHORING,
            "case_title": task.case_title or "",
            "status": task.status or "",
            "device": "",
            "assistant": resolve_assistant_name(getattr(task, "agent", None)),
            "started_at": _iso(task.started_at or task.created_at),
            "finished_at": _iso(task.finished_at),
            "cost_total": _money(task.cost_total),
            "result": str(payload.get("summary") or _result_summary(task.result)),
        },
        "conclusion": {"outcome": outcome, "verdicts": verdicts, "delivery": ""},
        "rounds": [],
        "cases": [],
        "case_import": case_import,
        "artifact": {
            "counts": counts,
            "diagram": str(artifact.get("diagram") or ""),
        },
        "facts": {
            "blocking": len(facts.get("blocking") or []),
            "warnings": len(facts.get("warnings") or []),
        },
        "documents": documents,
        "events": _case_events(events),
    }


def build_task_flow(user_id: str | None, task_id: str) -> dict | None:
    """可见任务的事件流程。看不见或编号无效时返回 None。"""
    task = _visible_task(user_id, task_id)
    if task is None:
        return None
    if task.task_kind == TaskKind.CASE_AUTHORING:
        return _case_authoring_flow(task)
    events = _load_events(task.id)
    rounds, spans = _rounds(_grouped(events), {event.seq: event for event in events})
    cases = _flow_cases(task, events, rounds, spans)
    return {
        "task": {
            "id": task.id,
            "title": task.title or "",
            "task_kind": task.task_kind,
            "case_title": task.case_title or "",
            "status": task.status or "",
            "device": _device_display(task),
            "assistant": resolve_assistant_name(getattr(task, "agent", None)),
            "started_at": _iso(task.started_at or task.created_at),
            "finished_at": _iso(task.finished_at),
            "cost_total": _money(task.cost_total),
            "result": _result_summary(task.result),
        },
        "conclusion": _conclusion(task, events),
        "rounds": rounds,
        "cases": cases,
    }
