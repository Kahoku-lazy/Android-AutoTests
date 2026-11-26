from __future__ import annotations

import time

from typing import Any

from django.conf import settings

from engines.device.logbus import LogSourceSpec
from engines.device.logfiles import tail_lines
from engines.uart_log import MAX_PORTS, PortParams, get_port_switch, reset_port_switch
from engines.uart_log.detect import _port_in_use
from utils.logs import backend_log, capture_file_path
from utils.netinfo import local_lan_ip

from . import api, sources

CAP_NOTE = "同时监听的端口已达 10 个，无法再打开"

__all__ = [
    "clamp_tail",
    "create_port",
    "delete_port",
    "disabled_port_note",
    "list_ports",
    "listen_ip",
    "read_lines",
    "reconcile",
    "set_enabled",
    "spec_for_port",
    "update_port",
]

FALLBACK_TAIL_LINES = 2000
FALLBACK_TAIL_LINES_MAX = 20000
LISTEN_WAIT_SECONDS = 1.0


class LogPortUnknown(ValueError):
    pass


class LogPortInvalid(ValueError):
    pass


class LogPortCapReached(ValueError):
    pass


def listen_ip() -> str:
    configured = str(getattr(settings, "DEVICE_LOG_ADVERTISE_HOST", "") or "").strip()
    return configured or local_lan_ip()


def _origin_for(port: int) -> str:
    custom = {int(spec.port) for spec in api.list_custom_port_specs()}
    return "custom" if int(port) in custom else "config"


def _listen_failure_note(port: int) -> str:
    host = str(getattr(settings, "DEVICE_LOG_TCP_HOST", "0.0.0.0") or "0.0.0.0")
    reason = "端口已被其它程序占用" if _port_in_use(host, int(port)) else "端口绑定失败"
    return f"端口 {int(port)} 监听失败：{reason}"


def _not_listening_note(port: int, switch) -> str:
    if not switch.is_reserved(int(port)) and switch.reserved_count() >= MAX_PORTS:
        return CAP_NOTE
    return _listen_failure_note(port)


def port_not_configured_note(port: int) -> str:
    return f"端口 {int(port)} 未配置为日志来源"


def port_disabled_note(port: int) -> str:
    return f"端口 {int(port)} 已关闭监听"


def _tail_default() -> int:
    return int(getattr(settings, "DEVICE_LOG_TAIL_LINES", FALLBACK_TAIL_LINES))


def _tail_max() -> int:
    return int(getattr(settings, "DEVICE_LOG_TAIL_LINES_MAX", FALLBACK_TAIL_LINES_MAX))


def clamp_tail(value: Any) -> int:
    limit = _tail_max()
    try:
        wanted = int(value)
    except (TypeError, ValueError):
        wanted = _tail_default()
    if wanted <= 0:
        wanted = _tail_default()
    return max(1, min(wanted, max(1, limit)))


def spec_for_port(port: int) -> LogSourceSpec | None:
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
    if not getattr(settings, "DEVICE_LOG_ENABLED", True):
        backend_log.info("device log collection disabled by settings; nothing to reconcile")
        reset_port_switch()
        return []
    specs = sources.source_specs()
    if not specs:
        backend_log.info("no device log port configured; nothing to reconcile")
        return []
    switch = get_port_switch()
    api.ensure_log_ports(sources.config_specs())
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
    specs = sources.source_specs()
    if not specs:
        return []
    switch = get_port_switch()
    config_rows = api.ensure_log_ports(sources.config_specs())
    origins = {int(spec.port): "custom" for spec in api.list_custom_port_specs()}
    for row in config_rows:
        origins.setdefault(int(row.port), "config")
    states = api.get_log_port_enabled_map()
    result: list[dict] = []
    for spec in specs:
        port = int(spec.port)
        enabled = states.get(port, True)
        listening = switch.is_listening(port)
        note = ""
        if enabled and not listening:
            note = _not_listening_note(port, switch)
        result.append(
            _payload(
                spec,
                enabled=enabled,
                listening=listening,
                note=note,
                origin=origins.get(port, "config"),
            )
        )
    return result


def set_enabled(port: int, enabled: bool) -> dict:
    spec = _require_spec(port)
    switch = get_port_switch()
    if enabled and not switch.is_reserved(int(spec.port)) and switch.reserved_count() >= MAX_PORTS:
        backend_log.warning("refuse uart port %s: listen cap %s", spec.port, MAX_PORTS)
        persisted = api.get_log_port_enabled_map().get(int(spec.port), False)
        return _payload(
            spec, enabled=persisted, listening=False, note=CAP_NOTE, origin=_origin_for(port)
        )
    api.ensure_log_ports(sources.config_specs())
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
    listening = switch.is_listening(int(spec.port))
    note = ""
    if not enabled:
        note = port_disabled_note(spec.port)
    elif not listening:
        note = _listen_failure_note(int(spec.port))
    return _payload(spec, enabled=enabled, listening=listening, note=note, origin=_origin_for(port))


