"""Step 0 基线 — 崩溃检测/存活探测现状行为锚定（L1c 引擎收敛前置）。"""

from types import SimpleNamespace

import pytest

from apps.test_runner.executors.ui import recovery as recovery_module

pytestmark = [pytest.mark.unit, pytest.mark.test_runner]


def _err(name="RuntimeError", msg=""):
    cls = type(name, (Exception,), {})
    return cls(msg)


class TestCrashDetection:
    def test_connection_error_is_u2_crash(self):
        assert recovery_module.is_u2_crash(ConnectionError("refused")) is True

    @pytest.mark.parametrize(
        "name",
        ["HTTPTimeoutError", "HTTPError", "ConnectError", "DeviceError", "SessionBrokenError"],
    )
    def test_u2_error_type_names(self, name):
        assert recovery_module.is_u2_crash(_err(name)) is True

    @pytest.mark.parametrize(
        "msg",
        [
            "device offline",
            "uiautomator service quit",
            "connection broken",
            "adb socket error",
            "remote end closed",
            "cannot connect to atx agent",
            "request timed out",
        ],
    )
    def test_u2_keyword_messages(self, msg):
        assert recovery_module.is_u2_crash(RuntimeError(msg)) is True

    def test_plain_error_not_u2_crash(self):
        assert recovery_module.is_u2_crash(ValueError("assert failed")) is False

    @pytest.mark.parametrize(
        "name", ["AdbError", "AdbShellError", "AdbTimeoutError", "MinicapError", "MinitouchError"]
    )
    def test_airtest_error_type_names(self, name):
        assert recovery_module.is_device_crash(_err(name)) is True

    @pytest.mark.parametrize(
        "msg", ["airtest minicap failed", "device not found", "minitouch down"]
    )
    def test_airtest_keyword_messages(self, msg):
        assert recovery_module.is_device_crash(RuntimeError(msg)) is True

    def test_plain_error_not_device_crash(self):
        assert recovery_module.is_device_crash(ValueError("x")) is False


class TestHealthCheck:
    def test_check_u2_alive_none(self):
        assert recovery_module.check_u2_alive(None) is False

    def test_check_u2_alive_probe_raises(self):
        class _Dev:
            @property
            def info(self):
                raise RuntimeError("broken")

        assert recovery_module.check_u2_alive(_Dev()) is False

    def test_check_u2_alive_ok(self):
        assert recovery_module.check_u2_alive(SimpleNamespace(info={})) is True

    def test_check_device_alive_none(self):
        assert recovery_module.check_device_alive(None) is False

    def test_check_device_alive_probe_raises(self):
        class _Conn:
            airtest = SimpleNamespace()

            @property
            def display_info(self):
                raise RuntimeError("broken")

        assert recovery_module.check_device_alive(_Conn()) is False

    def test_check_device_alive_ok(self):
        conn = SimpleNamespace(airtest=SimpleNamespace(display_info={"displayWidth": 1080}))
        assert recovery_module.check_device_alive(conn) is True


class TestReconnect:
    def _fake_engine_cls(self):
        class _FakeEngine:
            def __init__(self):
                self.u2 = SimpleNamespace(name="u2conn")
                self.airtest = SimpleNamespace(name="airconn")
                self.device_info = {"displayWidth": 1080}

            def connect(self, serial):
                self.connected_serial = serial

        return _FakeEngine

    def test_reconnect_u2(self, monkeypatch):
        monkeypatch.setattr(recovery_module, "AirtestU2Engine", self._fake_engine_cls())
        result = recovery_module.reconnect_u2("S")
        assert result.name == "u2conn"

    def test_reconnect_device_returns_connection(self, monkeypatch):
        monkeypatch.setattr(recovery_module, "AirtestU2Engine", self._fake_engine_cls())
        conn = recovery_module.reconnect_device("S")
        assert conn.serial == "S"
        assert conn.u2.name == "u2conn"
        assert conn.airtest.name == "airconn"
        assert conn.info["displayWidth"] == 1080

    def test_wait_and_reconnect_sleeps_then_reconnects(self, monkeypatch):
        slept = []
        monkeypatch.setattr(recovery_module.time, "sleep", lambda s: slept.append(s))
        monkeypatch.setattr(recovery_module, "reconnect_u2", lambda serial: ("conn", serial))

        result = recovery_module.wait_and_reconnect("S", wait_seconds=2)

        assert slept == [2]
        assert result == ("conn", "S")
