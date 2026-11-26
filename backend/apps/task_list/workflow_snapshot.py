from __future__ import annotations

import json


def backfill(apps) -> None:
    Task = apps.get_model("task_list", "Task")
    for task in Task.objects.filter(task_kind="assistant_sop").iterator():
        workflow_id = None
        try:
            payload = json.loads(task.result or "{}")
        except (TypeError, ValueError):
            payload = {}
        if isinstance(payload, dict):
            try:
                value = int(payload.get("workflow_id"))
            except (TypeError, ValueError):
                value = 0
            if value > 0:
                workflow_id = value
        task.workflow_id = workflow_id
        task.orchestration = "sop"
        task.kind = "ui_automation"
        task.save(update_fields=["workflow_id", "orchestration", "kind"])


def clear(apps) -> None:
    Task = apps.get_model("task_list", "Task")
    Task.objects.filter(task_kind="assistant_sop").update(
        workflow_id=None,
        orchestration="",
        kind="",
    )
