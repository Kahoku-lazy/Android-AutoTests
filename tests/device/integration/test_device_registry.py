import pytest

from backend.apps.device_pool.contracts import DeviceInfo
from backend.apps.device_pool.manager import DeviceError
from backend.apps.device_pool.models import Device


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_register_new_usb_device(registry, detector):
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
    assert dev.model == "SM-G973F"
    assert dev.brand == "samsung"
    assert dev.screen_w == 1080
    assert Device.objects.filter(serial="RF8N21MSW7A").count() == 1


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_register_existing_device_not_created(registry, detector):
    Device.objects.create(serial="RF8N21MSW7A", model="已有", screen_w=720)
    detector.resolve_serial.return_value = ("RF8N21MSW7A", "")
    detector.is_wireless.return_value = False

    dev, created = registry.register_device("RF8N21MSW7A", user_id="1")

    assert created is False
    assert Device.objects.filter(serial="RF8N21MSW7A").count() == 1
    detector.get_info.assert_not_called()


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.device_pool
def test_register_wireless_resolve_failure_raises(registry, detector):
    detector.resolve_serial.return_value = ("", "192.168.1.5:5555")

    with pytest.raises(DeviceError):
        registry.register_device("192.168.1.5:5555", user_id="1")
    assert Device.objects.count() == 0
