"""可连地址：丢掉无线调试别名，配对提示仍读原始 adb 列表。"""

from __future__ import annotations

import pytest

from apps.device_pool.manager import DeviceDetector

pytestmark = pytest.mark.unit

_USB = "R5CT62RH88F"
_IP = "192.168.35.57:39569"
_ALIAS_USB = "adb-R5CT62RH88F-chgdtV._adb-tls-connect._tcp"
_ALIAS_ONLY = "adb-RF8N21MSW7A-7tM54C._adb-tls-connect._tcp"
_FOUR = {_USB, _IP, _ALIAS_USB, _ALIAS_ONLY}


def test_connectable_keeps_usb_and_ip_port():
    detector = DeviceDetector()
    assert detector.connectable_serials(_FOUR) == {_USB, _IP}


def test_only_alias_has_no_connectable_address():
    detector = DeviceDetector()
    assert detector.connectable_serials({_ALIAS_ONLY}) == set()


def test_alias_is_not_registered_as_hardware_serial(monkeypatch):
    detector = DeviceDetector()
    monkeypatch.setattr(detector, "fetch_serial_no", lambda addr: "")
    serial, addr = detector.resolve_serial(_ALIAS_ONLY)
    assert serial == ""
    assert addr == _ALIAS_ONLY


def test_wireless_ready_hint_still_sees_alias(monkeypatch):
    detector = DeviceDetector()
    monkeypatch.setattr(detector, "adb_device_serials", lambda: {_ALIAS_ONLY})
    hint = detector.wireless_ready_hint("192.168.35.57")
    assert _ALIAS_ONLY in hint["mdns_addrs"]
    assert hint["can_skip_pair"] is True
