"""灰盒·单元测试 — 设备探测（DeviceDetector）。

覆盖 is_wireless / resolve_serial / adb_device_serials / detect / connect：
- 纯逻辑方法零 mock
- 依赖 ADB（subprocess）的方法用 mock 隔离，不跑真实 adb

零 DB；外部 I/O 全部 mock。
"""

from unittest.mock import Mock, patch

import pytest

from apps.device_pool.contracts import ConnectionType
from apps.device_pool.manager import DeviceDetector


@pytest.fixture
def detector() -> DeviceDetector:
    return DeviceDetector()


@pytest.mark.unit
@pytest.mark.device_pool
def test_is_wireless(detector):
    """IP:port 与 mDNS（adb- 前缀）判无线，USB 串号判有线。"""
    assert detector.is_wireless("192.168.1.5:5555") is True
    assert detector.is_wireless("adb-ABC123-_adb-tls-connect._tcp") is True
    assert detector.is_wireless("RF8N21MSW7A") is False


@pytest.mark.unit
@pytest.mark.device_pool
def test_resolve_serial_usb(detector):
    """USB 设备：serial 即地址本身，无连接地址。"""
    assert detector.resolve_serial("RF8N21MSW7A") == ("RF8N21MSW7A", "")


@pytest.mark.unit
@pytest.mark.device_pool
def test_resolve_serial_mdns_when_getprop_empty(detector):
    """无线 mDNS 且 getprop 拿不到串号时，从名称内嵌段拆出 serial。"""
    with patch.object(detector, "fetch_serial_no", return_value=""):
        serial, addr = detector.resolve_serial("adb-ABC123-xyz._adb")
    assert serial == "ABC123"
    assert addr == "adb-ABC123-xyz._adb"


@pytest.mark.unit
@pytest.mark.device_pool
def test_adb_device_serials_parses_device_lines(detector):
    """adb devices 输出只取状态为 device 的地址（跳过 offline）。"""
    stdout = (
        "List of devices attached\n"
        "RF8N21MSW7A\tdevice\n"
        "192.168.1.5:5555\tdevice\n"
        "emulator-5554\toffline\n"
    )
    with patch("apps.device_pool.manager.subprocess.run", return_value=Mock(stdout=stdout)):
        serials = detector.adb_device_serials()
    assert serials == {"RF8N21MSW7A", "192.168.1.5:5555"}


@pytest.mark.unit
@pytest.mark.device_pool
def test_adb_device_serials_returns_empty_on_error(detector):
    """adb 不可用时吞掉异常、返回空集（不抛错）。"""
    with patch("apps.device_pool.manager.subprocess.run", side_effect=Exception("adb not found")):
        assert detector.adb_device_serials() == set()


@pytest.mark.unit
@pytest.mark.device_pool
def test_detect_returns_contract_list(detector):
    """detect 组装契约：USB 与无线分别落 connection_type / connection_addr。"""
    with patch.object(
        detector, "adb_device_serials", return_value={"RF8N21MSW7A", "192.168.1.5:5555"}
    ), patch.object(
        detector,
        "resolve_serial",
        side_effect=lambda addr: (addr, "" if ":" not in addr else addr),
    ):
        devices = detector.detect()

    by_serial = {d.serial: d for d in devices}
    assert set(by_serial) == {"RF8N21MSW7A", "192.168.1.5:5555"}
    assert by_serial["RF8N21MSW7A"].connection_type is ConnectionType.USB
    assert by_serial["RF8N21MSW7A"].connection_addr == ""
    assert by_serial["192.168.1.5:5555"].connection_type is ConnectionType.WIFI
    assert by_serial["192.168.1.5:5555"].connection_addr == "192.168.1.5:5555"


@pytest.mark.unit
@pytest.mark.device_pool
def test_connect_wireless_success(detector):
    """无线 IP:port 连接成功（adb connect + u2 探活均成功，不抛错）。"""
    with patch(
        "apps.device_pool.manager.subprocess.run",
        return_value=Mock(stdout="connected to 192.168.1.5:5555\n", stderr=""),
    ), patch("apps.device_pool.manager.probe_u2"):
        detector.connect("192.168.1.5:5555")  # 不抛错


@pytest.mark.unit
@pytest.mark.device_pool
def test_connect_wireless_adb_fail(detector):
    """无线 adb connect 失败（输出无 connected/already）→ 504 连接超时。"""
    from apps.device_pool.manager import DeviceError

    with patch(
        "apps.device_pool.manager.subprocess.run",
        return_value=Mock(stdout="failed to connect\n", stderr=""),
    ):
        with pytest.raises(DeviceError) as e:
            detector.connect("192.168.1.5:5555")
    assert e.value.status_code == 504


@pytest.mark.unit
@pytest.mark.device_pool
def test_connect_atx_agent_not_running(detector):
    """u2 探活报 atx-agent → 502 ATX Agent 未运行。"""
    from apps.device_pool.manager import DeviceError
    from engines.device.base import EngineConnectError

    with patch(
        "apps.device_pool.manager.subprocess.run",
        return_value=Mock(stdout="connected\n", stderr=""),
    ), patch(
        "apps.device_pool.manager.probe_u2",
        side_effect=EngineConnectError("atx-agent not running"),
    ):
        with pytest.raises(DeviceError) as e:
            detector.connect("192.168.1.5:5555")
    assert e.value.status_code == 502


@pytest.mark.unit
@pytest.mark.device_pool
def test_connect_usb_skips_adb_connect(detector):
    """USB 设备跳过 adb connect，直接 u2 探活。"""
    with patch("apps.device_pool.manager.probe_u2"), patch(
        "apps.device_pool.manager.subprocess.run"
    ) as mock_run:
        detector.connect("RF8N21MSW7A")
    mock_run.assert_not_called()  # USB 不触发 adb connect
