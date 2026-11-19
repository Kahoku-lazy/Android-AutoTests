"""可配置的模型价目表与费用计算。

公式只有一条：未命中、缓存、输出、字符分别乘单价，再乘倍率，再折成人民币。
单价、倍率、门槛、汇率与模型映射都在 rates.py，更换它们不改本公式。
"""

from __future__ import annotations

import json
import os

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from engines.backend_bridge.model_billing.billing import DeepSeekBilling

from .rates import lookup_rate

_PRICING_PATH = Path(
    os.environ.get(
        "USAGE_PRICING_PATH",
        str(Path(__file__).with_name("pricing.json")),
    ),
)
_MILLION = Decimal(1_000_000)
_EIGHT = Decimal("0.00000001")


def _load() -> dict[str, Any]:
    """读取价目表；失败时返回空表，按 unpriced 处理。"""
    try:
        return json.loads(_PRICING_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"currency": "CNY", "models": {}}


_PRICING = _load()


def normalize_provider(provider: str, model: str = "") -> str:
    """把厂商归一为 deepseek / dashscope / openai。厂商只用于归类，不用于选价。"""
    value = (provider or "").strip().lower()
    if value in ("deepseek", "dashscope", "openai"):
        return value
    if value in ("omni", "qwen", "sambert"):
        return "dashscope"
    name = (model or "").lower()
    if name.startswith("grok"):
        return "openai"
    if "qwen" in name or "sambert" in name:
        return "dashscope"
    if name.startswith("deepseek"):
        return "deepseek"
    return value or "other"


def category_of(model: str, provider: str = "") -> str:
    """按模型名推断分类：LLM/TTS/Realtime/Embedding/ASR。"""
    name = (model or "").lower()
    if "embedding" in name:
        return "Embedding"
    if "tts" in name or "sambert" in name:
        return "TTS"
    if "asr" in name or "transcribe" in name:
        return "ASR"
    if "realtime" in name or "omni" in name or "livetranslate" in name:
        return "Realtime"
    return "Realtime" if provider == "dashscope" and "realtime" in name else "LLM"


def price_usage(
    provider: str,
    model: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_input_tokens: int = 0,
    cache_creation_tokens: int = 0,
    characters: int = 0,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    """
    按价目表计算一条用量的费用。

    Args:
        provider: deepseek / dashscope。
        model: 模型名。
        input_tokens: 输入 token。
        output_tokens: 输出 token。
        cache_input_tokens: 缓存命中 token。
        cache_creation_tokens: 缓存创建 token。
        characters: TTS 字符数。
        occurred_at: 发生时间；DeepSeek 用于高峰倍率。

    Returns:
        含 category/provider/cost_* /pricing_status/pricing_snapshot 的字典。
    """
    provider = normalize_provider(provider, model)
    rate = lookup_rate(model)
    if rate is not None:
        return _price_from_rate(
            provider,
            model,
            rate,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_input_tokens=cache_input_tokens,
            characters=characters,
            occurred_at=occurred_at,
        )

    config = (_PRICING.get("models") or {}).get(model)
    if not config:
        return {
            "provider": provider,
            "category": category_of(model, provider),
            "cost_input": Decimal(0),
            "cost_cache": Decimal(0),
            "cost_output": Decimal(0),
            "cost_total": Decimal(0),
            "pricing_status": "unpriced",
            "pricing_snapshot": {"model": model, "reason": "价目表未收录"},
        }

    status = str(config.get("pricing_status") or "priced")
    category = str(config.get("category") or category_of(model, provider))
    incoming = max(int(input_tokens or 0), 0)
    outgoing = max(int(output_tokens or 0), 0)
    chars = max(int(characters or 0), 0)
    input_cost = _cost_amount(
        chars,
        incoming,
        Decimal(str(config.get("input_per_million", 0) or 0)),
        Decimal(str(config.get("per_10k_chars", 0) or 0)),
    )
    output_cost = (
        Decimal(outgoing) * Decimal(str(config.get("output_per_million", 0) or 0)) / _MILLION
    )
    if status == "unpriced":
        input_cost = Decimal(0)
        output_cost = Decimal(0)
    return {
        "provider": provider,
        "category": category,
        "cost_input": _q(input_cost),
        "cost_cache": Decimal("0.00000000"),
        "cost_output": _q(output_cost),
        "cost_total": _q(input_cost + output_cost),
        "pricing_status": status,
        "pricing_snapshot": {
            "model": model,
            **config,
        },
    }


def _price_from_rate(
    provider: str,
    model: str,
    rate: dict,
    *,
    input_tokens: int,
    output_tokens: int,
    cache_input_tokens: int,
    characters: int,
    occurred_at: datetime | None,
) -> dict[str, Any]:
    """用一条公式把基数折成人民币。没有基数的调用不得进入本函数。"""
    incoming = max(int(input_tokens or 0), 0)
    outgoing = max(int(output_tokens or 0), 0)
    hit = min(max(int(cache_input_tokens or 0), 0), incoming)
    miss = incoming - hit
    chars = max(int(characters or 0), 0)
    threshold = int(rate.get("long_context_threshold") or 0)
    long_context = threshold > 0 and incoming >= threshold
    input_price = rate["long_input"] if long_context else rate["input"]
    cache_price = rate["long_cache"] if long_context else rate["cache"]
    output_price = rate["long_output"] if long_context else rate["output"]
    peak = _is_peak(occurred_at) if Decimal(rate["peak_multiplier"]) != 1 else False
    multiplier = Decimal(rate["peak_multiplier"]) if peak else Decimal(1)
    fx = Decimal(rate["fx_to_cny"])
    input_cost = Decimal(miss) * Decimal(input_price) / _MILLION * multiplier * fx
    cache_cost = Decimal(hit) * Decimal(cache_price) / _MILLION * multiplier * fx
    output_cost = Decimal(outgoing) * Decimal(output_price) / _MILLION * multiplier * fx
    char_cost = Decimal(chars) * Decimal(rate["characters"]) / Decimal(10_000) * multiplier * fx
    input_cost += char_cost
    return {
        "provider": provider,
        "category": rate["category"],
        "cost_input": _q(input_cost),
        "cost_cache": _q(cache_cost),
        "cost_output": _q(output_cost),
        "cost_total": _q(input_cost + cache_cost + output_cost),
        "pricing_status": "priced",
        "pricing_snapshot": {
            "model": str(model or "").strip().lower(),
            "alias_of": rate.get("alias_of") or "",
            "currency": rate["currency"],
            "fx_to_cny": str(fx),
            "multiplier": str(multiplier),
            "peak": peak,
            "long_context": long_context,
            "input_price": str(input_price),
            "cache_price": str(cache_price),
            "output_price": str(output_price),
            "basis": rate["basis"],
        },
    }


def _is_peak(occurred_at: datetime | None) -> bool:
    """复用 DeepSeek 的北京时间高峰规则。无时刻按空闲。"""
    return DeepSeekBilling._is_peak_time(occurred_at)


def _cost_amount(
    characters: int,
    input_tokens: int,
    input_per_million: Decimal,
    per_10k_chars: Decimal,
) -> Decimal:
    """按字符或输入 token 计算输入费用。"""
    if per_10k_chars:
        return Decimal(characters) * per_10k_chars / Decimal(10_000)
    return Decimal(input_tokens) * input_per_million / _MILLION


def _q(value: Decimal) -> Decimal:
    """金额保留 8 位。"""
    return value.quantize(_EIGHT, rounding=ROUND_HALF_UP)
