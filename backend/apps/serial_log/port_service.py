"""无线端口编排层 —— 把「库里的监听开关」落成「引擎层真正在监听的端口」，并汇总页面数据。

边界：本模块不碰 ORM（写库一律经 `api.py`）、不碰 socket 与文件句柄（在引擎层
`engines/uart_log`），只做三件事：

1. `reconcile()`：读开关状态 → 逐端口启停采集（幂等；平台启动与接口访问都调它）；
2. `set_enabled()`：写开关 + 立即生效（关闭即释放端口）；
3. 页面只读数据：端口列表（含运行时监听状态与日志文件大小）、当前日志文件尾部行。

开关语义（见 `device-log-port-console`）：**无记录 = 开启**；关闭的端口 MUST NOT 被
只读查询或 AI 任务顺手打开。
"""

from __future__ import annotations

import time

from typing import Any

from django.conf import settings

from engines.device.logbus import LogSourceSpec
from engines.device.logfiles import tail_lines
from engines.uart_log import MAX_PORTS, PortParams, get_port_switch, reset_port_switch
from utils.logs import backend_log, capture_file_path

from . import api, sources

CAP_NOTE = "同时监听的端口已达 10 个，无法再打开"

__all__ = [
    "clamp_tail",
    "disabled_port_note",
    "list_ports",
    "read_lines",
    "reconcile",
    "set_enabled",
    "spec_for_port",
]

FALLBACK_TAIL_LINES = 2000
FALLBACK_TAIL_LINES_MAX = 20000
LISTEN_WAIT_SECONDS = 1.0  # 开启后等绑定结果的最长时间（绑定在采集线程里异步完成）


class LogPortUnknown(ValueError):
    """请求了一个未被平台登记的日志端口。"""


def port_not_configured_note(port: int) -> str:
    return f"端口 {int(port)} 未配置为日志来源"


def port_disabled_note(port: int) -> str:
    return f"端口 {int(port)} 已关闭监听"


def _tail_default() -> int:
    return int(getattr(settings, "DEVICE_LOG_TAIL_LINES", FALLBACK_TAIL_LINES))


def _tail_max() -> int:
    return int(getattr(settings, "DEVICE_LOG_TAIL_LINES_MAX", FALLBACK_TAIL_LINES_MAX))


def clamp_tail(value: Any) -> int:
    """读取行数夹紧到 [1, 上限]；未给或非法时取平台默认值。"""
    limit = _tail_max()
    try:
        wanted = int(value)
    except (TypeError, ValueError):
        wanted = _tail_default()
    if wanted <= 0:
        wanted = _tail_default()
    return max(1, min(wanted, max(1, limit)))


def spec_for_port(port: int) -> LogSourceSpec | None:
    """配置里该端口的来源登记；未登记返回 None。"""
    for spec in sources.source_specs():
        if int(spec.port) == int(port):
            return spec
    return None


def _require_spec(port: int) -> LogSourceSpec:
    spec = spec_for_port(port)
    if spec is None:
        raise LogPortUnknown(port_not_configured_note(port))
    return spec


def disabled_port_note(port: int = 0) -> str:
    """端口已登记且监听开关关闭 → 返回可读结论；未登记 / 未关闭 → 空串。

    不传端口时看平台默认来源（现场 7005）：AI 用默认端口查询时同样能拿到关闭态结论。
    本函数只读开关状态，MUST NOT 启动或恢复任何监听。
    """
    specs = sources.source_specs()
    if not specs:
        return ""
    target = int(port) if port else int(specs[0].port)
    if spec_for_port(target) is None:
        return ""
    return "" if api.is_log_port_enabled(target) else port_disabled_note(target)


def _params_for(spec: LogSourceSpec) -> PortParams:
    return PortParams(
        host=str(getattr(settings, "DEVICE_LOG_TCP_HOST", "0.0.0.0") or "0.0.0.0"),
        port=int(spec.port),
        sku=spec.channel,
    )


def _capture_path(spec: LogSourceSpec):
    return capture_file_path(spec.channel, int(spec.port))


def reconcile() -> list[int]:
    """按库里的开关状态启停端口。同时实际监听的端口不超过 10 个。

    返回的是本次要求打开的端口。超出上限的端口保持库里的开关值，但不监听。
    """
    if not getattr(settings, "DEVICE_LOG_ENABLED", True):
        backend_log.info("device log collection disabled by settings; nothing to reconcile")
        reset_port_switch()
        return []
    specs = sources.source_specs()
    if not specs:
        backend_log.info("no device log port configured; nothing to reconcile")
        return []
    switch = get_port_switch()
    api.ensure_log_ports(specs)
    states = api.get_log_port_enabled_map()
    enabled = sorted(int(spec.port) for spec in specs if states.get(int(spec.port), True))
    started = enabled[:MAX_PORTS]
    skipped = enabled[MAX_PORTS:]
    if skipped:
        backend_log.warning("uart listen cap %s: skip ports %s", MAX_PORTS, skipped)
    by_port = {int(spec.port): spec for spec in specs}
    for port in started:
        switch.open(_params_for(by_port[port]))
    for spec in specs:
        port = int(spec.port)
        if port not in started:
            switch.close(port)
    backend_log.debug("device log ports reconciled: started=%s", started)
    return started


