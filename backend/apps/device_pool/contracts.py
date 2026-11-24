from dataclasses import dataclass
from datetime import datetime

from backend.models.constants import ConnectionType, DeviceStatus, LockReleaseReason, LockStatus

__all__ = [
    "RUNNER_OCCUPIED_PREFIXES",
    "ConnectionType",
    "DeviceInfo",
    "DeviceStatus",
    "LockReleaseReason",
    "LockStatus",
]

RUNNER_OCCUPIED_PREFIXES = ("ai_agent", "runner-", "task-", "run-")


@dataclass
class DeviceInfo:
    serial: str = ""
    name: str = ""
    model: str = ""
    brand: str = ""
    screen_w: int = 0
    screen_h: int = 0
    android_version: str = ""
    connection_type: ConnectionType = ConnectionType.USB
    connection_addr: str = ""
    status: DeviceStatus = DeviceStatus.ONLINE
    locked_by: str = ""
    locked_at: datetime | None = None
    occupied_by: str = ""
    occupied_at: datetime | None = None
    connected_at: datetime | None = None
    added_by: str = ""
    last_seen: datetime | None = None
    created_at: datetime | None = None
