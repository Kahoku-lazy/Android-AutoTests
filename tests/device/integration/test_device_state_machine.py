import pytest

from backend.apps.device_pool.manager import DeviceError
from backend.apps.device_pool.models import Device, DeviceLock


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_update_status_removes_offline_device(state_machine, detector):
    Device.objects.create(serial="OLD123", status="ONLINE")
    detector.adb_device_serials.return_value = set()

    updated, removed = state_machine.update_device_status()

    assert removed == 1
    assert not Device.objects.filter(serial="OLD123").exists()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_update_status_protects_busy_device(state_machine, detector):
    dev = Device.objects.create(serial="BUSY123", status="BUSY", occupied_by="runner-1")
    DeviceLock.objects.create(device=dev, lock_type="process", status="active", timeout_seconds=300)
    detector.adb_device_serials.return_value = set()

    updated, removed = state_machine.update_device_status()

    assert removed == 0
    assert Device.objects.filter(serial="BUSY123").exists()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_lock_wifi_and_unlock(state_machine):
    dev = Device.objects.create(serial="WIFI1", connection_type="WIFI")

    result = state_machine.set_device_lock(dev, True, "1")
    assert result == {"serial": "WIFI1", "locked": True}
    dev.refresh_from_db()
    assert dev.locked_by == "1"
    assert DeviceLock.objects.filter(device=dev, lock_type="user", status="active").exists()

    state_machine.set_device_lock(dev, False, "1")
    dev.refresh_from_db()
    assert dev.locked_by == ""


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_lock_usb_rejected(state_machine):
    dev = Device.objects.create(serial="USB1", connection_type="USB")

    with pytest.raises(DeviceError):
        state_machine.set_device_lock(dev, True, "1")


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_occupy_and_release_observe(state_machine):
    dev = Device.objects.create(serial="DEV1", status="ONLINE")

    state_machine.occupy_observe(dev, "user1")
    dev.refresh_from_db()
    assert dev.status == "BUSY"
    assert dev.occupied_by == "user1"

    state_machine.release_observe(dev)
    dev.refresh_from_db()
    assert dev.status == "ONLINE"
    assert dev.occupied_by == ""


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_release_occupy_protects_runner(state_machine):
    dev = Device.objects.create(serial="RUN1", status="BUSY", occupied_by="runner-1")

    with pytest.raises(DeviceError):
        state_machine.release_occupy(dev)


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_heartbeat_recycles_expired_observe(state_machine, detector):
    dev = Device.objects.create(
        serial="OBS123", status="BUSY", occupied_by="user1", model="X", screen_w=1080
    )
    DeviceLock.objects.create(device=dev, lock_type="observe", status="active", timeout_seconds=0)
    detector.adb_device_serials.return_value = {"OBS123"}
    detector.resolve_serial.side_effect = lambda a: (a, "")
    detector.is_wireless.return_value = False

    result = state_machine.heartbeat_sync()

    dev.refresh_from_db()
    assert dev.status == "ONLINE"
    assert dev.occupied_by == ""
    assert result["total"] == 1
