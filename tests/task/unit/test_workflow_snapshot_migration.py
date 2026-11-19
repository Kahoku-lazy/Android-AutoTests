"""旧工作流任务回填编排与种类，不把它们改成 Goal 或 Team。"""

from __future__ import annotations

import pytest

from django.apps import apps

from backend.apps.task_list import workflow_snapshot
from backend.apps.task_list.models import Task

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_workflow_snapshot_backfill_keeps_ui_pair(monkeypatch):
    workflow = Task.objects.create(
        title="旧工作流",
        task_kind="assistant_sop",
        result='{"workflow_id": 7, "status": "fail"}',
        status="failed",
    )
    device = Task.objects.create(title="设备任务", task_kind="device_control", status="failed")
    workflow.orchestration = ""
    workflow.kind = ""
    workflow.workflow_id = None
    workflow.save(update_fields=["orchestration", "kind", "workflow_id"])

    class _Historical:
        objects = Task.objects

        @staticmethod
        def get_model(app_label, model_name):
            assert (app_label, model_name) == ("task_list", "Task")
            return _Historical

    monkeypatch.setattr(apps, "get_model", _Historical.get_model, raising=False)
    workflow_snapshot.backfill(_Historical())

    workflow.refresh_from_db()
    device.refresh_from_db()
    assert workflow.workflow_id == 7
    assert workflow.orchestration == "sop"
    assert workflow.kind == "ui_automation"
    assert device.orchestration == ""
    assert device.kind == ""
