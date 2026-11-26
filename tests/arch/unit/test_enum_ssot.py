from __future__ import annotations

import pytest

from backend.apps.device_pool import contracts as device_contracts
from backend.models import constants as models_constants

pytestmark = [pytest.mark.unit]


def test_device_status_is_models_ssot_object():
    assert device_contracts.DeviceStatus is models_constants.DeviceStatus
    assert {(m.name, m.value) for m in device_contracts.DeviceStatus} == {
        ("ONLINE", "ONLINE"),
        ("BUSY", "BUSY"),
    }


def test_connection_type_is_models_ssot_object():
    assert device_contracts.ConnectionType is models_constants.ConnectionType
    assert {(m.name, m.value) for m in device_contracts.ConnectionType} == {
        ("USB", "USB"),
        ("WIFI", "WIFI"),
    }


def test_device_enums_keep_str_semantics():
    assert device_contracts.DeviceStatus.ONLINE == "ONLINE"
    assert device_contracts.DeviceStatus.BUSY == "BUSY"
    assert device_contracts.ConnectionType.WIFI == "WIFI"
    assert device_contracts.ConnectionType.USB == "USB"
