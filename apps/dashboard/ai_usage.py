"""Dashboard AI 用量聚合 — 对话 / token / 缓存命中 + DeepSeek 费用。

从 views.py 抽出以控制文件体量（views.py 已超 300 行上限）。纯只读聚合，无任何写操作。
"""

from datetime import timedelta

from django.db import OperationalError, ProgrammingError
from django.db.models import Sum
from django.utils import timezone

from apps.ai_assistant.models import AIConversation, AIMessage

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


def _assistant_msgs(user_id):
    """当前用户拥有的智能体产生的 assistant 消息（token 用量只统计 assistant）。"""
    if user_id:
        return AIMessage.objects.filter(conversation__agent__owner_id=user_id, role="assistant")
    return AIMessage.objects.none()


def _sum_cost(queryset):
    """对 queryset 内的 DeepSeek 消息逐条计费并累加（元，保留 4 位小数）。"""
    try:
        rows = queryset.filter(model_name__istartswith="deepseek").values_list(
            "created_at", "input_tokens", "tokens", "cache_input_tokens", "model_name"
        )
    except (OperationalError, ProgrammingError):
        return 0.0
    total = 0.0
    for created_at, inp, out, hit, model in rows:
        total += deepseek_cost(inp, out, hit, model, created_at)
    return round(total, 4)


def ai_usage_stats(user_id):
    """AI 用量聚合（今日/累计），含 DeepSeek 费用。

    返回：对话数、输入/输出 token、缓存命中 token/命中率、平均每对话 token、
    DeepSeek 费用，各指标分 today / total 两组口径。
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    conv_qs = (
        AIConversation.objects.filter(agent__owner_id=user_id)
        if user_id
        else AIConversation.objects.none()
    )
    msg_qs = _assistant_msgs(user_id)

    def safe_count(qs, filter_kwargs=None):
        try:
            if filter_kwargs:
                qs = qs.filter(**filter_kwargs)
            return qs.count()
        except (OperationalError, ProgrammingError):
            return 0

    conv_total = safe_count(conv_qs)
    conv_today = safe_count(conv_qs, {"created_at__gte": today_start})

    def agg(qs):
        """聚合输入/输出/缓存命中 token；表缺失时计 0。"""
        try:
            row = qs.aggregate(
                inp=Sum("input_tokens"),
                out=Sum("tokens"),
                hit=Sum("cache_input_tokens"),
            )
        except (OperationalError, ProgrammingError):
            return 0, 0, 0
        return int(row["inp"] or 0), int(row["out"] or 0), int(row["hit"] or 0)

    in_t, out_t, hit_t = agg(msg_qs)
    in_d, out_d, hit_d = agg(msg_qs.filter(created_at__gte=today_start))

    def rate(hit, inp):
        # 缓存命中率 = 命中 token / 输入 token，返回百分比（0-100，1 位小数）
        return round(hit / inp * 100, 1) if inp else 0.0

    def avg(inp, out, conv):
        return int((inp + out) / conv) if conv else 0

    return {
        "conversation_count": {"today": conv_today, "total": conv_total},
        "input_tokens": {"today": in_d, "total": in_t},
        "output_tokens": {"today": out_d, "total": out_t},
        "total_tokens": {"today": in_d + out_d, "total": in_t + out_t},
        "cache_hit_tokens": {"today": hit_d, "total": hit_t},
        "cache_hit_rate": {"today": rate(hit_d, in_d), "total": rate(hit_t, in_t)},
        "avg_tokens_per_conversation": {
            "today": avg(in_d, out_d, conv_today),
            "total": avg(in_t, out_t, conv_total),
        },
        "deepseek_cost": {
            "today": _sum_cost(msg_qs.filter(created_at__gte=today_start)),
            "total": _sum_cost(msg_qs),
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
        rows = (
            _assistant_msgs(user_id)
            .filter(created_at__gte=first_day)
            .values_list("created_at", "input_tokens", "tokens", "cache_input_tokens", "model_name")
        )
    except (OperationalError, ProgrammingError):
        return {
            "labels": labels,
            "total_tokens": total_tokens,
            "cache_tokens": cache_tokens,
            "deepseek_cost": cost,
        }

    start_date = first_day.date()
    for created_at, inp, out, hit, model in rows:
        idx = (created_at.date() - start_date).days
        if not 0 <= idx < days:
            continue
        total_tokens[idx] += (inp or 0) + (out or 0)
        cache_tokens[idx] += hit or 0
        if _is_deepseek_model(model):
            cost[idx] += deepseek_cost(inp, out, hit, model, created_at)

    return {
        "labels": labels,
        "total_tokens": total_tokens,
        "cache_tokens": cache_tokens,
        "deepseek_cost": [round(c, 4) for c in cost],
    }
