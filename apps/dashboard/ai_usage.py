"""Dashboard AI 用量聚合 — 只读小时用量表。

任务数仍按可见任务计。token、缓存命中和费用按智能体整份合计，不按角色拆开。
纯只读聚合，无任何写操作。
"""

from datetime import timedelta
from decimal import Decimal

from django.db import OperationalError, ProgrammingError
from django.db.models import Sum
from django.utils import timezone

from apps.ai_assistant.api import filter_agents_for_user, resolve_assistant_name
from apps.ai_assistant.models import AIAgent, AITask, AIUsageHourly


def _agents(user_id):
    return list(filter_agents_for_user(AIAgent.objects.all(), user_id))


def _task_qs(user_id):
    """当前用户可见智能体产生的任务。任务数仍按任务表计。"""
    return AITask.objects.filter(agent__in=_agents(user_id))


def _hourly_qs(agent_ids):
    if not agent_ids:
        return AIUsageHourly.objects.none()
    return AIUsageHourly.objects.filter(agent_id__in=agent_ids)


def _money(value) -> float:
    amount = Decimal(value or 0).quantize(Decimal("0.00000001"))
    return float(amount)


def _sum_usage(qs):
    """小时用量合计：输入、输出、缓存命中、总费用。"""
    try:
        row = qs.aggregate(
            inp=Sum("input_tokens"),
            out=Sum("output_tokens"),
            hit=Sum("cache_input_tokens"),
            cost=Sum("cost_total"),
        )
    except (OperationalError, ProgrammingError):
        return 0, 0, 0, 0.0
    return (
        int(row["inp"] or 0),
        int(row["out"] or 0),
        int(row["hit"] or 0),
        _money(row["cost"]),
    )


def _agg_by_role(qs):
    """按角色种类合计 token。执行者与验收者并进同一个智能体之前，角色芯片仍分开。"""
    result = {}
    try:
        rows = qs.values("role_kind").annotate(
            inp=Sum("input_tokens"),
            out=Sum("output_tokens"),
            hit=Sum("cache_input_tokens"),
        )
    except (OperationalError, ProgrammingError):
        return result
    for row in rows:
        role = row["role_kind"] or ""
        if role not in {"planner", "executor", "verifier"}:
            continue
        result[role] = {
            "input_tokens": int(row["inp"] or 0),
            "output_tokens": int(row["out"] or 0),
            "cache_input_tokens": int(row["hit"] or 0),
        }
    return result


def _agent_usage(agents):
    """每个智能体一份合计，不按角色或模型拆开。"""
    try:
        grouped = (
            _hourly_qs([agent.id for agent in agents])
            .values("agent_id")
            .annotate(
                inp=Sum("input_tokens"),
                out=Sum("output_tokens"),
                hit=Sum("cache_input_tokens"),
                cost=Sum("cost_total"),
            )
        )
    except (OperationalError, ProgrammingError):
        grouped = []
    rows = {row["agent_id"]: row for row in grouped}
    usage = []
    for agent in agents:
        row = rows.get(agent.id) or {}
        usage.append(
            {
                "id": agent.id,
                "name": resolve_assistant_name(agent) or agent.name,
                "input_tokens": int(row.get("inp") or 0),
                "output_tokens": int(row.get("out") or 0),
                "cache_hit_tokens": int(row.get("hit") or 0),
                "cost_total": f"{Decimal(row.get('cost') or 0):.8f}",
            }
        )
    return usage


