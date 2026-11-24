"""
模块功能：➡️ 按模型名索引的计价基数。换单价只改本表，不改公式 🏁
Python 调试：➡️ python -m backend.apps.usage_ledger.rates 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 usage_ledger 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

from decimal import Decimal

# 2026-11-17 中国外汇交易中心美元/人民币中间价。只用于把美元基数折成人民币库存。
DISPLAY_FX_DATE = "2026-11-17"
DISPLAY_FX_USD_CNY = Decimal("6.7132")

_FLASH = {
    "currency": "CNY",
    "category": "LLM",
    "input": Decimal("1"),
    "cache": Decimal("0.02"),
    "output": Decimal("4"),
    "characters": Decimal("0"),
    "peak_multiplier": Decimal("2"),
    "long_context_threshold": 0,
    "fx_to_cny": Decimal("1"),
    "basis": "official",
}
_PRO = {
    **_FLASH,
    "input": Decimal("4.5"),
    "cache": Decimal("0.15"),
    "output": Decimal("13.5"),
}
_GROK = {
    "currency": "USD",
    "category": "LLM",
    "input": Decimal("2"),
    "cache": Decimal("0.50"),
    "output": Decimal("6"),
    "characters": Decimal("0"),
    "peak_multiplier": Decimal("1"),
    "long_context_threshold": 200_000,
    "long_input": Decimal("4"),
    "long_cache": Decimal("1"),
    "long_output": Decimal("12"),
    "fx_to_cny": DISPLAY_FX_USD_CNY,
    "basis": "official-trial",
}
_OMNI_AUDIO = {
    "currency": "CNY",
    "category": "Realtime",
    "input": Decimal("80"),
    "cache": Decimal("0"),
    "output": Decimal("300"),
    "characters": Decimal("0"),
    "peak_multiplier": Decimal("1"),
    "long_context_threshold": 0,
    "fx_to_cny": Decimal("1"),
    "basis": "official-trial-audio",
}

# 单价单位：token 价为元或美元 / 百万 token；字符价为 / 万字符。
RATES: dict[str, dict] = {
    "deepseek-flash": _FLASH,
    "deepseek-v4-flash": {**_FLASH, "alias_of": "deepseek-flash"},
    "deepseek-v4-flash-vision-exp": {**_FLASH, "alias_of": "deepseek-flash"},
    "deepseek-v4.1-flash": {**_FLASH, "alias_of": "deepseek-flash"},
    "deepseek-v4-pro": _PRO,
    "grok-4.6": _GROK,
    "grok-4.7": _GROK,
    "qwen3.5-omni-plus-realtime": _OMNI_AUDIO,
}


def lookup_rate(model: str) -> dict | None:
    """按模型名取基数。没有基数时返回 None，调用方不得当成已计价。"""
    row = RATES.get(str(model or "").strip().lower())
    if row is None:
        return None
    return dict(row)
