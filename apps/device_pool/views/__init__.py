"""device-pool HTTP routes — re-exports from sub-modules."""

from .connect_views import connect_device, disconnect_device, disconnect_observe, scan_device
from .device_views import activate_device, device_current, list_devices
from .helpers import (
    _adb_device_serials,
    _auto_assign_from_queue,
    _check_timeout_queue,
    _collect_device_info,
    _delete_device_record,
    _device_to_dict,
    _purge_disconnected_devices,
    _release_internal,
    _update_device_status,
)
from .lock_views import (
    device_queue,
    heartbeat,
    join_device_queue,
    leave_device_queue,
    lock_device,
    release_device,
)

__all__ = [
    "list_devices",
    "scan_device",
    "connect_device",
    "disconnect_device",
    "disconnect_observe",
    "device_current",
    "activate_device",
    "lock_device",
    "release_device",
    "heartbeat",
    "device_queue",
    "join_device_queue",
    "leave_device_queue",
]