def _await_listening(port: int, timeout: float = LISTEN_WAIT_SECONDS) -> bool:
    switch = get_port_switch()
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if switch.is_listening(port):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.02)


def _payload(
    spec: LogSourceSpec, *, enabled: bool, listening: bool, note: str, origin: str
) -> dict:
    path = _capture_path(spec)
    ip = listen_ip()
    return {
        "port": int(spec.port),
        "sku": spec.channel,
        "baud": int(spec.baud),
        "origin": origin,
        "address": f"{ip}:{int(spec.port)}" if ip else "",
        "enabled": bool(enabled),
        "listening": bool(listening),
        "log_file": path.name,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "note": note,
    }


def _validate_port_fields(port: Any, sku: Any, baud: Any) -> tuple[int, str, int]:
    try:
        port_num = int(port)
    except (TypeError, ValueError) as exc:
        raise LogPortInvalid("端口必填且必须为数字") from exc
    if not 1 <= port_num <= 65535:
        raise LogPortInvalid("端口号必须在 1–65535 之间")
    sku_text = str(sku or "").strip()
    if not sku_text:
        raise LogPortInvalid("SKU 名称必填")
    if len(sku_text) > 100:
        raise LogPortInvalid("SKU 名称不能超过 100 个字符")
    try:
        baud_num = int(baud)
    except (TypeError, ValueError) as exc:
        raise LogPortInvalid("波特率必须为数字") from exc
    if baud_num <= 0:
        raise LogPortInvalid("波特率必须为正整数")
    return port_num, sku_text, baud_num


def create_port(port: Any, sku: Any, baud: Any) -> dict:
    port_num, sku_text, baud_num = _validate_port_fields(port, sku, baud)
    if spec_for_port(port_num) is not None:
        raise LogPortInvalid(f"端口 {port_num} 已登记（配置或自定义），不能重复新增")
    switch = get_port_switch()
    if switch.reserved_count() >= MAX_PORTS:
        backend_log.warning("refuse new uart port %s: listen cap %s", port_num, MAX_PORTS)
        raise LogPortCapReached(CAP_NOTE)
    row = api.create_custom_port(port_num, sku_text, baud_num)
    spec = LogSourceSpec(port=row.port, sku=row.sku, baud=row.baud)
    switch.open(_params_for(spec))
    _await_listening(row.port)
    listening = switch.is_listening(row.port)
    backend_log.info(
        "custom log port %s created (sku=%s, listening=%s)", row.port, row.sku, listening
    )
    note = "" if listening else _listen_failure_note(row.port)
    return _payload(spec, enabled=True, listening=listening, note=note, origin="custom")


def update_port(port: int, *, sku: Any = None, baud: Any = None) -> dict:
    spec = _require_spec(port)
    if _origin_for(port) != "custom":
        raise LogPortInvalid(f"端口 {int(port)} 是配置端口，不能编辑")
    if sku is None and baud is None:
        raise LogPortInvalid("没有要修改的字段（sku / baud 至少给一个）")
    new_sku = spec.channel if sku is None else str(sku).strip()
    new_baud = int(spec.baud) if baud is None else baud
    _, new_sku, new_baud = _validate_port_fields(int(spec.port), new_sku, new_baud)
    switch = get_port_switch()
    was_enabled = api.is_log_port_enabled(int(spec.port))
    switch.close(int(spec.port))
    row = api.update_custom_port(int(spec.port), sku=new_sku, baud=new_baud)
    updated = LogSourceSpec(port=row.port, sku=row.sku, baud=row.baud)
    if was_enabled:
        switch.open(_params_for(updated))
        _await_listening(row.port)
    listening = switch.is_listening(row.port)
    backend_log.info("custom log port %s updated (sku=%s)", row.port, row.sku)
    note = ""
    if not was_enabled:
        note = port_disabled_note(row.port)
    elif not listening:
        note = _listen_failure_note(row.port)
    return _payload(updated, enabled=was_enabled, listening=listening, note=note, origin="custom")


def delete_port(port: int) -> dict:
    _require_spec(port)
    if _origin_for(port) != "custom":
        raise LogPortInvalid(f"端口 {int(port)} 是配置端口，不能删除")
    switch = get_port_switch()
    switch.close(int(port))
    api.delete_custom_port(int(port))
    backend_log.info("custom log port %s deleted (log files kept)", port)
    return {
        "port": int(port),
        "deleted": True,
        "note": f"端口 {int(port)} 已删除，监听已停止（历史日志文件保留）",
    }


def read_lines(port: int, tail: Any = 0) -> dict:
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
    return [{"text": raw.rstrip("\r\n")} for raw in raw_lines if raw.strip()]
