"""灰盒·单元测试 — 无线端口开关编排（变更 add-device-log-port-console）。

零设备、不占固定端口（用临时空闲端口）：
覆盖「无记录＝开启」、三列以配置为准且不动开关、reconcile 开/关/幂等、
关闭即释放端口、启动恢复（含 autoreload 父进程跳过）、页面只读数据与日志尾部读取口径。
"""

from __future__ import annotations

import json
import socket
import time

from pathlib import Path

import pytest

from apps.ai_assistant import api, log_port_service
from engines.device.logbus import (
    LogSourceSpec,
    get_log_bus,
    get_or_create_log_bus,
    stop_log_bus,
)
from engines.device.logfiles import FileLine, LogFileSink

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

SKU = "H6810"
STAMP = "2026-09-28 15:47:41.466"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, settings):
    """每个用例一套干净设置：日志目录指向临时目录，端口来源由用例自己登记。"""
    stop_log_bus()
    settings.DEVICE_LOG_ENABLED = True
    settings.DEVICE_LOG_TCP_PORT = 0  # 不走单端口退化，来源显式登记
    settings.DEVICE_LOG_SOURCES = ""
    settings.DEVICE_LOG_SERIAL_PORT = ""
    settings.DEVICE_LOG_SOURCE_SKU = SKU
    settings.DEVICE_LOG_SOURCE_BAUD = 921600
    settings.DEVICE_LOG_LOG_DIR = str(tmp_path)
    settings.DEVICE_LOG_FILE_MAX_BYTES = 50 * 1024 * 1024
    settings.DEVICE_LOG_TAIL_LINES = 2000
    settings.DEVICE_LOG_TAIL_LINES_MAX = 20000
    yield
    stop_log_bus()


def _register(settings, port: int, sku: str = SKU, baud: int = 921600) -> None:
    settings.DEVICE_LOG_SOURCES = json.dumps({str(port): {"sku": sku, "baud": baud}})


