from dataclasses import dataclass
from datetime import datetime

from rest_framework.exceptions import APIException

from backend.models.constants import ConnectionType, DeviceStatus, LockReleaseReason, LockStatus
from utils.logs import backend_log

__all__ = [
    "RUNNER_OCCUPIED_PREFIXES",
    "ConnectionType",
    "DeviceError",
    "DeviceInfo",
    "DeviceStatus",
    "LockReleaseReason",
    "LockStatus",
]

RUNNER_OCCUPIED_PREFIXES = ("ai_agent", "runner-", "task-", "run-")


class DeviceError(APIException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.log = backend_log
        self.status_code = status_code


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
