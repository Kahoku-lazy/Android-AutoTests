"""
模块功能：➡️ Dashboard AI 用量聚合 — 只读小时用量表 🏁
Python 调试：➡️ python -m backend.apps.dashboard.ai_usage 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/dashboard/api/test_dashboard_agent_usage.py: 覆盖本模块
🏁
"""

from datetime import timedelta
from decimal import Decimal

from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone

from backend.apps.task_list.case_identity import case_identity_label
from backend.apps.task_list.models import Task, TaskUsageHourly
from backend.apps.usage_ledger.models import ModelUsage
from backend.apps.usage_ledger.rates import DISPLAY_FX_DATE, DISPLAY_FX_USD_CNY
from backend.models.constants import TaskKind


def _task_qs(user_id, agents=None):
    """已登录用户可见的工作流任务。已退役的设备执行与用例编写不计入。"""
    del agents
    if not user_id:
        return Task.objects.none()
    return Task.objects.filter(task_kind=TaskKind.ASSISTANT_SOP)


def workflow_task_counts(user_id) -> dict:
    """工作流任务的累计、今日、执行中与排队数。

    Args:
        user_id: 当前用户 id；空值时四项都是 0。

    Returns:
        `{total, today, running, pending}`。
    """
    empty = {"total": 0, "today": 0, "running": 0, "pending": 0}
    if not user_id:
        return empty
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        rows = _task_qs(user_id).values("status").annotate(count=Count("id"))
        today = _task_qs(user_id).filter(created_at__gte=today_start).count()
    except (OperationalError, ProgrammingError):
        return empty
    counts = {str(row["status"] or ""): int(row["count"]) for row in rows}
    return {
        "total": sum(counts.values()),
        "today": today,
        "running": counts.get("running", 0),
        "pending": counts.get("pending", 0),
    }


def _ledger_qs():
    """平台全部逐次账。账单只读这里，不读小时表。"""
    return ModelUsage.objects.all()


def _priced(qs):
    """费用合计只取已计价行。"""
    return qs.exclude(pricing_status="unpriced")


def _unpriced_tokens(qs) -> int:
    """未计价行的输入加输出。这些 token 不进费用。"""
    try:
        row = qs.filter(pricing_status="unpriced").aggregate(
            inp=Sum("input_tokens"),
            out=Sum("output_tokens"),
        )
    except (OperationalError, ProgrammingError):
        return 0
    return int(row["inp"] or 0) + int(row["out"] or 0)


def _archived_hourly_cost() -> float:
    """切换点之前的小时表合计。只作归档，不并入平台费用。"""
    try:
        row = TaskUsageHourly.objects.aggregate(cost=Sum("cost_total"))
    except (OperationalError, ProgrammingError):
        return 0.0
    return _money(row["cost"])


def _money(value) -> float:
    amount = Decimal(value or 0).quantize(Decimal("0.00000001"))
    return float(amount)


