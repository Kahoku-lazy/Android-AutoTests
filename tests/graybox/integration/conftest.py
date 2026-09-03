"""device_pool 集成测试共享 fixture — 组合注入隔离真实 ADB。

真实写库（django_db），探测层用 mock 隔离，状态机与注册表真实协作。
"""

from unittest.mock import MagicMock

import pytest

from apps.device_pool.manager import DeviceDetector, DeviceRegistry, DeviceStateMachine


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