def _wait_port_released(port: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            time.sleep(0.1)
        finally:
            probe.close()
    return False


def _wait_listening(port: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        bus = get_log_bus()
        if bus is not None and bus.is_listening(port):
            return True
        time.sleep(0.05)
    return False


# ── 4.2 三列以配置为准，开关归用户 ───────────────────────────


def test_default_state_is_enabled_without_any_row() -> None:
    """无记录＝开启（升级后行为与现状一致：平台照旧持续监听）。"""
    assert api.is_log_port_enabled(7005) is True
    assert api.get_log_port_enabled_map() == {}


def test_ensure_log_ports_creates_rows_from_config(settings) -> None:
    """登记来源时按配置落三列（端口 / SKU / 波特率）。"""
    _register(settings, 7005, sku="H6810", baud=921600)
    rows = api.ensure_log_ports(log_port_service.source_specs())
    assert [(row.port, row.sku, row.baud) for row in rows] == [(7005, "H6810", 921600)]
    assert rows[0].enabled is True


def test_upsert_refreshes_columns_but_keeps_switch(settings) -> None:
    """改配置只刷新三列，MUST NOT 把用户关掉的开关改回开启。"""
    _register(settings, 7005, baud=921600)
    api.ensure_log_ports(log_port_service.source_specs())
    api.set_log_port_enabled(7005, False)

    _register(settings, 7005, baud=115200)
    rows = api.ensure_log_ports(log_port_service.source_specs())
    assert rows[0].baud == 115200
    assert rows[0].enabled is False


def test_reconcile_noop_when_collection_disabled_globally(settings) -> None:
    """平台总开关关闭时 reconcile 不起任何采集。"""
    _register(settings, _free_port())
    settings.DEVICE_LOG_ENABLED = False
    assert log_port_service.reconcile() == []
    assert get_log_bus() is None


# ── 4.3 reconcile / set_enabled ──────────────────────────────


def test_reconcile_starts_enabled_port(settings) -> None:
    port = _free_port()
    _register(settings, port)
    assert log_port_service.reconcile() == [port]
    assert _wait_listening(port)


def test_reconcile_stops_port_whose_switch_is_off(settings) -> None:
    port = _free_port()
    _register(settings, port)
    log_port_service.reconcile()
    assert _wait_listening(port)

    api.set_log_port_enabled(port, False)
    assert log_port_service.reconcile() == []
    assert _wait_port_released(port)


def test_reconcile_is_idempotent(settings) -> None:
    port = _free_port()
    _register(settings, port)
    assert log_port_service.reconcile() == [port]
    assert log_port_service.reconcile() == [port]
    assert get_log_bus() is not None and get_log_bus().line_count(SKU) == 0


def test_set_enabled_true_start_false_stop_and_release(settings) -> None:
    port = _free_port()
    _register(settings, port)

    opened = log_port_service.set_enabled(port, True)
    assert opened["enabled"] is True and opened["listening"] is True
    assert opened["sku"] == SKU and opened["baud"] == 921600
    assert opened["log_file"] == f"{SKU}_{port}.log"

    closed = log_port_service.set_enabled(port, False)
    assert closed["enabled"] is False and closed["listening"] is False
    assert closed["note"] == f"端口 {port} 已关闭监听"
    assert _wait_port_released(port)


def test_set_enabled_rejects_unregistered_port(settings) -> None:
    _register(settings, 7005)
    with pytest.raises(log_port_service.LogPortUnknown) as excinfo:
        log_port_service.set_enabled(7004, True)
    assert str(excinfo.value) == "端口 7004 未配置为日志来源"


def test_reconcile_keeps_two_ports_independent(settings) -> None:
    """两端口各自开关：只开一个时另一个不监听。"""
    port_a, port_b = _free_port(), _free_port()
    settings.DEVICE_LOG_SOURCES = json.dumps(
        {
            str(port_a): {"sku": "H6810", "baud": 921600},
            str(port_b): {"sku": "H6199", "baud": 921600},
        }
    )
    api.set_log_port_enabled(port_b, False)
    assert log_port_service.reconcile() == [port_a]
    assert _wait_listening(port_a)
    assert get_log_bus() is not None
    assert get_log_bus().is_listening(port_b) is False
    assert _wait_port_released(port_b)


# ── 4.4 启动恢复（含 autoreload 父进程跳过）──────────────────


def _app_config():
    """取真正注册的 AppConfig（`_restore_log_ports` 挂在它上面）。"""
    from django.apps import apps as django_apps

    return django_apps.get_app_config("ai_assistant")


def test_startup_restore_starts_listening(settings) -> None:
    port = _free_port()
    _register(settings, port)
    _app_config()._restore_log_ports()
    assert _wait_listening(port)


def test_startup_restore_skipped_in_autoreload_parent(settings, monkeypatch) -> None:
    """autoreload 父进程只做文件监控：MUST NOT 抢先把日志端口占住。"""
    port = _free_port()
    _register(settings, port)
    monkeypatch.setenv("DJANGO_AUTORELOAD_PARENT", "1")
    _app_config()._restore_log_ports()
    assert get_log_bus() is None


# ── 页面只读数据 ─────────────────────────────────────────────


def test_list_ports_reports_columns_and_runtime(settings) -> None:
    port = _free_port()
    _register(settings, port, sku="H6810", baud=921600)
    log_port_service.reconcile()
    _wait_listening(port)

    rows = log_port_service.list_ports()
    assert len(rows) == 1
    row = rows[0]
    assert (row["port"], row["sku"], row["baud"]) == (port, "H6810", 921600)
    assert row["enabled"] is True and row["listening"] is True
    assert row["log_file"] == f"H6810_{port}.log"
    assert row["size_bytes"] == 0


def test_list_ports_flags_enabled_but_not_listening(settings) -> None:
    """开关开着但端口没监听（例如被别的程序占用）时给出可读提示。"""
    port = _free_port()
    _register(settings, port)
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", port))
    blocker.listen(1)
    try:
        log_port_service.reconcile()
        time.sleep(0.3)
        row = log_port_service.list_ports()[0]
        assert row["enabled"] is True and row["listening"] is False
        assert "未监听" in row["note"]
    finally:
        blocker.close()


def test_read_lines_merges_same_ms_and_sorts_newest_first(settings) -> None:
    """日志窗口口径与 AI 查询一致：同毫秒合并、最新在上、合并条内部保持顺序。"""
    port = _free_port()
    _register(settings, port)
    sink = LogFileSink(
        sku=SKU, port=port, directory=str(settings.DEVICE_LOG_LOG_DIR), max_bytes=10**7
    )
    sink.write(FileLine(timestamp=STAMP, source="tcp", text="first"))
    sink.write(FileLine(timestamp=STAMP, source="tcp", text="second"))
    sink.write(FileLine(timestamp="2026-09-28 15:47:42.466", source="tcp", text="later"))
    sink.close()

    payload = log_port_service.read_lines(port)
    assert payload["conclusion"] == "ok"
    assert payload["line_count"] == 2 and payload["raw_line_count"] == 3
    assert [item["timestamp"] for item in payload["lines"]] == [
        "2026-09-28 15:47:42.466",
        STAMP,
    ]
    assert payload["lines"][1]["text"] == "first\nsecond"


def test_read_lines_reports_no_log_for_empty_file(settings) -> None:
    port = _free_port()
    _register(settings, port)
    payload = log_port_service.read_lines(port)
    assert payload["conclusion"] == "no_log" and payload["lines"] == []
    assert "暂无内容" in payload["note"]


def test_read_lines_unregistered_port_is_readable(settings) -> None:
    _register(settings, 7005)
    payload = log_port_service.read_lines(7004)
    assert payload["conclusion"] == "port_not_configured"
    assert payload["note"] == "端口 7004 未配置为日志来源"
    assert payload["line_count"] == 0 and payload["lines"] == []


def test_read_lines_disabled_port_is_readable_and_read_only(settings) -> None:
    """关闭态：可读结论 + 0 行，且读取本身 MUST NOT 把监听打开。"""
    port = _free_port()
    _register(settings, port)
    api.set_log_port_enabled(port, False)

    payload = log_port_service.read_lines(port)
    assert payload["conclusion"] == "port_disabled"
    assert payload["note"] == f"端口 {port} 已关闭监听"
    assert payload["line_count"] == 0
    assert get_log_bus() is None or not get_log_bus().is_listening(port)


def test_tail_is_clamped_to_platform_limits(settings) -> None:
    settings.DEVICE_LOG_TAIL_LINES = 2000
    settings.DEVICE_LOG_TAIL_LINES_MAX = 5000
    assert log_port_service.clamp_tail(0) == 2000
    assert log_port_service.clamp_tail("abc") == 2000
    assert log_port_service.clamp_tail(10) == 10
    assert log_port_service.clamp_tail(999999) == 5000


def test_disabled_port_note_uses_default_port_when_omitted(settings) -> None:
    """不传端口时看平台默认来源：AI 用默认端口查询同样拿到关闭态结论。"""
    _register(settings, 7005)
    api.set_log_port_enabled(7005, False)
    assert log_port_service.disabled_port_note(0) == "端口 7005 已关闭监听"
    assert log_port_service.disabled_port_note(7005) == "端口 7005 已关闭监听"
    api.set_log_port_enabled(7005, True)
    assert log_port_service.disabled_port_note(0) == ""


def test_bus_reuses_single_instance_with_config(settings) -> None:
    """总线单例：重复取用返回同一实例（配置以首次为准）。"""
    _register(settings, _free_port())
    first = get_or_create_log_bus(log_port_service.build_config())
    second = get_or_create_log_bus(log_port_service.build_config())
    assert first is second


def test_source_specs_shape_is_shared_with_engine(settings) -> None:
    """编排层把来源登记直接交给引擎层（含 SKU 与波特率）。"""
    _register(settings, 7005, sku="H6810", baud=921600)
    specs = log_port_service.source_specs()
    assert specs == [LogSourceSpec(port=7005, sku="H6810", baud=921600)]