def ai_usage_stats(user_id):
    """AI 用量聚合（今日/累计），含 DeepSeek 费用。

    返回：任务数量、输入/输出 token、缓存命中 token/命中率、平均每任务 token、
    DeepSeek 费用，各指标分 today / total 两组口径。
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    agents = _agents(user_id)
    task_qs = AITask.objects.filter(agent__in=agents)
    hourly = _hourly_qs([agent.id for agent in agents])
    today_hourly = hourly.filter(stat_date=today_start.date())

    def safe_count(qs):
        try:
            return qs.count()
        except (OperationalError, ProgrammingError):
            return 0

    task_total = safe_count(task_qs)
    task_today = safe_count(task_qs.filter(created_at__gte=today_start))

    in_t, out_t, hit_t, cost_t = _sum_usage(hourly)
    in_d, out_d, hit_d, cost_d = _sum_usage(today_hourly)

    def rate(hit, inp):
        # 缓存命中率 = 命中 token / 输入 token，返回百分比（0-100，1 位小数）
        return round(hit / inp * 100, 1) if inp else 0.0

    def avg(inp, out, cnt):
        return int((inp + out) / cnt) if cnt else 0

    by_role_total = _agg_by_role(hourly)
    by_role_today = _agg_by_role(today_hourly)

    return {
        "task_count": {"today": task_today, "total": task_total},
        "input_tokens": {"today": in_d, "total": in_t},
        "output_tokens": {"today": out_d, "total": out_t},
        "total_tokens": {"today": in_d + out_d, "total": in_t + out_t},
        "cache_hit_tokens": {"today": hit_d, "total": hit_t},
        "cache_hit_rate": {"today": rate(hit_d, in_d), "total": rate(hit_t, in_t)},
        "avg_tokens_per_task": {
            "today": avg(in_d, out_d, task_today),
            "total": avg(in_t, out_t, task_total),
        },
        "deepseek_cost": {"today": cost_d, "total": cost_t},
        "by_role": {"today": by_role_today, "total": by_role_total},
        "agents": _agent_usage(agents),
    }


def ai_daily_series(user_id, days=12):
    """近 N 天逐日：总 token、缓存命中 token、DeepSeek 费用。

    返回 {labels, total_tokens, cache_tokens, deepseek_cost}，labels 与执行趋势同口径。
    """
    first_day = (timezone.now() - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    labels = [
        (timezone.now() - timedelta(days=days - 1 - i)).strftime("%m/%d") for i in range(days)
    ]

    total_tokens = [0] * days
    cache_tokens = [0] * days
    cost = [0.0] * days
    start_date = first_day.date()
    try:
        rows = (
            _hourly_qs([agent.id for agent in _agents(user_id)])
            .filter(stat_date__gte=start_date)
            .values("stat_date")
            .annotate(
                inp=Sum("input_tokens"),
                out=Sum("output_tokens"),
                hit=Sum("cache_input_tokens"),
                spent=Sum("cost_total"),
            )
        )
        for row in rows:
            idx = (row["stat_date"] - start_date).days
            if not 0 <= idx < days:
                continue
            total_tokens[idx] = int(row["inp"] or 0) + int(row["out"] or 0)
            cache_tokens[idx] = int(row["hit"] or 0)
            cost[idx] = _money(row["spent"])
    except (OperationalError, ProgrammingError):
        # 统计表缺失或迁移未完成时返回空数据，不阻断仪表盘
        pass

    return {
        "labels": labels,
        "total_tokens": total_tokens,
        "cache_tokens": cache_tokens,
        "deepseek_cost": cost,
    }


# 助手任务卡：成功 / 失败（与前端 TaskBoard taskStatusTone 对齐）
_TASK_SUCCESS = ("completed", "success")
_TASK_FAILED = ("failed",)


def _panel_status(raw: str) -> str:
    """列表 status → 仪表盘结果面板图标档。"""
    key = (raw or "").lower()
    if key in _TASK_SUCCESS:
        return "success"
    if key in _TASK_FAILED:
        return "failed"
    if key == "running":
        return "running"
    return "idle"


def _day_labels(days: int):
    """近 N 日标签与首日 00:00（与 ai_daily_series 同口径）。"""
    first_day = (timezone.now() - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    labels = [
        (timezone.now() - timedelta(days=days - 1 - i)).strftime("%m/%d") for i in range(days)
    ]
    return first_day, labels


def ai_task_daily_execution(user_id, days=12):
    """近 N 日按 created_at 分桶的助手任务卡成功 / 失败柱。"""
    first_day, labels = _day_labels(days)
    success = [0] * days
    failed = [0] * days
    try:
        tasks = list(
            _task_qs(user_id).filter(created_at__gte=first_day).only("created_at", "status")
        )
    except (OperationalError, ProgrammingError):
        return {"labels": labels, "success": success, "failed": failed}

    start_date = first_day.date()
    for t in tasks:
        idx = (t.created_at.date() - start_date).days
        if not 0 <= idx < days:
            continue
        key = (t.status or "").lower()
        if key in _TASK_SUCCESS:
            success[idx] += 1
        elif key in _TASK_FAILED:
            failed[idx] += 1
    return {"labels": labels, "success": success, "failed": failed}


def ai_task_execution_summary(user_id):
    """可见助手任务卡的成功 / 失败总数。"""
    qs = _task_qs(user_id)

    def safe_count(filtered):
        try:
            return filtered.count()
        except (OperationalError, ProgrammingError):
            return 0

    return {
        "passed": safe_count(qs.filter(status__in=_TASK_SUCCESS)),
        "failed": safe_count(qs.filter(status__in=_TASK_FAILED)),
    }


def ai_recent_tasks(user_id, limit=8):
    """最近助手任务卡（结果面板行）。"""
    try:
        rows = list(
            _task_qs(user_id)
            .order_by("-created_at")
            .only("id", "title", "goal", "status", "created_at")[:limit]
        )
    except (OperationalError, ProgrammingError):
        return []

    items = []
    for t in rows:
        created = t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else ""
        items.append(
            {
                "id": t.id,
                "title": t.title or t.goal or "未命名任务",
                "status": _panel_status(t.status),
                "time": created,
            }
        )
    return items


# 活动时间线合并窗口：各源最多取 WINDOW，合并排序后再截 WINDOW，分页在窗口内切片
_ACTIVITY_WINDOW = 100


def platform_activities(user_id, *, limit=10, offset=0):
    """平台活动时间线：助手任务卡（run）+ 智能体更新（agent），按 time 倒序。

    各源最多取 _ACTIVITY_WINDOW 条，合并后截断为 _ACTIVITY_WINDOW，再按
    offset/limit 切片。不查询已删除的 TestRunRecord。
    """
    items = []

    try:
        tasks = list(
            _task_qs(user_id)
            .order_by("-created_at")
            .only("title", "goal", "status", "created_at")[:_ACTIVITY_WINDOW]
        )
    except (OperationalError, ProgrammingError):
        tasks = []
    for t in tasks:
        title = t.title or t.goal or "未命名任务"
        created = t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else ""
        items.append(
            {
                "type": "run",
                "action": f"助手任务: {title}",
                "detail": f"状态: {_panel_status(t.status)}",
                "time": created,
            }
        )

    try:
        agents = list(
            filter_agents_for_user(AIAgent.objects.all(), user_id).order_by("-updated_at")[
                :_ACTIVITY_WINDOW
            ]
        )
    except (OperationalError, ProgrammingError):
        agents = []
    for agent in agents:
        items.append(
            {
                "type": "agent",
                "action": f"智能体更新: {agent.name}",
                "detail": f"模型: {agent.model_provider}/{agent.model_name}",
                "time": agent.updated_at.strftime("%Y-%m-%d %H:%M") if agent.updated_at else "",
            }
        )

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    window = items[:_ACTIVITY_WINDOW]
    return window[offset : offset + limit]
