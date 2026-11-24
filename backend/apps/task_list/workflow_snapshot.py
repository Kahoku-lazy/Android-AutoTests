"""
模块功能：➡️ 旧工作流任务的编排与种类回填。迁移只调用这里，避免数字文件名不可导入 🏁
Python 调试：➡️ python -m backend.apps.task_list.workflow_snapshot 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 task_list 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import json


def backfill(apps) -> None:
    """把 assistant_sop 回填为 sop + ui_automation，并尽量取出工作流编号。"""
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
    """反向迁移只清空回填值，不改任务结果。"""
    Task = apps.get_model("task_list", "Task")
    Task.objects.filter(task_kind="assistant_sop").update(
        workflow_id=None,
        orchestration="",
        kind="",
    )
