"""device-pool URL routing — 10 endpoints under /api/devices/."""

from django.urls import path

from .views import (
    activate_device,
    connect_device,
    device_current,
    disconnect_device,
    disconnect_observe,
    heartbeat,
    list_devices,
    lock_device,
    release_device,
    scan_device,
)

app_name = "devices"

urlpatterns = [
    path("", list_devices, name="list"),
    path("scan", scan_device, name="scan"),
    path("current", device_current, name="current"),
    path("heartbeat", heartbeat, name="heartbeat"),
    path("<str:serial>", connect_device, name="connect"),
    path("<str:serial>/disconnect", disconnect_device, name="disconnect"),
    path("<str:serial>/disconnect-observe", disconnect_observe, name="disconnect_observe"),
    path("<str:serial>/activate", activate_device, name="activate"),
    path("<str:serial>/lock", lock_device, name="lock"),
    path("<str:serial>/release", release_device, name="release"),
]
