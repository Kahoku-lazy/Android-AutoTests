"""模型费用计算 — 当前仅计 DeepSeek（价目对齐 apps.ai_assistant.deepseek_billing）。

每轮 RoleResult.cost 由此计算；非 DeepSeek 模型返回 0。
调价需同步 apps/ai_assistant/deepseek_billing.py 的 DEEPSEEK_PRICING。
"""

from __future__ import annotations

from datetime import datetime

# 空闲时段单价（元 / 百万 tokens）
# 依据（2026-10-08 官方价目页）：deepseek-flash 0.02 / 1 / 4；deepseek-v4-pro 0.15 / 4.5 / 13.5。
DEEPSEEK_PRICING = {
    "deepseek-flash": {"input_cache_hit": 0.02, "input_cache_miss": 1.0, "output": 4.0},
    "deepseek-v4-pro": {"input_cache_hit": 0.15, "input_cache_miss": 4.5, "output": 13.5},
}

_PEAK_MULTIPLIER = 2

# 通用名与旧名 → 正式模型名（厂商口径：旧名仍可调用、按 Flash 计费）
_DEEPSEEK_MODEL_ALIASES = {
    "deepseek-chat": "deepseek-flash",
    "deepseek-reasoner": "deepseek-v4-pro",
    "deepseek-v4-flash": "deepseek-flash",
    "deepseek-v4-flash-vision-exp": "deepseek-flash",
}

_DEFAULT_DEEPSEEK_MODEL = "deepseek-flash"


def _resolve_price(model_name: str | None) -> dict:
    name = str(model_name or "").strip().lower()
    name = _DEEPSEEK_MODEL_ALIASES.get(name, name)
    return DEEPSEEK_PRICING.get(name, DEEPSEEK_PRICING[_DEFAULT_DEEPSEEK_MODEL])


def _is_peak_time(dt: datetime | None) -> bool:
    """北京时间周一至周五 9:00–12:00、14:00–18:00。"""
    if dt is None:
        return False
    if dt.weekday() >= 5:
        return False
    hour = dt.hour
    return (9 <= hour < 12) or (14 <= hour < 18)


def model_cost(
    provider: str,
    model_name: str,
    usage: dict,
    created_at: datetime | None = None,
) -> float:
    """单轮模型费用（元）。非 DeepSeek 返回 0。"""
    if str(provider or "").strip().lower() != "deepseek":
        return 0.0
    price = _resolve_price(model_name)
    multiplier = _PEAK_MULTIPLIER if _is_peak_time(created_at) else 1
    inp = int(usage.get("input_tokens", 0) or 0)
    out = int(usage.get("output_tokens", 0) or 0)
    hit = max(min(int(usage.get("cache_input_tokens", 0) or 0), inp), 0)
    miss = max(inp - hit, 0)
    return round(
        (hit * price["input_cache_hit"] + miss * price["input_cache_miss"] + out * price["output"])
        / 1_000_000
        * multiplier,
        6,
    )
