"""D4 契约：枚举唯一真相源在 `models/` —— device_pool 不得重复定义设备枚举。

本用例用 `is`（而非值相等）断言：值相等在「两份重复定义」下同样会通过，
只有 `is` 能证明全仓只有一个定义。见 `设计方案-Django设计系统分层.html` 行 269/331/375。
"""

from __future__ import annotations

import pytest

from apps.device_pool import contracts as device_contracts
from models import constants as models_constants

pytestmark = [pytest.mark.unit]


def test_device_status_is_models_ssot_object():
    """device_pool 的 DeviceStatus 必须**就是** models.constants 的那一个对象。"""
    assert device_contracts.DeviceStatus is models_constants.DeviceStatus
    assert {(m.name, m.value) for m in device_contracts.DeviceStatus} == {
        ("ONLINE", "ONLINE"),
        ("BUSY", "BUSY"),
    }


def test_connection_type_is_models_ssot_object():
    """device_pool 的 ConnectionType 必须**就是** models.constants 的那一个对象。"""
    assert device_contracts.ConnectionType is models_constants.ConnectionType
    assert {(m.name, m.value) for m in device_contracts.ConnectionType} == {
        ("USB", "USB"),
        ("WIFI", "WIFI"),
    }


def test_device_enums_keep_str_semantics():
    """保持 str, Enum 语义：与字面量比较仍成立（后续收敛字面量依赖此性质）。"""
    assert device_contracts.DeviceStatus.ONLINE == "ONLINE"
    assert device_contracts.DeviceStatus.BUSY == "BUSY"
    assert device_contracts.ConnectionType.WIFI == "WIFI"
    assert device_contracts.ConnectionType.USB == "USB"
