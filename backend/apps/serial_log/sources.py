from __future__ import annotations

import json

from django.conf import settings

from engines.device.logbus import DEFAULT_CHANNEL, LogSourceSpec
from utils.logs import backend_log

from . import api

__all__ = ["config_specs", "source_specs"]


def _default_baud() -> int:
    return int(getattr(settings, "DEVICE_LOG_SOURCE_BAUD", 0) or 0)


def _int_or(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _specs_from_mapping(data: dict) -> list[LogSourceSpec]:
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


def config_specs() -> list[LogSourceSpec]:
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


def source_specs() -> list[LogSourceSpec]:
    merged = {int(spec.port): spec for spec in config_specs()}
    for spec in api.list_custom_port_specs():
        merged[int(spec.port)] = spec
    return sorted(merged.values(), key=lambda item: item.port)
