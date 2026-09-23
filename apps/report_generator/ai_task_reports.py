"""只读聚合：把可见 AITask 填进 GET /api/reports 的平铺信封。"""

from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Q

from apps.ai_assistant.api import filter_agents_for_user, resolve_assistant_name
from apps.ai_assistant.models import AIAgent, AITask

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


def _device_display(task: AITask) -> str:
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
    qs = AITask.objects.filter(agent__in=agents).select_related("agent").order_by("-created_at")
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
        "status": True,
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
