"""Dashboard AI 用量聚合 — 任务 / token / 缓存命中 + DeepSeek 费用。

对话模式已移除（ARCH v3.4），AI 用量改按「任务」（AITask）统计：任务数量、
每任务累计 token（工作流采集落库）与 DeepSeek 费用。从 views.py 抽出以控制文件体量。
纯只读聚合，无任何写操作。
"""

from datetime import timedelta

from django.db import OperationalError, ProgrammingError
from django.db.models import Sum
from django.utils import timezone

from apps.ai_assistant.api import filter_agents_for_user
from apps.ai_assistant.models import AIAgent, AITask

# ── DeepSeek 计费单价（元 / 百万 tokens）─────────────────────────────────
# 参考官方定价：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
# 下表为「空闲时段」价；「高峰时段」价 = 空闲时段 × 2（见 _is_peak_time）。
# 调价只改此常量，聚合逻辑无需变动。
DEEPSEEK_PRICING = {
    "deepseek-v4-flash": {
        "input_cache_hit": 0.05,
        "input_cache_miss": 1.5,
        "output": 4.5,
    },
    "deepseek-v4-flash-vision-exp": {
        "input_cache_hit": 0.05,
        "input_cache_miss": 1.5,
        "output": 4.5,
    },
    "deepseek-v4-pro": {
        "input_cache_hit": 0.15,
        "input_cache_miss": 4.5,
        "output": 13.5,
    },
}

# 高峰时段单价 = 空闲时段 × 2
_PEAK_MULTIPLIER = 2

# 历史/别名模型 → 当前价目（官方定价页已下线的旧名仍可计费）
_DEEPSEEK_MODEL_ALIASES = {
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-pro",
}

# 未命中价目表时的兜底档位
_DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


def _is_deepseek_model(model_name):
    """判断消息是否由 DeepSeek 模型生成（model_name 以 deepseek 开头，忽略大小写）。"""
    return bool(model_name) and str(model_name).strip().lower().startswith("deepseek")


def _resolve_price(model_name):
    """按模型名解析计费档位；别名映射后未命中则回退默认档。"""
    name = str(model_name or "").strip().lower()
    name = _DEEPSEEK_MODEL_ALIASES.get(name, name)
    return DEEPSEEK_PRICING.get(name, DEEPSEEK_PRICING[_DEFAULT_DEEPSEEK_MODEL])


def _is_peak_time(dt):
    """高峰时段判定：北京时间周一至周五 9:00-12:00、14:00-18:00。

    settings 中 TIME_ZONE=Asia/Shanghai、USE_TZ=False，created_at 即北京时间 naive datetime，
    可直接取 weekday / hour。
    """
    if dt.weekday() >= 5:  # 周六 / 周日
        return False
    hour = dt.hour
    return (9 <= hour < 12) or (14 <= hour < 18)


def deepseek_cost(input_tokens, output_tokens, cache_hit_tokens, model_name, created_at):
    """单条消息的 DeepSeek 费用（元）。

    计费口径：缓存命中 token 按命中价、其余输入 token 按未命中价、输出 token 按输出价；
    高峰时段单价 ×2。
    """
    price = _resolve_price(model_name)
    multiplier = _PEAK_MULTIPLIER if _is_peak_time(created_at) else 1
    hit = max(min(cache_hit_tokens or 0, input_tokens or 0), 0)
    miss = max((input_tokens or 0) - hit, 0)
    out = output_tokens or 0
    return (
        (hit * price["input_cache_hit"] + miss * price["input_cache_miss"] + out * price["output"])
        / 1_000_000
        * multiplier
    )


def _task_qs(user_id):
    """当前用户可见智能体产生的任务（任务数 / token / 费用统一口径）。"""
    agents = filter_agents_for_user(AIAgent.objects.all(), user_id)
    return AITask.objects.filter(agent__in=agents)


def _task_cost(task) -> float:
    """单任务 DeepSeek 费用：遍历 model_usage 按模型单价计费（仅 DeepSeek 模型）。"""
    mu = task.model_usage
    if not isinstance(mu, dict):
        return 0.0
    ts = task.finished_at or task.created_at
    total = 0.0
    for model, m in mu.items():
        if not _is_deepseek_model(model) or not isinstance(m, dict):
            continue
        total += deepseek_cost(
            m.get("input_tokens") or 0,
            m.get("output_tokens") or 0,
            m.get("cache_input_tokens") or 0,
            model,
            ts,
        )
    return round(total, 4)


def _qs_cost(queryset):
    """对任务 queryset 逐条计费并累加（元，保留 4 位小数）。"""
    try:
        tasks = list(queryset.only("finished_at", "created_at", "model_usage"))
    except (OperationalError, ProgrammingError):
        return 0.0
    return round(sum(_task_cost(t) for t in tasks), 4)


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
