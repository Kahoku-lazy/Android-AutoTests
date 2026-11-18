"""串口日志写库口 —— 端口登记与监听开关的唯一写点。

跨模块需要读开关状态时走本文件；禁止其它 App 直接读写 `LogPort`。
双轨制：config 行三列由配置同步（`ensure_log_ports`），custom 行三列由本文件
的增删改函数维护；配置同步不创建、不改写、不删除自定义行。
"""

from __future__ import annotations

from engines.device.logbus import LogSourceSpec
from utils.logs import backend_log

from .models import LogPort

__all__ = [
    "create_custom_port",
    "delete_custom_port",
    "ensure_log_ports",
    "get_log_port_enabled_map",
    "is_log_port_enabled",
    "list_custom_port_specs",
    "set_log_port_enabled",
    "update_custom_port",
]


def ensure_log_ports(specs) -> list[LogPort]:
    """按配置登记刷新**配置行**的端口 / SKU / 波特率三列，返回按端口排序的配置行。

    只刷三列，**不动** `enabled`（开关状态归用户，配置变更不得悄悄改回默认）。
    端口已被自定义行占用时跳过并记 warning（自定义行真相源在库，配置不得覆盖）。
    """
    stored = {row.port: row for row in LogPort.objects.all()}
    rows: list[LogPort] = []
    for spec in specs:
        port = int(spec.port)
        channel = str(spec.channel)
        baud = int(spec.baud)
        row = stored.get(port)
        if row is not None and row.origin == LogPort.ORIGIN_CUSTOM:
            backend_log.warning(
                "config port %s already registered as custom; skip config sync", port
            )
            continue
        if row is None:
            row = LogPort.objects.create(
                port=port, sku=channel, baud=baud, origin=LogPort.ORIGIN_CONFIG
            )
        elif row.sku != channel or row.baud != baud:
            row.sku = channel
            row.baud = baud
            row.save(update_fields=["sku", "baud", "updated_at"])
        rows.append(row)
    return sorted(rows, key=lambda item: item.port)


def list_custom_port_specs() -> list[LogSourceSpec]:
    """自定义端口登记 → 来源列表（按端口排序）；供 `sources` 双轨合并。"""
    rows = LogPort.objects.filter(origin=LogPort.ORIGIN_CUSTOM).order_by("port")
    return [LogSourceSpec(port=row.port, sku=row.sku, baud=row.baud) for row in rows]


def create_custom_port(port: int, sku: str, baud: int) -> LogPort:
    """新增自定义端口（默认开启监听）；同号已存在时抛 ValueError（数据侧兜底）。"""
    port = int(port)
    if LogPort.objects.filter(port=port).exists():
        raise ValueError(f"端口 {port} 已登记，不能重复新增")
    return LogPort.objects.create(
        port=port,
        sku=str(sku),
        baud=int(baud),
        origin=LogPort.ORIGIN_CUSTOM,
        enabled=True,
    )


def update_custom_port(port: int, *, sku: str | None = None, baud: int | None = None) -> LogPort:
    """编辑自定义端口的 SKU / 波特率；非自定义行抛 ValueError。"""
    row = LogPort.objects.filter(port=int(port), origin=LogPort.ORIGIN_CUSTOM).first()
    if row is None:
        raise ValueError(f"端口 {int(port)} 不是自定义端口，不能编辑")
    fields: list[str] = []
    if sku is not None:
        row.sku = str(sku)
        fields.append("sku")
    if baud is not None:
        row.baud = int(baud)
        fields.append("baud")
    if fields:
        row.save(update_fields=[*fields, "updated_at"])
    return row


def delete_custom_port(port: int) -> bool:
    """删除自定义端口登记（不动日志文件）；非自定义行返回 False。"""
    deleted, _ = LogPort.objects.filter(port=int(port), origin=LogPort.ORIGIN_CUSTOM).delete()
    return bool(deleted)


def get_log_port_enabled_map() -> dict[int, bool]:
    """端口 → 是否开启监听；无记录＝开启（与平台工具开关同一口径）。"""
    return {row.port: bool(row.enabled) for row in LogPort.objects.all()}


def is_log_port_enabled(port: int) -> bool:
    """该端口是否开启监听；无记录＝开启。"""
    row = LogPort.objects.filter(port=int(port)).first()
    return True if row is None else bool(row.enabled)


def set_log_port_enabled(port: int, enabled: bool) -> None:
    """写单个端口的监听开关（upsert；三列由 `ensure_log_ports` / 自定义增改负责）。"""
    LogPort.objects.update_or_create(port=int(port), defaults={"enabled": bool(enabled)})
