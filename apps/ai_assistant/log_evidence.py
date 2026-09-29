"""设备日志证据（Django 侧装配）—— 把 settings 的采集配置交给引擎层日志总线，并注入 AI 引擎。

分层：采集句柄与缓冲在 `engines/device/logbus.py`（引擎层），本模块只做三件事：
1. 从 settings 组装 `LogBusConfig`（端口来源登记含 SKU 与波特率、日志目录与单文件上限）；
2. 提供 `open_window` / `read_window` 协议对象给引擎（引擎不碰句柄、也不 import 本模块）；
3. 提供当前总线给端口编排（`log_port_service`）与只读查询工具使用。

**端口监听开关归用户**（AI 工具箱「无线端口」）：本模块 MUST NOT 自行启动采集，
只使用此刻真正在监听的端口；没有任何端口在监听时返回 `None`，任务照常执行、
验收阶段标注「无日志证据」。
"""

from __future__ import annotations

import json
import logging

from django.conf import settings

from engines.device.logbus import (
    DEFAULT_CHANNEL,
    LogBus,
    LogBusConfig,
    LogSourceSpec,
    get_log_bus,
)

logger = logging.getLogger(__name__)

__all__ = ["DeviceLogEvidence", "build_config", "ensure_log_evidence", "source_specs"]


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
            logger.error("DEVICE_LOG_SOURCES 端口不是数字，已忽略: %s", key)
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
            logger.error("DEVICE_LOG_SOURCES 不是合法 JSON，已忽略: %s", raw)
            data = {}
        specs = _specs_from_mapping(data if isinstance(data, dict) else {})
        if specs:
            return specs
    sku = str(getattr(settings, "DEVICE_LOG_SOURCE_SKU", "") or "").strip() or DEFAULT_CHANNEL
    port = int(settings.DEVICE_LOG_TCP_PORT)
    return [LogSourceSpec(port=port, sku=sku, baud=_default_baud())] if port else []


def build_config() -> LogBusConfig:
    """settings → 采集配置（含端口来源登记与日志文件归档参数）。"""
    specs = source_specs()
    return LogBusConfig(
        enabled=bool(settings.DEVICE_LOG_ENABLED),
        tcp_host=str(settings.DEVICE_LOG_TCP_HOST),
        tcp_port=int(settings.DEVICE_LOG_TCP_PORT),
        serial_port=str(settings.DEVICE_LOG_SERIAL_PORT),
        serial_baud=int(settings.DEVICE_LOG_SERIAL_BAUD),
        buffer_seconds=float(settings.DEVICE_LOG_BUFFER_SECONDS),
        buffer_max_lines=int(settings.DEVICE_LOG_BUFFER_MAX_LINES),
        window_seconds=float(settings.DEVICE_LOG_WINDOW_SECONDS),
        baseline_seconds=float(settings.DEVICE_LOG_BASELINE_SECONDS),
        keyword_file=str(settings.DEVICE_LOG_KEYWORD_FILE),
        # 通道名用被测设备 SKU（如 H6810）：这条日志来源就是它，证据里也会标出来源
        channel=specs[0].channel if specs else DEFAULT_CHANNEL,
        sources=specs,
        log_dir=str(getattr(settings, "DEVICE_LOG_LOG_DIR", "") or ""),
        file_max_bytes=int(getattr(settings, "DEVICE_LOG_FILE_MAX_BYTES", 0) or 0),
    )


class DeviceLogEvidence:
    """注入 AI 引擎的日志证据提供者（引擎只经 open_window / read_window 调用）。"""

    def __init__(self, bus: LogBus) -> None:
        self._bus = bus

    def open_window(self, device: str, label: str = "") -> str:
        return self._bus.open_window(device, label)

    def read_window(
        self,
        device: str,
        window_id: str = "",
        action_times: list[str] | None = None,
        wait_seconds: float = 0.0,
    ) -> dict:
        """读窗口；未显式要求等待时，按平台配置等到「最后一次动作 + 取证阈值」再读。"""
        wait = float(wait_seconds) or float(settings.DEVICE_LOG_WINDOW_SECONDS)
        return self._bus.read_window(
            device,
            window_id=window_id,
            action_times=list(action_times or []),
            wait_seconds=wait,
        )


def ensure_log_evidence() -> DeviceLogEvidence | None:
    """取当前**已在监听**的日志总线并返回证据提供者；没有端口在监听时返回 None。

    本函数 MUST NOT 启动采集：端口监听开关由用户在 AI 工具箱「无线端口」控制，
    关着的端口不因一次设备任务被悄悄打开（关闭态即「验收无日志证据」）。
    """
    if not settings.DEVICE_LOG_ENABLED:
        logger.info("device log evidence disabled by settings; verifier runs without log evidence")
        return None
    bus = get_log_bus()
    if bus is None:
        logger.info("device log bus not started; verifier runs without log evidence")
        return None
    if not bus.running_ports() and not str(settings.DEVICE_LOG_SERIAL_PORT or "").strip():
        logger.info("device log ports are all off; verifier runs without log evidence")
        return None
    return DeviceLogEvidence(bus)
