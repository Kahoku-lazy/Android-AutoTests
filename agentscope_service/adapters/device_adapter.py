"""Adapter for apps.device_pool — device operations."""
from __future__ import annotations


class DeviceAdapter:
    """Wraps device_pool.api and device_pool.models for tool access."""

    @staticmethod
    def get_online_devices():
        from apps.device_pool.api import get_online_devices
        return get_online_devices()

    @staticmethod
    def get_device_by_serial(serial: str):
        from apps.device_pool.api import get_device_by_serial
        return get_device_by_serial(serial)

    @staticmethod
    def acquire_device(serial: str, user_id: str, timeout: int = 300):
        from apps.device_pool.api import acquire_device
        return acquire_device(serial, user_id=user_id, timeout=timeout)

    @staticmethod
    def release_device(serial: str, reason: str = "manual"):
        from apps.device_pool.api import release_device
        return release_device(serial, reason=reason)

    @staticmethod
    def device_exists(serial: str) -> bool:
        from apps.device_pool.models import Device
        return Device.objects.filter(serial=serial).exists()

    @staticmethod
    def get_device(serial: str):
        from apps.device_pool.models import Device
        return Device.objects.filter(serial=serial).first()

    @staticmethod
    def get_device_pool():
        """Return the global device pool singleton for direct u2 access."""
        from apps.device_pool.api import device
        return device
