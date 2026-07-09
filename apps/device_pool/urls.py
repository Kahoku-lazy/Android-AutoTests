"""device-pool URL routing — 12 endpoints under /api/devices/."""

from django.urls import path
from .views import (
    list_devices,
    scan_device,
    connect_device,
    disconnect_device,
    disconnect_observe,
    activate_device,
    device_current,
    lock_device,
    release_device,
    device_queue,
    heartbeat,
    join_device_queue,
    leave_device_queue,
)

app_name = "devices"

urlpatterns = [
    # v1 (named before wildcards)
    path("", list_devices, name="list"),
    path("scan", scan_device, name="scan"),
    path("current", device_current, name="current"),
    path("heartbeat", heartbeat, name="heartbeat"),
    path("queue", device_queue, name="queue"),
    # v1 serial routes
    path("<str:serial>", connect_device, name="connect"),
    path("<str:serial>/disconnect", disconnect_device, name="disconnect"),
    path("<str:serial>/disconnect-observe", disconnect_observe, name="disconnect-observe"),
    path("<str:serial>/activate", activate_device, name="activate"),
    # v2
    path("<str:serial>/lock", lock_device, name="lock"),
    path("<str:serial>/release", release_device, name="release"),
    path("<str:serial>/queue", join_device_queue, name="queue-join"),
    path("<str:serial>/queue/leave", leave_device_queue, name="queue-leave"),
]
