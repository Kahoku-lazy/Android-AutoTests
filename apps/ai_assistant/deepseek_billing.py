"""DeepSeek 任务费用（元）。仪表盘聚合与任务详情共用。

价目参考：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
调价只改 DEEPSEEK_PRICING；高峰时段单价 = 空闲 × 2。
"""

from datetime import datetime

# 空闲时段单价（元 / 百万 tokens）
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

_PEAK_MULTIPLIER = 2

_DEEPSEEK_MODEL_ALIASES = {
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-pro",
}

_DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


def _is_deepseek_model(model_name: str | None) -> bool:
    return bool(model_name) and str(model_name).strip().lower().startswith("deepseek")


def _resolve_price(model_name: str | None) -> dict:
    name = str(model_name or "").strip().lower()
    name = _DEEPSEEK_MODEL_ALIASES.get(name, name)
    return DEEPSEEK_PRICING.get(name, DEEPSEEK_PRICING[_DEFAULT_DEEPSEEK_MODEL])


def _is_peak_time(dt: datetime | None) -> bool:
    """北京时间周一至周五 9:00–12:00、14:00–18:00。依赖 TIME_ZONE=Asia/Shanghai。"""
    if dt is None:
        return False
    if dt.weekday() >= 5:
        return False
    hour = dt.hour
    return (9 <= hour < 12) or (14 <= hour < 18)


def deepseek_cost(
    input_tokens: int,
    output_tokens: int,
    cache_hit_tokens: int,
    model_name: str | None,
    created_at: datetime | None,
) -> float:
    """单模型用量费用（元）。命中按命中价，其余输入按未命中价，输出按输出价。"""
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


def task_deepseek_cost(task) -> float:
    """单任务 DeepSeek 费用。

    有分模型用量时按各 DeepSeek 模型单价求和；无拆分时按默认 flash 档对任务总量计费。
    非 DeepSeek 用量不计费。
    """
    ts = getattr(task, "finished_at", None) or getattr(task, "created_at", None)
    mu = getattr(task, "model_usage", None)
    if isinstance(mu, dict) and mu:
        total = 0.0
        billed = False
        for model, usage in mu.items():
            if not _is_deepseek_model(model) or not isinstance(usage, dict):
                continue
            billed = True
            total += deepseek_cost(
                usage.get("input_tokens") or 0,
                usage.get("output_tokens") or 0,
                usage.get("cache_input_tokens") or 0,
                model,
                ts,
            )
        if billed:
            return round(total, 4)
        return 0.0
    inp = int(getattr(task, "input_tokens", 0) or 0)
    out = int(getattr(task, "output_tokens", 0) or 0)
    hit = int(getattr(task, "cache_input_tokens", 0) or 0)
    if inp <= 0 and out <= 0:
        return 0.0
    return round(deepseek_cost(inp, out, hit, _DEFAULT_DEEPSEEK_MODEL, ts), 4)
