"""可配置的模型价目表与费用计算。"""

from __future__ import annotations

import json
import os

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from engines.agents.messaging.billing import DeepSeekBilling

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
    """把厂商归一为 deepseek / dashscope。"""
    value = (provider or "").strip().lower()
    if value in ("deepseek", "dashscope"):
        return value
    if value in ("omni", "qwen", "sambert"):
        return "dashscope"
    return "dashscope" if "qwen" in model.lower() or "sambert" in model.lower() else "deepseek"


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
    config = (_PRICING.get("models") or {}).get(model)
    if provider == "deepseek":
        billing = DeepSeekBilling()
        input_cost, output_cost, cache_cost = billing.cost(
            model,
            input_tokens,
            output_tokens,
            cache_input_tokens,
            occurred_at,
        )
        snapshot = billing.snapshot(model, occurred_at)
        return {
            "provider": provider,
            "category": "LLM",
            "cost_input": input_cost,
            "cost_cache": cache_cost,
            "cost_output": output_cost,
            "cost_total": input_cost + cache_cost + output_cost,
            "pricing_status": "priced",
            "pricing_snapshot": snapshot,
        }

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
