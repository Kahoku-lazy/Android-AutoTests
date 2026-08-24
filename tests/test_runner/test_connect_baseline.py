"""Step 0 基线（3b 显式更新）— 连接预检关键词/常量锚定，目标迁至引擎模块。

consolidate-airtest-u2-engine 将连接实现迁入 engines/android/airtest_u2.py：
- 关键词判定/超时分支 → AirtestU2Engine._adb_connect / connect
- U2_OP_TIMEOUT → 引擎模块；DEVICE_CHECK_TIMEOUT → connect.py（执行编排）
"""

import subprocess

from types import SimpleNamespace

import pytest

from apps.test_runner.executors.ui import connect as connect_module
from engines.android import airtest_u2 as engine_module

pytestmark = [pytest.mark.unit, pytest.mark.test_runner]


class TestConstantsAnchor:
    def test_preflight_timeout_in_connect(self):
        assert connect_module.DEVICE_CHECK_TIMEOUT == 45

    def test_u2_op_timeout_in_engine(self):
        assert engine_module.U2_OP_TIMEOUT == 20


class TestEngineAdbConnect:
    @pytest.fixture(autouse=True)
    def _mock_deps(self, monkeypatch):
        monkeypatch.setattr(
            engine_module, "Android", lambda **kw: SimpleNamespace(serial=kw["serialno"])
        )
        monkeypatch.setattr(
            engine_module,
            "subprocess",
            SimpleNamespace(
                run=lambda *a, **k: SimpleNamespace(stdout="", stderr=""),
                TimeoutExpired=subprocess.TimeoutExpired,
            ),
        )
        monkeypatch.setattr(
            engine_module.u2, "connect", lambda target: SimpleNamespace(settings={}, info={})
        )
        monkeypatch.setattr(
            engine_module.AirtestU2Engine, "_verify_display", lambda self, log=None: {}
        )
        monkeypatch.setattr(
            engine_module.AirtestU2Engine, "_tune_u2_http_timeout", lambda self: None
        )

    def test_usb_serial_skips_adb(self, monkeypatch):
        def _boom(*a, **k):
            raise AssertionError("USB 设备不应调用 adb connect")

        monkeypatch.setattr(engine_module.subprocess, "run", _boom)
        engine = engine_module.AirtestU2Engine()
        engine.connect("SERIAL")
        assert engine.airtest.serial == "SERIAL"

    @pytest.mark.parametrize(
        "output",
        [
            "connected to 192.168.1.5:5555",
            "already connected to 192.168.1.5:5555",
            "已连接 192.168.1.5:5555",
            "已经连接",
            "连接成功",
        ],
    )
    def test_wifi_success_keywords_accepted(self, monkeypatch, output):
        monkeypatch.setattr(
            engine_module.subprocess,
            "run",
            lambda *a, **k: SimpleNamespace(stdout=output, stderr=""),
        )
        engine = engine_module.AirtestU2Engine()
        engine.connect("SN", "192.168.1.5:5555")
        assert engine.airtest.serial == "192.168.1.5:5555"

    def test_wifi_failure_keywords_rejected(self, monkeypatch):
        monkeypatch.setattr(
            engine_module.subprocess,
            "run",
            lambda *a, **k: SimpleNamespace(stdout="failed to connect", stderr=""),
        )
        with pytest.raises(engine_module.EngineConnectError, match="ADB connect failed"):
            engine_module.AirtestU2Engine().connect("SN", "192.168.1.5:5555")

    def test_adb_timeout_raises(self, monkeypatch):
        def _timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd="adb", timeout=10)

        monkeypatch.setattr(engine_module.subprocess, "run", _timeout)
        with pytest.raises(engine_module.EngineConnectError, match="timed out"):
            engine_module.AirtestU2Engine().connect("SN", "192.168.1.5:5555")

    def test_airtest_init_failure_raises(self, monkeypatch):
        def _raise(**kw):
            raise RuntimeError("airtest init failed")

        monkeypatch.setattr(engine_module, "Android", _raise)
        monkeypatch.setattr(
            engine_module.subprocess,
            "run",
            lambda *a, **k: SimpleNamespace(stdout="connected", stderr=""),
        )
        with pytest.raises(engine_module.EngineConnectError, match="Airtest connection failed"):
            engine_module.AirtestU2Engine().connect("SN", "192.168.1.5:5555")


class TestSessionMode:
    """executor-session-toggle：use_session=True 经 EXCLUSIVE 会话。"""

    def _patch_session(self, monkeypatch):
        import apps.device_pool.session as session_module

        class _FakeEngine:
            def __init__(self):
                self.airtest = SimpleNamespace(name="air")
                self.u2 = SimpleNamespace(name="u2conn")
                self.device_info = {"displayWidth": 1080}
                self.connected = None

            def connect(self, serial, addr):
                self.connected = (serial, addr)

        class _FakeSession:
            def __init__(self):
                self.engine = _FakeEngine()
                self.released = False

            def release(self):
                self.released = True

            @classmethod
            def lease(cls, serial, mode, addr="", engine=None):
                return cls()

        monkeypatch.setattr(session_module, "DeviceSession", _FakeSession)
        monkeypatch.setattr(
            connect_module,
            "_query_pool_device",
            lambda s: SimpleNamespace(
                status="ONLINE", connection_type="USB", connection_addr="", name="x"
            ),
        )
        monkeypatch.setattr(connect_module, "_sessions", {})
        return _FakeSession

    def test_use_session_builds_connection_and_registers(self, monkeypatch):
        fake_cls = self._patch_session(monkeypatch)
        conn = connect_module.check_and_connect("SER", use_session=True)
        assert conn.serial == "SER"
        assert conn.airtest.name == "air"
        assert conn.u2.name == "u2conn"
        assert conn.info["displayWidth"] == 1080
        assert "SER" in connect_module._sessions

    def test_release_session_clears(self, monkeypatch):
        self._patch_session(monkeypatch)
        connect_module.check_and_connect("SER", use_session=True)
        connect_module.release_session("SER")
        assert "SER" not in connect_module._sessions
        connect_module.release_session("SER")  # no-op 幂等

    def test_lease_conflict_maps_to_check_error(self, monkeypatch):
        import apps.device_pool.session as session_module

        from apps.device_pool.session import LeaseConflict

        class _BoomSession:
            @classmethod
            def lease(cls, *a, **k):
                raise LeaseConflict("设备 X 已被租用")

        monkeypatch.setattr(session_module, "DeviceSession", _BoomSession)
        monkeypatch.setattr(
            connect_module,
            "_query_pool_device",
            lambda s: SimpleNamespace(
                status="ONLINE", connection_type="USB", connection_addr="", name="x"
            ),
        )
        with pytest.raises(connect_module.DeviceCheckError, match="已被租用"):
            connect_module.check_and_connect("SER", use_session=True)

    def test_settings_default_false(self):
        from django.conf import settings

        assert settings.DEVICE_SESSION_ENABLED is False


class TestConnectU2Method:
    def test_success(self, monkeypatch):
        monkeypatch.setattr(
            engine_module.u2, "connect", lambda serial: SimpleNamespace(serial=serial)
        )
        dev = engine_module.AirtestU2Engine()._connect_u2("SERIAL")
        assert dev.serial == "SERIAL"

    def test_failure_raises(self, monkeypatch):
        def _raise(serial):
            raise RuntimeError("boom")

        monkeypatch.setattr(engine_module.u2, "connect", _raise)
        with pytest.raises(engine_module.EngineConnectError, match="u2.connect failed"):
            engine_module.AirtestU2Engine()._connect_u2("SERIAL")
