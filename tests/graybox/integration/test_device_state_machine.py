"""灰盒·集成测试 — 设备状态机（DeviceStateMachine）。

业务场景：
- 场景三：设备断开被移除（离线清理）
- 场景四：使用中的设备断线不误删（执行保护）
- 场景五：无线设备锁定与公开
- 场景六：设备占用与释放（在线 ⇄ 使用中）
- 场景七：超时占用自动回收（防泄漏兜底）

django_db + 注入 mock detector + 真实 registry。
"""

import pytest

from apps.device_pool.manager import DeviceError
from apps.device_pool.models import Device, DeviceLock


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_update_status_removes_offline_device(state_machine, detector):
    """场景三：设备不在线（已拔线）→ 状态同步时从设备库移除。"""
    Device.objects.create(serial="OLD123", status="ONLINE")
    detector.adb_device_serials.return_value = set()

    updated, removed = state_machine.update_device_status()

    assert removed == 1
    assert not Device.objects.filter(serial="OLD123").exists()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_update_status_protects_busy_device(state_machine, detector):
    """场景四：使用中（BUSY + 有效进程锁）的设备断线 → 不误删，保护任务。"""
    dev = Device.objects.create(serial="BUSY123", status="BUSY", occupied_by="runner-1")
    DeviceLock.objects.create(
        device=dev, lock_type="process", status="active", timeout_seconds=300
    )
    detector.adb_device_serials.return_value = set()

    updated, removed = state_machine.update_device_status()

    assert removed == 0
    assert Device.objects.filter(serial="BUSY123").exists()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_lock_wifi_and_unlock(state_machine):
    """场景五：无线设备锁定（记录锁定者）→ 公开（清空锁定）。"""
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
    """场景五边界：USB 设备不支持锁定。"""
    dev = Device.objects.create(serial="USB1", connection_type="USB")

    with pytest.raises(DeviceError):
        state_machine.set_device_lock(dev, True, "1")


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_occupy_and_release_observe(state_machine):
    """场景六：设备被观察占用（在线→使用中）→ 释放（使用中→在线）。"""
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
    """场景六补充：执行引擎占用（runner 前缀）不可手动释放。"""
    dev = Device.objects.create(serial="RUN1", status="BUSY", occupied_by="runner-1")

    with pytest.raises(DeviceError):
        state_machine.release_occupy(dev)


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_heartbeat_recycles_expired_observe(state_machine, detector):
    """场景七：占用超时（关页/崩溃无释放）→ 心跳自动回收，设备恢复在线。"""
    dev = Device.objects.create(
        serial="OBS123", status="BUSY", occupied_by="user1", model="X", screen_w=1080
    )
    DeviceLock.objects.create(
        device=dev, lock_type="observe", status="active", timeout_seconds=0
    )
    detector.adb_device_serials.return_value = {"OBS123"}
    detector.resolve_serial.side_effect = lambda a: (a, "")
    detector.is_wireless.return_value = False

    result = state_machine.heartbeat_sync()

    dev.refresh_from_db()
    assert dev.status == "ONLINE"
    assert dev.occupied_by == ""
    assert result["total"] == 1
