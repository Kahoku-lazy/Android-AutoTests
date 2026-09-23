"""device-inspector URL routing — /api/inspector/*（v1.7 快照化端点 + 分层查询）."""

from django.urls import path

from .views import (
    capture,
    save_elements,
    snapshot_delete,
    snapshot_layers,
    snapshots,
    snapshots_clear,
)

app_name = "inspector"

urlpatterns = [
    path("capture/", capture, name="capture"),
    path("snapshots/", snapshots, name="snapshots"),
    path("snapshots/clear/", snapshots_clear, name="snapshots_clear"),
    path("snapshots/<int:snapshot_id>/layers/", snapshot_layers, name="snapshot_layers"),
    path("snapshots/<int:snapshot_id>/delete/", snapshot_delete, name="snapshot_delete"),
    path("snapshots/<int:snapshot_id>/save-elements/", save_elements, name="save_elements"),
]
