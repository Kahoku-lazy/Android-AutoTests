"""port_service 自定义端口编排：增量生效 / 上限 / 失败细化 / 双轨列表 / 本机 IP。

TCP 监听用假 switch 替身；占用探测与等待绑定用 monkeypatch 替身，零真实网络。
"""

from __future__ import annotations

import pytest

from django.test import override_settings

from backend.apps.serial_log import api, port_service
from backend.apps.serial_log.models import LogPort
from utils.logs import capture_file_path

pytestmark = [pytest.mark.django_db, pytest.mark.integration]

CONFIG_SOURCES = '{"7005": {"sku": "H6810", "baud": 921600}}'


class _FakeSwitch:
    """记录 open/close 的替身：fail_ports 里的端口模拟绑定失败（open 后不监听）。"""

    def __init__(self, fail_ports: set[int] | None = None):
        self.opened: set[int] = set()
        self.closed: list[int] = []
        self.fail_ports = fail_ports or set()

    def is_listening(self, port: int) -> bool:
        return int(port) in self.opened

    def is_reserved(self, port: int) -> bool:
        return int(port) in self.opened

    def reserved_count(self) -> int:
        return len(self.opened)

    def open(self, params) -> bool:
        if int(params.port) not in self.fail_ports:
            self.opened.add(int(params.port))
        return True

    def close(self, port: int) -> bool:
        self.closed.append(int(port))
        self.opened.discard(int(port))
        return True


