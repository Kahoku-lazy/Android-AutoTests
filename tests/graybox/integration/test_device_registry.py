"""灰盒·集成测试 — 设备注册落库（DeviceRegistry）。

业务场景：
- 场景一：新设备接入登记（注册 + 自动采集型号/分辨率）
- 场景二：重复扫描不重复登记（幂等）
- 边界：无线设备拿不到序列号时抛错、不登记

django_db（SQLite :memory:）+ 注入 mock detector（隔离真实 ADB）。
"""

import pytest

from apps.device_pool.contracts import DeviceInfo
from apps.device_pool.manager import DeviceError
from apps.device_pool.models import Device


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_register_new_usb_device(registry, detector):
    """场景一：新 USB 设备接入 → 登记入库 + 自动采集型号/品牌/分辨率。"""
    detector.resolve_serial.return_value = ("RF8N21MSW7A", "")
    detector.is_wireless.return_value = False
    detector.get_info.return_value = DeviceInfo(
        model="SM-G973F", brand="samsung", screen_w=1080, screen_h=2400, android_version="29"
    )

    dev, created = registry.register_device("RF8N21MSW7A", user_id="1")

    assert created is True
    assert dev.connection_type == "USB"
    assert dev.status == "ONLINE"
    assert dev.added_by == "1"
    # 自动采集信息已写库
    assert dev.model == "SM-G973F"
    assert dev.brand == "samsung"
    assert dev.screen_w == 1080
    assert Device.objects.filter(serial="RF8N21MSW7A").count() == 1


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_register_existing_device_not_created(registry, detector):
    """场景二：设备已登记，重复扫描不重复登记、不重复采集。"""
    Device.objects.create(serial="RF8N21MSW7A", model="已有", screen_w=720)
    detector.resolve_serial.return_value = ("RF8N21MSW7A", "")
    detector.is_wireless.return_value = False

    dev, created = registry.register_device("RF8N21MSW7A", user_id="1")

    assert created is False
    assert Device.objects.filter(serial="RF8N21MSW7A").count() == 1
    # 未重复采集
    detector.get_info.assert_not_called()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_register_wireless_resolve_failure_raises(registry, detector):
    """边界：无线设备拿不到真实序列号 → 抛错（502），不登记。"""
    detector.resolve_serial.return_value = ("", "192.168.1.5:5555")

    with pytest.raises(DeviceError):
        registry.register_device("192.168.1.5:5555", user_id="1")
    assert Device.objects.count() == 0
