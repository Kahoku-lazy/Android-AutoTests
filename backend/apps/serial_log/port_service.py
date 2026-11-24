"""
模块功能：➡️ 无线端口编排层 —— 把「库里的监听开关」落成「引擎层真正在监听的端口」，并汇总页面数据 🏁
Python 调试：➡️ python -m backend.apps.serial_log.port_service 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 serial_log 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import time

from typing import Any

from django.conf import settings

from engines.device.logbus import LogSourceSpec
from engines.device.logfiles import tail_lines
from engines.uart_log import MAX_PORTS, PortParams, get_port_switch, reset_port_switch

# 公共 available() 不区分失败原因；这里只读复用占用探测细化 note，不改引擎契约。
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
LISTEN_WAIT_SECONDS = 1.0  # 开启后等绑定结果的最长时间（绑定在采集线程里异步完成）


class LogPortUnknown(ValueError):
    """请求了一个未被平台登记的日志端口。"""


class LogPortInvalid(ValueError):
    """端口登记字段校验失败或操作不被允许（可读错误，交调用方改请求）。"""


class LogPortCapReached(ValueError):
    """同时监听端口已达上限，拒绝新增 / 开启。"""


def listen_ip() -> str:
    """页面展示的本机监听 IP：配置覆盖优先，否则出站探测；取不到返回空串。"""
    configured = str(getattr(settings, "DEVICE_LOG_ADVERTISE_HOST", "") or "").strip()
    return configured or local_lan_ip()


def _origin_for(port: int) -> str:
    """端口来源：custom 行优先（与 sources 合并口径一致），其余为 config。"""
    custom = {int(spec.port) for spec in api.list_custom_port_specs()}
    return "custom" if int(port) in custom else "config"


def _listen_failure_note(port: int) -> str:
    """开启但未监听时的可读失败原因：区分被占用与绑定失败。"""
    host = str(getattr(settings, "DEVICE_LOG_TCP_HOST", "0.0.0.0") or "0.0.0.0")
    reason = "端口已被其它程序占用" if _port_in_use(host, int(port)) else "端口绑定失败"
    return f"端口 {int(port)} 监听失败：{reason}"


def _not_listening_note(port: int, switch) -> str:
    """enabled 但未 listening 的 note：超限保持开关值不监听，其余按绑定失败细化。"""
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
    """端口管理页的表格数据：三列取双轨登记，`enabled` 取库，`listening` 取运行时。"""
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
    """写开关并立即生效：开启即开始监听，关闭即停止监听并释放端口。"""
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
    """短暂等待采集线程完成端口绑定，让开关响应里的 `listening` 是真实结果。"""
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
    """端口行统一载荷：三列 + 来源 + 完整监听地址 + 开关 / 运行时状态 + 文件信息。"""
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
    """新增端口字段校验：端口 1–65535、SKU 必填 ≤100、波特率正整数。"""
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
    """新增自定义端口并立即监听（单端口增量，不触碰其它端口）。

    Raises:
        LogPortInvalid: 字段非法或端口已登记。
        LogPortCapReached: 同时监听已达上限。
    """
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
    """编辑自定义端口（SKU / 波特率）：只重启被编辑的这一个端口。

    Raises:
        LogPortUnknown: 端口未登记。
        LogPortInvalid: 配置端口不可编辑、字段非法或无可改字段。
    """
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
    """删除自定义端口：停监听释放端口、删登记；历史日志文件保留。

    Raises:
        LogPortUnknown: 端口未登记。
        LogPortInvalid: 配置端口不可删除。
    """
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
