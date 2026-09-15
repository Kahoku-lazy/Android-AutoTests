"""D4-1 不变量：设备域字面量收敛到 `models/` 枚举后，枚举成员写库必须等价于写取值串。

本变更把 `device_pool` 的 62 处状态/类型字面量换成 `models.constants` 的枚举成员，
其正确性**完全依赖** `StrEnum` 的性质（`str(member) == member.value`，见
`test_ssot_enum_strenum.py`）。本用例把该依赖显式钉住：写入、按成员过滤、
`filter().update()` 三条真实代码路径读回的都必须是普通取值串 —— 而不是
`"DeviceStatus.ONLINE"` 这类限定名（那正是 `(str, Enum)` 下的写库错值形态）。
"""

from __future__ import annotations

import pytest

from django.utils import timezone

from apps.device_pool.contracts import (
    ConnectionType,
    DeviceStatus,
    LockReleaseReason,
    LockStatus,
)
from apps.device_pool.models import Device, DeviceLock

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_device_status_and_connection_type_round_trip():
    """写入：枚举成员 → 读回普通取值串。"""
    Device.objects.create(
        serial="ENUM-1",
        status=DeviceStatus.ONLINE,
        connection_type=ConnectionType.USB,
    )

    dev = Device.objects.get(serial="ENUM-1")
    assert dev.status == "ONLINE"
    assert dev.connection_type == "USB"
    assert "DeviceStatus" not in dev.status
    assert "ConnectionType" not in dev.connection_type


def test_filter_by_enum_member_matches_plain_value_column():
    """过滤：按成员查与按字面量查必须命中同一行。"""
    Device.objects.create(
        serial="ENUM-2",
        status=DeviceStatus.BUSY,
        connection_type=ConnectionType.WIFI,
    )

    assert Device.objects.filter(status=DeviceStatus.BUSY).count() == 1
    assert Device.objects.filter(status="BUSY").count() == 1
    assert Device.objects.filter(connection_type=ConnectionType.WIFI).count() == 1


def test_update_fields_with_enum_member_persists_plain_value():
    """`save(update_fields=...)`：状态机写原语的真实路径。"""
    dev = Device.objects.create(serial="ENUM-3", status=DeviceStatus.BUSY)

    dev.status = DeviceStatus.ONLINE
    dev.save(update_fields=["status"])

    refreshed = Device.objects.get(serial="ENUM-3")
    assert refreshed.status == "ONLINE"
    assert "DeviceStatus" not in refreshed.status


def test_device_lock_filter_update_with_enum_members():
    """设备锁的真实写形状：`filter(status=成员).update(status=成员, release_reason=成员)`。"""
    dev = Device.objects.create(serial="ENUM-4", status=DeviceStatus.BUSY)
    DeviceLock.objects.create(
        device=dev,
        user_id="u1",
        lock_type="process",
        status=LockStatus.ACTIVE,
    )

    lock = DeviceLock.objects.get(device=dev)
    assert lock.status == "active"
    assert DeviceLock.objects.filter(status=LockStatus.ACTIVE).count() == 1

    DeviceLock.objects.filter(device=dev, status=LockStatus.ACTIVE).update(
        status=LockStatus.RELEASED,
        released_at=timezone.now(),
        release_reason=LockReleaseReason.MANUAL,
    )

    lock.refresh_from_db()
    assert lock.status == "released"
    assert lock.release_reason == "manual"
    assert "LockStatus" not in lock.status
    assert "LockReleaseReason" not in lock.release_reason


def test_status_order_dict_keys_still_lookup_by_plain_string():
    """回归：以枚举成员为键的排期表，仍可用从库里读出的普通字符串查中。"""
    status_order = {DeviceStatus.ONLINE: 0, DeviceStatus.BUSY: 1}

    assert status_order.get("ONLINE") == 0
    assert status_order.get("BUSY") == 1
