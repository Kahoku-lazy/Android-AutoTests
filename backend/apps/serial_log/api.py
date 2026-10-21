"""串口日志写库口 —— 端口监听开关的唯一写点。

跨模块需要读开关状态时走本文件；禁止其它 App 直接读写 `LogPort`。
"""

from __future__ import annotations

from .models import LogPort

__all__ = [
    "ensure_log_ports",
    "get_log_port_enabled_map",
    "is_log_port_enabled",
    "set_log_port_enabled",
]


def ensure_log_ports(specs) -> list[LogPort]:
    """按配置登记刷新端口 / SKU / 波特率三列，返回按端口排序的开关行。

    只刷三列，**不动** `enabled`（开关状态归用户，配置变更不得悄悄改回默认）。
    """
    stored = {row.port: row for row in LogPort.objects.all()}
    rows: list[LogPort] = []
    for spec in specs:
        port = int(spec.port)
        channel = str(spec.channel)
        baud = int(spec.baud)
        row = stored.get(port)
        if row is None:
            row = LogPort.objects.create(port=port, sku=channel, baud=baud)
        elif row.sku != channel or row.baud != baud:
            row.sku = channel
            row.baud = baud
            row.save(update_fields=["sku", "baud", "updated_at"])
        rows.append(row)
    return sorted(rows, key=lambda item: item.port)


def get_log_port_enabled_map() -> dict[int, bool]:
    """端口 → 是否开启监听；无记录＝开启（与平台工具开关同一口径）。"""
    return {row.port: bool(row.enabled) for row in LogPort.objects.all()}


def is_log_port_enabled(port: int) -> bool:
    """该端口是否开启监听；无记录＝开启。"""
    row = LogPort.objects.filter(port=int(port)).first()
    return True if row is None else bool(row.enabled)


def set_log_port_enabled(port: int, enabled: bool) -> None:
    """写单个端口的监听开关（upsert；三列由 `ensure_log_ports` 负责）。"""
    LogPort.objects.update_or_create(port=int(port), defaults={"enabled": bool(enabled)})
