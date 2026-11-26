from unittest.mock import MagicMock

import pytest

from backend.apps.device_pool import api
from backend.apps.device_pool.contracts import ConnectionType, DeviceError, LockReleaseReason
from backend.apps.device_pool.manager import DeviceDetector
from backend.apps.device_pool.models import Device
from backend.apps.device_pool.pool import device as device_pool

pytestmark = [pytest.mark.integration, pytest.mark.django_db, pytest.mark.device_pool]


@pytest.fixture(autouse=True)
def _reset_current_pointer():
    device_pool.current_serial = ""
    yield
    device_pool.current_serial = ""


@pytest.fixture
def detector():
    return MagicMock(spec=DeviceDetector)


def test_activate_registers_missing_device_and_switches_current(detector, monkeypatch):
    registry = MagicMock()

    def fake_register(serial, user_id):
        return Device.objects.create(serial=serial, status="ONLINE"), True

    registry.register_device.side_effect = fake_register
    monkeypatch.setattr(api, "detector", detector)
    monkeypatch.setattr(api, "registry", registry)

    assert api.activate_device("NEW1", "7") == "NEW1"
    registry.register_device.assert_called_once_with("NEW1", "7")
    assert registry.touch_last_seen.call_count == 1
    assert device_pool.current_serial == "NEW1"


def test_activate_busy_device_is_rejected(monkeypatch):
    Device.objects.create(serial="BUSY1", status="BUSY")
    monkeypatch.setattr(api, "detector", MagicMock(spec=DeviceDetector))

    with pytest.raises(DeviceError) as exc:
        api.activate_device("BUSY1", "7")

    assert exc.value.status_code == 400
    assert device_pool.current_serial == ""


def test_connect_observe_occupies_and_collects(detector, monkeypatch):
    dev = Device.objects.create(
        serial="1.2.3.4:5555",
        status="ONLINE",
        connection_type=ConnectionType.WIFI,
        connection_addr="1.2.3.4:5555",
    )
    detector.is_wireless.return_value = True
    registry = MagicMock()
    state_machine = MagicMock()
    monkeypatch.setattr(api, "detector", detector)
    monkeypatch.setattr(api, "registry", registry)
    monkeypatch.setattr(api, "state_machine", state_machine)

    payload = api.connect_device(dev.serial, "7", mode="observe")

    detector.connect.assert_called_once_with("1.2.3.4:5555")
    registry.set_connection_state.assert_called_once_with(dev, ConnectionType.WIFI)
    registry.collect_device_info.assert_called_once_with(dev, "1.2.3.4:5555")
    state_machine.occupy_observe.assert_called_once_with(dev, "7")
    assert payload["serial"] == dev.serial
    assert device_pool.current_serial == dev.serial


def test_connect_busy_device_is_rejected(monkeypatch):
    Device.objects.create(serial="BUSY2", status="BUSY")
    monkeypatch.setattr(api, "detector", MagicMock(spec=DeviceDetector))

    with pytest.raises(DeviceError) as exc:
        api.connect_device("BUSY2", "7")

    assert exc.value.status_code == 409


def test_disconnect_rejects_usb_and_deletes_wifi(monkeypatch):
    registry = MagicMock()
    monkeypatch.setattr(api, "registry", registry)
    Device.objects.create(serial="USB1", status="ONLINE", connection_type=ConnectionType.USB)

    with pytest.raises(DeviceError) as exc:
        api.disconnect_device("USB1")
    assert exc.value.status_code == 400

    wifi = Device.objects.create(
        serial="1.1.1.1:5555", status="ONLINE", connection_type=ConnectionType.WIFI
    )
    api.disconnect_device(wifi.serial)
    registry.delete_device_record.assert_called_once_with(wifi, reason=LockReleaseReason.DISCONNECT)


def test_lock_and_release_go_through_state_machine():
    dev = Device.objects.create(
        serial="WIFI9", status="ONLINE", connection_type=ConnectionType.WIFI
    )

    assert api.set_device_lock(dev.serial, True, "7") == {"serial": "WIFI9", "locked": True}
    dev.refresh_from_db()
    assert dev.locked_by == "7"

    dev.status = "BUSY"
    dev.occupied_by = "7"
    dev.save(update_fields=["status", "occupied_by"])

    assert api.release_occupy(dev.serial) == {"serial": "WIFI9", "released": True}
    dev.refresh_from_db()
    assert dev.status == "ONLINE"
    assert dev.occupied_by == ""


def test_list_devices_returns_shape_and_selects_first_online(monkeypatch):
    Device.objects.create(serial="A1", status="ONLINE")
    Device.objects.create(serial="B1", status="BUSY")
    monkeypatch.setattr(api, "state_machine", MagicMock())

    payload = api.list_devices("")

    assert payload["current"] == "A1"
    assert [row["serial"] for row in payload["devices"]] == ["A1", "B1"]
    assert payload["devices"][0]["is_current"] is True
