"""Dashboard AI 用量聚合 — 任务 / token / 缓存命中 + DeepSeek 费用。

对话模式已移除（ARCH v3.4），AI 用量改按「任务」（AITask）统计：任务数量、
每任务累计 token（工作流采集落库）与 DeepSeek 费用。从 views.py 抽出以控制文件体量。
纯只读聚合，无任何写操作。
"""

from datetime import timedelta

from django.db import OperationalError, ProgrammingError
from django.db.models import Sum
from django.utils import timezone

from apps.ai_assistant.api import filter_agents_for_user, task_deepseek_cost
from apps.ai_assistant.models import AIAgent, AITask

# 价目与高峰规则见 apps.ai_assistant.deepseek_billing（经 api.task_deepseek_cost 消费）


def _task_qs(user_id):
    """当前用户可见智能体产生的任务（任务数 / token / 费用统一口径）。"""
    agents = filter_agents_for_user(AIAgent.objects.all(), user_id)
    return AITask.objects.filter(agent__in=agents)


def _task_cost(task) -> float:
    """单任务 DeepSeek 费用（与任务详情同一口径）。"""
    return task_deepseek_cost(task)


def _qs_cost(queryset):
    """对任务 queryset 逐条计费并累加（元，保留 4 位小数）。"""
    try:
        tasks = list(
            queryset.only(
                "finished_at",
                "created_at",
                "model_usage",
                "input_tokens",
                "output_tokens",
                "cache_input_tokens",
            )
        )
    except (OperationalError, ProgrammingError):
        return 0.0
    return round(sum(_task_cost(t) for t in tasks), 4)


def _agg_by_role(qs):
    """聚合 by_role JSON（planner/executor/verifier 分角色 token 总量）。"""
    result = {}
    try:
        tasks = qs.only("by_role")
    except (OperationalError, ProgrammingError):
        return result
    for t in tasks:
        for role, v in (t.by_role or {}).items():
            r = result.setdefault(
                role, {"input_tokens": 0, "output_tokens": 0, "cache_input_tokens": 0}
            )
            r["input_tokens"] += int(v.get("input_tokens") or 0)
            r["output_tokens"] += int(v.get("output_tokens") or 0)
            r["cache_input_tokens"] += int(v.get("cache_input_tokens") or 0)
    return result


def ai_usage_stats(user_id):
    """AI 用量聚合（今日/累计），含 DeepSeek 费用。

    返回：任务数量、输入/输出 token、缓存命中 token/命中率、平均每任务 token、
    DeepSeek 费用，各指标分 today / total 两组口径。
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    task_qs = _task_qs(user_id)

    def safe_count(qs):
        try:
            return qs.count()
        except (OperationalError, ProgrammingError):
            return 0

    task_total = safe_count(task_qs)
    task_today = safe_count(task_qs.filter(created_at__gte=today_start))

    def agg(qs):
        """聚合输入/输出/缓存命中 token；表缺失时计 0。"""
        try:
            row = qs.aggregate(
                inp=Sum("input_tokens"),
                out=Sum("output_tokens"),
                hit=Sum("cache_input_tokens"),
            )
        except (OperationalError, ProgrammingError):
            return 0, 0, 0
        return int(row["inp"] or 0), int(row["out"] or 0), int(row["hit"] or 0)

    in_t, out_t, hit_t = agg(task_qs)
    in_d, out_d, hit_d = agg(task_qs.filter(created_at__gte=today_start))

    def rate(hit, inp):
        # 缓存命中率 = 命中 token / 输入 token，返回百分比（0-100，1 位小数）
        return round(hit / inp * 100, 1) if inp else 0.0

    def avg(inp, out, cnt):
        return int((inp + out) / cnt) if cnt else 0

    by_role_total = _agg_by_role(task_qs)
    by_role_today = _agg_by_role(task_qs.filter(created_at__gte=today_start))

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
        "deepseek_cost": {
            "today": _qs_cost(task_qs.filter(created_at__gte=today_start)),
            "total": _qs_cost(task_qs),
        },
        "by_role": {"today": by_role_today, "total": by_role_total},
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

    try:
        tasks = list(
            _task_qs(user_id)
            .filter(created_at__gte=first_day)
            .only(
                "created_at",
                "input_tokens",
                "output_tokens",
                "cache_input_tokens",
                "finished_at",
                "model_usage",
            )
        )
    except (OperationalError, ProgrammingError):
        return {
            "labels": labels,
            "total_tokens": total_tokens,
            "cache_tokens": cache_tokens,
            "deepseek_cost": cost,
        }

    start_date = first_day.date()
    for t in tasks:
        idx = (t.created_at.date() - start_date).days
        if not 0 <= idx < days:
            continue
        inp = t.input_tokens or 0
        out = t.output_tokens or 0
        total_tokens[idx] += inp + out
        cache_tokens[idx] += t.cache_input_tokens or 0
        cost[idx] += _task_cost(t)

    return {
        "labels": labels,
        "total_tokens": total_tokens,
        "cache_tokens": cache_tokens,
        "deepseek_cost": [round(c, 4) for c in cost],
    }
