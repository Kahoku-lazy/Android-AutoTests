"""device-inspector URL routing — /api/inspector/*（v1.7 快照化 6 端点）."""

from django.urls import path

from .views import (
    capture,
    page_view,
    save_elements,
    snapshot_delete,
    snapshot_detail,
    snapshots,
)

app_name = "inspector"

urlpatterns = [
    path("capture", capture, name="capture"),
    path("snapshots", snapshots, name="snapshots"),
    path("snapshots/<int:snapshot_id>", snapshot_detail, name="snapshot_detail"),
    path("snapshots/<int:snapshot_id>/delete", snapshot_delete, name="snapshot_delete"),
    path("snapshots/<int:snapshot_id>/save-elements", save_elements, name="save_elements"),
    path("pages/<int:page_id>", page_view, name="page_view"),
]