def list_ports() -> list[dict]:
    """端口管理页的表格数据：三列取配置，`enabled` 取库，`listening` 取运行时。"""
    specs = sources.source_specs()
    if not specs:
        return []
    switch = get_port_switch()
    rows = api.ensure_log_ports(specs)
    states = {row.port: bool(row.enabled) for row in rows}
    result: list[dict] = []
    for spec in specs:
        port = int(spec.port)
        enabled = states.get(port, True)
        listening = switch.is_listening(port)
        path = _capture_path(spec)
        note = ""
        if enabled and not listening:
            note = "已开启但端口未监听（可能已被其它程序占用）"
        result.append(
            {
                "port": port,
                "sku": spec.channel,
                "baud": int(spec.baud),
                "enabled": enabled,
                "listening": listening,
                "log_file": path.name,
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "note": note,
            }
        )
    return result


def set_enabled(port: int, enabled: bool) -> dict:
    """写开关并立即生效：开启即开始监听，关闭即停止监听并释放端口。"""
    spec = _require_spec(port)
    switch = get_port_switch()
    if enabled and not switch.is_reserved(int(spec.port)) and switch.reserved_count() >= MAX_PORTS:
        backend_log.warning("refuse uart port %s: listen cap %s", spec.port, MAX_PORTS)
        persisted = api.get_log_port_enabled_map().get(int(spec.port), False)
        return _port_payload(spec, enabled=persisted, listening=False, note=CAP_NOTE)
    api.ensure_log_ports(sources.source_specs())
    api.set_log_port_enabled(int(spec.port), bool(enabled))
    if enabled:
        switch.open(_params_for(spec))
        _await_listening(int(spec.port))
    else:
        switch.close(int(spec.port))
    backend_log.info(
        "device log port %s %s (listening=%s)",
        spec.port,
        "开启监听" if enabled else "停止监听",
        switch.is_listening(int(spec.port)),
    )
    path = _capture_path(spec)
    listening = switch.is_listening(int(spec.port))
    note = ""
    if not enabled:
        note = port_disabled_note(spec.port)
    elif not listening:
        note = "已开启但端口未监听（可能已被其它程序占用）"
    return {
        "port": int(spec.port),
        "sku": spec.channel,
        "baud": int(spec.baud),
        "enabled": bool(enabled),
        "listening": listening,
        "log_file": path.name,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "note": note,
    }


def _await_listening(port: int, timeout: float = LISTEN_WAIT_SECONDS) -> bool:
    """短暂等待采集线程完成端口绑定，让开关响应里的 `listening` 是真实结果。"""
    switch = get_port_switch()
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if switch.is_listening(port):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)


def _port_payload(spec: LogSourceSpec, *, enabled: bool, listening: bool, note: str) -> dict:
    path = _capture_path(spec)
    return {
        "port": int(spec.port),
        "sku": spec.channel,
        "baud": int(spec.baud),
        "enabled": bool(enabled),
        "listening": bool(listening),
        "log_file": path.name,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "note": note,
    }


def read_lines(port: int, tail: Any = 0) -> dict:
    """读当前日志文件的尾部若干行（只读当前文件，不碰存档、不启动监听）。

    未登记端口与已关闭监听的端口都返回**可读结论**（不抛错），行数为 0。
    """
    limit = clamp_tail(tail)
    spec = spec_for_port(port)
    if spec is None:
        return {
            "port": int(port),
            "sku": "",
            "log_file": "",
            "tail": limit,
            "line_count": 0,
            "raw_line_count": 0,
            "lines": [],
            "conclusion": "port_not_configured",
            "note": port_not_configured_note(port),
        }
    path = _capture_path(spec)
    payload: dict = {
        "port": int(spec.port),
        "sku": spec.channel,
        "log_file": path.name,
        "tail": limit,
    }
    if not api.is_log_port_enabled(int(spec.port)):
        payload.update(
            {
                "line_count": 0,
                "raw_line_count": 0,
                "lines": [],
                "conclusion": "port_disabled",
                "note": port_disabled_note(spec.port),
            }
        )
        return payload
    rows = _raw_rows(tail_lines(path, limit))
    payload.update(
        {
            "line_count": len(rows),
            "raw_line_count": len(rows),
            "lines": rows,
            "conclusion": "ok" if rows else "no_log",
            "note": "" if rows else "暂无日志",
        }
    )
    return payload


def _raw_rows(raw_lines: list[str]) -> list[dict[str, str]]:
    """按文件顺序返回原文行，不拆时间、不倒序。"""
    return [{"text": raw.rstrip("\r\n")} for raw in raw_lines if raw.strip()]
