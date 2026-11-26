from unittest.mock import MagicMock

import pytest

from backend.apps.device_pool.manager import DeviceDetector, DeviceRegistry, DeviceStateMachine


@pytest.fixture
def detector() -> MagicMock:
    return MagicMock(spec=DeviceDetector)


@pytest.fixture
def registry(detector) -> DeviceRegistry:
    return DeviceRegistry(detector)


@pytest.fixture
def state_machine(detector, registry) -> DeviceStateMachine:
    return DeviceStateMachine(detector, registry)
