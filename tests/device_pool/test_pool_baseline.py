"""Step 0 基线（Step 4 显式更新）— DevicePool 状态管理与委托现状锚定。

mock 注入点：`apps.device_pool.session.get_device_engine` → FakeEngine
（旧 `_u2_instances/_airtest_instances` 接口已随协议收敛消失）。
"""

import pytest

from apps.device_pool.pool import DevicePool
from tests.device_pool.fakes import FakeEngine, clear_sessions, install_fake_engine

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


@pytest.fixture
def pool(monkeypatch):
    clear_sessions()
    monkeypatch.setattr(DevicePool, "_connection_types", {})
    monkeypatch.setattr(DevicePool, "_addresses", {})
    p = DevicePool()
    p.current_serial = ""
    setattr(p, "_info_cache", None)
    return p


class TestAddressResolution:
    def test_usb_serial_used_directly(self, pool):
        pool.switch_to("ABC123")
        assert pool._addr("ABC123") == "ABC123"
        assert pool.get_connection_type() == "USB"

    def test_wifi_addr_preferred_over_serial(self, pool):
        pool.switch_to("SN001", "WIFI", "192.168.1.5:5555")
        assert pool._addr("SN001") == "192.168.1.5:5555"
        assert pool.get_connection_type("SN001") == "WIFI"

    def test_connection_type_inferred_from_colon(self, pool):
        pool.switch_to("1.2.3.4:5555")
        assert pool.get_connection_type() == "WIFI"

    def test_connection_type_cached_across_switches(self, pool):
        pool.switch_to("SN001", "WIFI", "10.0.0.2:5555")
        pool.switch_to("SN001")  # 不带 connection_type 重切，保留已缓存类型
        assert pool.get_connection_type("SN001") == "WIFI"


class TestRemoveDevice:
    def test_clears_caches_session_and_current_serial(self, pool, monkeypatch):
        install_fake_engine(monkeypatch)
        DevicePool._connection_types["X"] = "USB"
        DevicePool._addresses["X"] = "addr"
        pool.switch_to("X")
        pool.info()  # 触发会话建立
        assert "X" in DevicePool._sessions

        pool.remove_device("X")

        assert "X" not in DevicePool._sessions
        assert "X" not in DevicePool._connection_types
        assert "X" not in DevicePool._addresses
        assert pool.current_serial == ""

    def test_remove_other_serial_keeps_current(self, pool):
        pool.switch_to("A")
        pool.remove_device("B")
        assert pool.current_serial == "A"


class TestInfo:
    def test_info_cached_2_seconds(self, pool, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        pool.switch_to("S")

        first = pool.info()
        second = pool.info()

        assert engine.device_info_reads == 1  # 2s 缓存内不重复取数
        assert first["displayWidth"] == 1080
        assert first["connection_type"] == "USB"
        assert second == first

    def test_info_fallback_on_device_error(self, pool, monkeypatch):
        engine = FakeEngine()
        engine.connect_error = "boom"
        install_fake_engine(monkeypatch, engine)
        pool.switch_to("S")

        result = pool.info()

        # 现状行为：失败仅回退 connection_type，不抛异常
        assert result == {"connection_type": "USB"}
        assert "displayWidth" not in result


class TestActionPrimitives:
    def test_action_click_and_swipe_forward(self, pool, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        pool.switch_to("S")

        pool.action_click(10, 20)
        pool.action_swipe("up", 500)

        assert ("click", 10, 20) in engine.calls
        # 现状行为：swipe 按方向计算起终点（1080x2400 上滑：从 (540,1800) 到 (540,1300)）
        assert ("swipe", 540, 1800, 540, 1300, 0.5) in engine.calls

    def test_action_input_taps_then_inputs(self, pool, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        pool.switch_to("S")

        pool.action_input("hi", x=5, y=6)

        assert ("click", 5, 6) in engine.calls
        assert ("input_text", "hi", True) in engine.calls