@pytest.fixture
def fake_switch(monkeypatch):
    switch = _FakeSwitch()
    monkeypatch.setattr(port_service, "get_port_switch", lambda: switch)
    monkeypatch.setattr(port_service, "_await_listening", lambda port, timeout=1.0: True)
    return switch


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_listens_incrementally_without_touching_others(fake_switch):
    fake_switch.opened.add(7005)  # 既有配置端口正在监听
    payload = port_service.create_port(7008, "H717D", 115200)
    assert payload["origin"] == "custom"
    assert payload["enabled"] is True and payload["listening"] is True
    assert fake_switch.closed == []  # 新增不得 close 任何其它端口
    assert 7005 in fake_switch.opened and 7008 in fake_switch.opened
    assert LogPort.objects.get(port=7008).origin == LogPort.ORIGIN_CUSTOM


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_rejects_duplicate_and_invalid_fields(fake_switch):
    port_service.create_port(7008, "H717D", 115200)
    with pytest.raises(port_service.LogPortInvalid, match="7008"):
        port_service.create_port(7008, "X", 9600)
    with pytest.raises(port_service.LogPortInvalid, match="7005"):
        port_service.create_port(7005, "X", 9600)  # 配置端口同号
    for bad in (0, 70000, "abc", None):
        with pytest.raises(port_service.LogPortInvalid):
            port_service.create_port(bad, "X", 9600)
    with pytest.raises(port_service.LogPortInvalid):
        port_service.create_port(7009, "  ", 9600)
    with pytest.raises(port_service.LogPortInvalid):
        port_service.create_port(7009, "X", 0)


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_refused_at_cap(fake_switch):
    fake_switch.opened.update(range(7000, 7010))  # 10 个在监听
    with pytest.raises(port_service.LogPortCapReached):
        port_service.create_port(7099, "X", 9600)
    assert not LogPort.objects.filter(port=7099).exists()
    assert fake_switch.closed == []


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_failure_note_occupied(fake_switch, monkeypatch):
    fake_switch.fail_ports.add(7008)
    monkeypatch.setattr(port_service, "_port_in_use", lambda host, port: True)
    payload = port_service.create_port(7008, "H717D", 115200)
    assert payload["listening"] is False
    assert "监听失败" in payload["note"] and "占用" in payload["note"]
    # 失败保留登记，可直接重试
    row = LogPort.objects.get(port=7008)
    assert row.enabled is True and row.origin == LogPort.ORIGIN_CUSTOM


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_create_failure_note_bind_failed(fake_switch, monkeypatch):
    fake_switch.fail_ports.add(7008)
    monkeypatch.setattr(port_service, "_port_in_use", lambda host, port: False)
    payload = port_service.create_port(7008, "H717D", 115200)
    assert payload["listening"] is False
    assert "端口绑定失败" in payload["note"]


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_update_restarts_only_own_port(fake_switch):
    port_service.create_port(7008, "H717D", 115200)
    fake_switch.opened.add(7005)
    fake_switch.closed.clear()
    payload = port_service.update_port(7008, sku="H717D-V2", baud=460800)
    assert fake_switch.closed == [7008]
    assert 7005 in fake_switch.opened
    assert payload["sku"] == "H717D-V2" and payload["baud"] == 460800
    assert payload["listening"] is True


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_update_and_delete_reject_config_port(fake_switch):
    with pytest.raises(port_service.LogPortInvalid, match="配置端口"):
        port_service.update_port(7005, sku="X")
    with pytest.raises(port_service.LogPortInvalid, match="配置端口"):
        port_service.delete_port(7005)
    with pytest.raises(port_service.LogPortUnknown):
        port_service.update_port(7099, sku="X")


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_delete_stops_listen_and_keeps_log_file(fake_switch):
    port_service.create_port(7008, "TESTSKU", 115200)
    path = capture_file_path("TESTSKU", 7008)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("evidence line\n", encoding="utf-8")
    try:
        payload = port_service.delete_port(7008)
        assert payload["deleted"] is True
        assert 7008 in fake_switch.closed
        assert not LogPort.objects.filter(port=7008).exists()
        assert path.is_file(), "删除端口不得删除历史日志文件"
    finally:
        path.unlink(missing_ok=True)


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES, DEVICE_LOG_ADVERTISE_HOST="10.0.0.9")
def test_list_ports_dual_track_with_address(fake_switch):
    port_service.create_port(7008, "H717D", 115200)
    rows = port_service.list_ports()
    by_port = {row["port"]: row for row in rows}
    assert by_port[7005]["origin"] == "config"
    assert by_port[7008]["origin"] == "custom"
    assert by_port[7008]["address"] == "10.0.0.9:7008"
    assert port_service.listen_ip() == "10.0.0.9"


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES, DEVICE_LOG_ADVERTISE_HOST="")
def test_listen_ip_falls_back_to_probe(fake_switch, monkeypatch):
    monkeypatch.setattr(port_service, "local_lan_ip", lambda: "192.168.35.100")
    assert port_service.listen_ip() == "192.168.35.100"


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES)
def test_read_lines_supports_custom_port(fake_switch):
    port_service.create_port(7008, "H717D", 115200)
    payload = port_service.read_lines(7008)
    assert payload["sku"] == "H717D"
    assert payload["conclusion"] in ("no_log", "ok")  # 不是 port_not_configured


@override_settings(DEVICE_LOG_SOURCES='{"7008": {"sku": "LATER-CONFIG", "baud": 9600}}')
def test_merge_prefers_custom_when_config_adds_same_port_later(fake_switch):
    api.create_custom_port(7008, "H717D", 115200)
    specs = {int(spec.port): spec for spec in port_service.sources.source_specs()}
    assert specs[7008].sku == "H717D"  # 同号时自定义行优先，配置同步跳过


@override_settings(DEVICE_LOG_SOURCES=CONFIG_SOURCES, DEVICE_LOG_ENABLED=True)
def test_reconcile_restores_custom_ports(fake_switch):
    port_service.create_port(7008, "H717D", 115200)
    port_service.create_port(7009, "X6000", 921600)
    api.set_log_port_enabled(7009, False)
    fake_switch.opened.clear()
    started = port_service.reconcile()
    assert 7005 in started and 7008 in started
    assert 7009 not in started  # 关闭的自定义端口不恢复
