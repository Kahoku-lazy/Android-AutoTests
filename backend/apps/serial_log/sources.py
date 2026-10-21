"""端口来源登记 —— 把 `DEVICE_LOG_SOURCES` 配置解析成日志来源列表。

只做配置解析，不碰监听、不碰文件、不写库。
"""

from __future__ import annotations

import json

from django.conf import settings

from engines.device.logbus import DEFAULT_CHANNEL, LogSourceSpec
from utils.logs import backend_log

__all__ = ["source_specs"]


def _default_baud() -> int:
    return int(getattr(settings, "DEVICE_LOG_SOURCE_BAUD", 0) or 0)


def _int_or(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _specs_from_mapping(data: dict) -> list[LogSourceSpec]:
    """`DEVICE_LOG_SOURCES` 的 JSON → 来源登记列表；端口非数字的条目记录错误后跳过。"""
    specs: list[LogSourceSpec] = []
    for key, value in data.items():
        port = _int_or(key, 0)
        if not port:
            backend_log.error("DEVICE_LOG_SOURCES 端口不是数字，已忽略: %s", key)
            continue
        if isinstance(value, dict):
            sku = str(value.get("sku") or value.get("channel") or "").strip() or DEFAULT_CHANNEL
            baud = _int_or(value.get("baud"), _default_baud())
        else:
            sku = str(value or "").strip() or DEFAULT_CHANNEL
            baud = _default_baud()
        specs.append(LogSourceSpec(port=port, sku=sku, baud=baud))
    return sorted(specs, key=lambda item: item.port)


def source_specs() -> list[LogSourceSpec]:
    """「端口 → 来源登记」：优先 `settings.DEVICE_LOG_SOURCES`（JSON），否则按单端口合成。

    支持两种 JSON 形态：

    - 显式：`{"7005": {"sku": "H6810", "baud": 921600}}`
    - 简写：`{"7005": "H6810"}`（波特率取 `DEVICE_LOG_SOURCE_BAUD`）
    """
    raw = str(getattr(settings, "DEVICE_LOG_SOURCES", "") or "").strip()
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            backend_log.error("DEVICE_LOG_SOURCES 不是合法 JSON，已忽略: %s", raw)
            data = {}
        specs = _specs_from_mapping(data if isinstance(data, dict) else {})
        if specs:
            return specs
    sku = str(getattr(settings, "DEVICE_LOG_SOURCE_SKU", "") or "").strip() or DEFAULT_CHANNEL
    port = int(settings.DEVICE_LOG_TCP_PORT)
    return [LogSourceSpec(port=port, sku=sku, baud=_default_baud())] if port else []