def _sum_usage(qs):
    """小时用量合计：输入、输出、缓存命中、总费用。"""
    try:
        row = _priced(qs).aggregate(
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
    """逐次账没有角色列。角色拆分已退出账单，这里固定返回空。"""
    del qs
    return {}


def _agent_usage(agents):
    """智能体已下线，不再按智能体拆账单。"""
    del agents
    return []


def ai_usage_stats(user_id, agents=None):
    """AI 用量聚合（今日/累计），含 DeepSeek 费用。

    用量与费用取平台全部小时用量，任务数取当前用户可见任务。
    返回：任务数量、输入/输出 token、缓存命中 token/命中率、平均每任务 token、
    DeepSeek 费用，各指标分 today / total 两组口径。

    Args:
        user_id: 当前用户 id。
        agents: 已装载的可见智能体；None 时自行装载（避免重复读取大字段）。
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    del agents
    tasks = workflow_task_counts(user_id)
    ledger = _ledger_qs()
    today_hourly = ledger.filter(occurred_at__gte=today_start)
    hourly = ledger

    task_total = tasks["total"]
    task_today = tasks["today"]

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
        "unpriced_tokens": {
            "today": _unpriced_tokens(today_hourly),
            "total": _unpriced_tokens(hourly),
        },
        "display_fx": {"date": DISPLAY_FX_DATE, "usd_cny": str(DISPLAY_FX_USD_CNY)},
        "archived_hourly_cost": _archived_hourly_cost(),
        "by_role": {"today": by_role_today, "total": by_role_total},
        "agents": _agent_usage([]),
    }


_SERIES_LIMIT = 5


def _bucket_series(rows, days, start_date, key_name):
    """把按日分组的行收成对齐的序列。超过 5 条的尾部并入「其他」。"""
    buckets = {}
    for row in rows:
        stat_date = row["stat_date"]
        if hasattr(stat_date, "date"):
            stat_date = stat_date.date()
        idx = (stat_date - start_date).days
        if not 0 <= idx < days:
            continue
        name = str(row.get(key_name) or "未命名")
        bucket = buckets.setdefault(name, {"tokens": [0] * days, "cost": [0.0] * days})
        bucket["tokens"][idx] += int(row["inp"] or 0) + int(row["out"] or 0)
        bucket["cost"][idx] = _money(Decimal(bucket["cost"][idx]) + Decimal(row["spent"] or 0))
    ranked = sorted(buckets.items(), key=lambda item: sum(item[1]["tokens"]), reverse=True)
    visible = ranked[:_SERIES_LIMIT]
    rest = ranked[_SERIES_LIMIT:]
    if rest:
        other = {"tokens": [0] * days, "cost": [0.0] * days}
        for _name, bucket in rest:
            for index in range(days):
                other["tokens"][index] += bucket["tokens"][index]
                other["cost"][index] = _money(
                    Decimal(other["cost"][index]) + Decimal(bucket["cost"][index])
                )
        visible.append(("其他", other))
    return [
        {"name": name, "tokens": bucket["tokens"], "cost": bucket["cost"]}
        for name, bucket in visible
    ]


def _daily_rows(start_date, source=""):
    """按模型与日期分组。source 为空时含全部来源。"""
    qs = _priced(_ledger_qs()).filter(occurred_at__date__gte=start_date)
    if source:
        qs = qs.filter(source=source)
    return (
        qs.annotate(stat_date=TruncDate("occurred_at"))
        .values("model", "stat_date")
        .annotate(
            inp=Sum("input_tokens"),
            out=Sum("output_tokens"),
            hit=Sum("cache_input_tokens"),
            spent=Sum("cost_total"),
        )
    )


def ai_daily_series(user_id, days=7):
    """近 N 天逐日：总 token、缓存命中 token、DeepSeek 费用。

    按平台全部小时用量分桶；`user_id` 保留在签名里仅为与其它统计入口一致。
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
            _priced(_ledger_qs())
            .filter(occurred_at__date__gte=start_date)
            .annotate(stat_date=TruncDate("occurred_at"))
            .values("stat_date")
            .annotate(
                inp=Sum("input_tokens"),
                out=Sum("output_tokens"),
                hit=Sum("cache_input_tokens"),
                spent=Sum("cost_total"),
            )
        )
        for row in rows:
            stat_date = row["stat_date"]
            if hasattr(stat_date, "date"):
                stat_date = stat_date.date()
            idx = (stat_date - start_date).days
            if not 0 <= idx < days:
                continue
            total_tokens[idx] = int(row["inp"] or 0) + int(row["out"] or 0)
            cache_tokens[idx] = int(row["hit"] or 0)
            cost[idx] = _money(row["spent"])
        by_model = _bucket_series(_daily_rows(start_date), days, start_date, "model")
        voice_by_model = _bucket_series(_daily_rows(start_date, "voice"), days, start_date, "model")
    except (OperationalError, ProgrammingError):
        # 统计表缺失或迁移未完成时返回空数据，不阻断仪表盘
        by_model = []
        voice_by_model = []

    return {
        "labels": labels,
        "total_tokens": total_tokens,
        "cache_tokens": cache_tokens,
        "deepseek_cost": cost,
        "by_model": by_model,
        "voice_by_model": voice_by_model,
    }


# ── 当日用量 ──
# 数据按小时落桶（库里就是小时粒度）；横轴刻度每 4 小时一个，由前端按 0–24 渲染。
_HOURS_PER_DAY = 24


