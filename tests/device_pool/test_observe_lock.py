"""observe 占用锁单测（fix-observe-leak：真机发现 #4）。"""

from datetime import timedelta

import pytest

from django.utils import timezone

from apps.device_pool.models import Device, DeviceLock
from apps.device_pool.service import (
    OBSERVE_LOCK_TTL,
    heartbeat_sync,
    occupy_observe,
    release_observe,
)

pytestmark = [pytest.mark.integration, pytest.mark.device_pool, pytest.mark.django_db]


@pytest.fixture
def device():
    return Device.objects.create(serial="OBS-1", status="ONLINE", occupied_by="")


class TestOccupyObserve:
    def test_occupy_creates_observe_lock(self, device):
        occupy_observe(device, "admin")
        device.refresh_from_db()
        assert device.status == "BUSY"
        assert device.occupied_by == "admin"
        lock = DeviceLock.objects.get(device=device, lock_type="observe", status="active")
        assert lock.timeout_seconds == OBSERVE_LOCK_TTL

    def test_release_observe_clears(self, device):
        occupy_observe(device, "admin")
        release_observe(device)
        device.refresh_from_db()
        assert device.status == "ONLINE"
        assert device.occupied_by == ""
        assert DeviceLock.objects.filter(device=device, status="active").count() == 0

    def test_release_observe_protects_runner_prefix(self, device):
        occupy_observe(device, "admin")
        device.occupied_by = "runner-xyz"
        device.save(update_fields=["occupied_by"])
        release_observe(device)
        device.refresh_from_db()
        assert device.occupied_by == "runner-xyz"  # 执行引擎占用不受观察释放影响


class TestHeartbeatReclaim:
    def test_expired_observe_lock_reclaimed(self, device):
        occupy_observe(device, "admin")
        # 把锁置为已过期（locked_at 提前超时窗口）
        lock = DeviceLock.objects.get(device=device, lock_type="observe", status="active")
        lock.locked_at = timezone.now() - timedelta(seconds=OBSERVE_LOCK_TTL + 60)
        lock.save(update_fields=["locked_at"])

        heartbeat_sync()

        device.refresh_from_db()
        assert device.status == "ONLINE"
        assert device.occupied_by == ""
        assert DeviceLock.objects.filter(device=device, status="active").count() == 0

    def test_active_observe_lock_not_reclaimed(self, device):
        occupy_observe(device, "admin")
        heartbeat_sync()
        device.refresh_from_db()
        assert device.status == "BUSY"  # 未过期不回收
