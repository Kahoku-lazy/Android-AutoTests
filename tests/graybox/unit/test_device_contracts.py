"""灰盒·单元测试 — device_pool 数据契约（contracts.py）。

覆盖 DeviceStatus / ConnectionType 枚举与 DeviceInfo 数据契约：
- 枚举值正确、str 语义（对外仍是字符串）
- DeviceInfo 默认值
- 契约字段与 Device 模型（dp_devices 表）一一对应、顺序一致（防漂移）

零 I/O 零 DB。
"""

from dataclasses import fields

import pytest

from apps.device_pool.contracts import ConnectionType, DeviceInfo, DeviceStatus
from apps.device_pool.models import Device


@pytest.mark.unit
@pytest.mark.device_pool
def test_device_status_values():
    """状态枚举只有 ONLINE/BUSY 两态，且与字符串比较相等（对外契约不变）。"""
    assert DeviceStatus.ONLINE.value == "ONLINE"
    assert DeviceStatus.BUSY.value == "BUSY"
    assert DeviceStatus.ONLINE == "ONLINE"
    assert {e.value for e in DeviceStatus} == {"ONLINE", "BUSY"}


@pytest.mark.unit
@pytest.mark.device_pool
def test_connection_type_values():
    """连接类型枚举 USB/WIFI。"""
    assert ConnectionType.USB.value == "USB"
    assert ConnectionType.WIFI.value == "WIFI"
    assert {e.value for e in ConnectionType} == {"USB", "WIFI"}


@pytest.mark.unit
@pytest.mark.device_pool
def test_device_info_defaults():
    """DeviceInfo 默认值：空串、USB、ONLINE、零值、None 时间戳。"""
    info = DeviceInfo()
    assert info.serial == ""
    assert info.connection_type is ConnectionType.USB
    assert info.status is DeviceStatus.ONLINE
    assert info.screen_w == 0
    assert info.screen_h == 0
    assert info.locked_at is None
    assert info.occupied_at is None
    assert info.last_seen is None
    assert info.created_at is None


@pytest.mark.unit
@pytest.mark.device_pool
def test_device_info_fields_match_model():
    """数据契约字段与 dp_devices 表业务字段一一对应、顺序一致。

    排除 Django 自动主键 id：契约承载「检测/信息数据」，id 是 DB 自增主键，
    不属契约范畴。
    """
    contract_fields = [f.name for f in fields(DeviceInfo)]
    model_fields = [f.name for f in Device._meta.fields if f.name != "id"]
    assert contract_fields == model_fields
