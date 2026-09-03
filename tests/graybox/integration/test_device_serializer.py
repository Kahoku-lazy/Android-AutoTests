"""灰盒·集成测试 — 设备展示/可见性（DeviceSerializer）。

业务场景五的可见性规则 + 列表序列化字段。
"""

import pytest

from apps.device_pool.manager import DeviceSerializer
from apps.device_pool.models import Device


@pytest.fixture
def serializer() -> DeviceSerializer:
    return DeviceSerializer()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_usb_device_visible_to_all(serializer):
    """USB 设备恒公开，所有用户可见。"""
    dev = Device.objects.create(serial="USB1", connection_type="USB")
    assert serializer.is_device_visible(dev, "999", set()) is True


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_wifi_device_locked_visible_only_owner(serializer):
    """无线设备锁定后仅锁定者可见，他人不可见。"""
    dev = Device.objects.create(
        serial="WIFI1", connection_type="WIFI", locked_by="1", added_by="1"
    )
    assert serializer.is_device_visible(dev, "1", set()) is True
    assert serializer.is_device_visible(dev, "2", set()) is False


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_wifi_device_unlocked_visible_to_all(serializer):
    """无线设备未锁定公开。"""
    dev = Device.objects.create(serial="WIFI2", connection_type="WIFI")
    assert serializer.is_device_visible(dev, "2", set()) is True


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_admin_sees_all(serializer):
    """管理员全局可见。"""
    dev = Device.objects.create(
        serial="WIFI3", connection_type="WIFI", locked_by="1", added_by="1"
    )
    assert serializer.is_device_visible(dev, "999", {"999"}) is True


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_device_to_dict_fields(serializer):
    """列表序列化：字段完整 + screen 合成 + is_current + remaining。"""
    dev = Device.objects.create(
        serial="DEV1",
        model="X",
        brand="B",
        screen_w=1080,
        screen_h=2400,
        connection_type="USB",
        status="ONLINE",
    )
    d = serializer.device_to_dict(dev, current_serial="DEV1")
    assert d["serial"] == "DEV1"
    assert d["screen"] == "1080x2400"
    assert d["status"] == "ONLINE"
    assert d["connection_type"] == "USB"
    assert d["is_current"] is True
    assert d["remaining"] == 0
