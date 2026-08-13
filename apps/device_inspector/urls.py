"""device-inspector URL routing — /api/inspector/*."""

from django.urls import path

from .views import (
    device_info_view,
    do_action,
    dump_page,
    screenshot_snapshot,
)

app_name = "inspector"

urlpatterns = [
    path("dump", dump_page, name="dump"),
    path("action", do_action, name="action"),
    path("device-info", device_info_view, name="device_info"),
    path("screenshot", screenshot_snapshot, name="screenshot"),
]
