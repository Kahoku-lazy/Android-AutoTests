"""
模块功能：➡️ device_pool 集成用例夹具：注入探测器、注册表与状态机，隔离真实 ADB 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/device/integration/conftest.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 被 tests/device/integration 用例共用（无独立用例）
🏁
"""

from unittest.mock import MagicMock

import pytest

from backend.apps.device_pool.manager import DeviceDetector, DeviceRegistry, DeviceStateMachine


@pytest.fixture
def detector() -> MagicMock:
    """mock 探测器：隔离真实 ADB/u2，测试只关心落库与状态机。"""
    return MagicMock(spec=DeviceDetector)


@pytest.fixture
def registry(detector) -> DeviceRegistry:
    """真实注册表：注入 mock detector，真实写库。"""
    return DeviceRegistry(detector)


@pytest.fixture
def state_machine(detector, registry) -> DeviceStateMachine:
    """真实状态机：注入 mock detector + 真实 registry，真实协作。"""
    return DeviceStateMachine(detector, registry)