def ai_today_usage_slots(user_id, now=None):
    """当天逐小时的 token 与费用消耗（按时间进度出数）。

    取平台全部小时用量，`user_id` 保留在签名里仅为与其它统计入口一致。
    `tokens[h]` 是第 h 小时（[h:00, h+1:00)）的用量：该小时走完才给值，
    没走完或还没开始时为 None。进行中的那一小时由 `current` 单独返回，
    MUST NOT 提前出数。
    """
    now = now or timezone.now()
    now_hour = min(24.0, round(now.hour + now.minute / 60 + now.second / 3600, 2))
    today = now.date()
    hourly_tokens = [0] * _HOURS_PER_DAY
    hourly_cost = [Decimal(0)] * _HOURS_PER_DAY
    try:
        rows = (
            _priced(_ledger_qs())
            .filter(occurred_at__date=today)
            .annotate(stat_hour=TruncHour("occurred_at"))
            .values("stat_hour")
            .annotate(
                inp=Sum("input_tokens"),
                out=Sum("output_tokens"),
                spent=Sum("cost_total"),
            )
        )
        for row in rows:
            moment = row["stat_hour"]
            hour = moment.hour if hasattr(moment, "hour") else int(moment or 0)
            if not 0 <= hour < _HOURS_PER_DAY:
                # stat_hour 脏数据（<0 或 >23）丢弃，不让分桶越界
                continue
            hourly_tokens[hour] += int(row["inp"] or 0) + int(row["out"] or 0)
            hourly_cost[hour] += Decimal(row["spent"] or 0)
    except (OperationalError, ProgrammingError):
        # 统计表缺失或迁移未完成时返回空序列，不阻断仪表盘
        pass

    tokens = []
    cost = []
    current = None
    for hour in range(_HOURS_PER_DAY):
        if hour + 1 <= now_hour:
            tokens.append(hourly_tokens[hour])
            cost.append(_money(hourly_cost[hour]))
            continue
        tokens.append(None)
        cost.append(None)
        if hour < now_hour < hour + 1:
            current = {
                "hour": now_hour,
                "tokens": hourly_tokens[hour],
                "cost": _money(hourly_cost[hour]),
            }

    return {
        "tokens": tokens,
        "cost": cost,
        "current": current,
    }


# 助手任务卡：成功 / 失败（与前端 TaskBoard taskStatusTone 对齐）
_TASK_SUCCESS = ("completed", "success")
_TASK_FAILED = ("failed",)


def _panel_status(raw: str) -> str:
    """列表 status → 仪表盘结果面板图标档。中断与取消不收成未执行。"""
    key = (raw or "").lower()
    if key in _TASK_SUCCESS:
        return "success"
    if key in _TASK_FAILED:
        return "failed"
    if key in ("running", "interrupted", "cancelled"):
        return key
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


def ai_task_daily_execution(user_id, days=7, agents=None):
    """近 N 日按 created_at 分桶的助手任务卡成功 / 失败柱。

    Args:
        user_id: 当前用户 id。
        days: 天数窗口。
        agents: 已装载的可见智能体；None 时自行装载。
    """
    first_day, labels = _day_labels(days)
    success = [0] * days
    failed = [0] * days
    try:
        tasks = list(
            _task_qs(user_id, agents).filter(created_at__gte=first_day).only("created_at", "status")
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


def ai_task_execution_summary(user_id, agents=None):
    """可见助手任务卡的成功 / 失败总数。

    Args:
        user_id: 当前用户 id。
        agents: 已装载的可见智能体；None 时自行装载。
    """
    qs = _task_qs(user_id, agents)

    def safe_count(filtered):
        try:
            return filtered.count()
        except (OperationalError, ProgrammingError):
            return 0

    return {
        "passed": safe_count(qs.filter(status__in=_TASK_SUCCESS)),
        "failed": safe_count(qs.filter(status__in=_TASK_FAILED)),
    }


def ai_recent_tasks(user_id, limit=8, agents=None):
    """最近助手任务卡（结果面板行）。

    Args:
        user_id: 当前用户 id。
        limit: 条数。
        agents: 已装载的可见智能体；None 时自行装载。
    """
    try:
        rows = list(
            _task_qs(user_id, agents)
            .order_by("-created_at")
            .only("id", "title", "goal", "status", "created_at", "case_identity")[:limit]
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
                "case_label": case_identity_label(t.case_identity),
                "status": _panel_status(t.status),
                "time": created,
            }
        )
    return items


# 活动时间线合并窗口：各源最多取 WINDOW，合并排序后再截 WINDOW，分页在窗口内切片
_ACTIVITY_WINDOW = 100


def platform_activities(user_id, *, limit=10, offset=0, agents=None):
    """平台活动时间线：只列工作流任务，按 time 倒序。

    最多取 _ACTIVITY_WINDOW 条，再按 offset/limit 切片。不查询已删除的
    TestRunRecord，也不再返回已下线智能体的更新。

    Args:
        user_id: 当前用户 id。
        limit: 返回条数。
        offset: 分页偏移。
        agents: 兼容旧调用；工作流任务不再按智能体过滤。
    """
    del agents
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

    return items[offset : offset + limit]
