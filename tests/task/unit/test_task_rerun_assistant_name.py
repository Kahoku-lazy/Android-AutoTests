"""失败任务克隆重跑：复制用例身份，不回读用例库，也不依赖已下线的智能体。"""

from __future__ import annotations

import pytest

from backend.apps.task_list import api
from backend.models.constants import TaskStatus

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]


def test_rerun_task_clones_without_mutating_original():
    original = api.create_task(
        title="点击音乐",
        goal="进入音乐模式",
        attachment="# md",
        attachment_filename="a.pdf",
        device_serial="SER1",
        device_label="SM-S9010",
        case_identity={"source": "platform", "rows": [{"project": "灯", "id": "1", "title": "定时"}]},
        created_by="42",
    )
    api.finalize_task(original, status=TaskStatus.FAILED, result="执行异常: 402")
    original.refresh_from_db()
    assert original.status == TaskStatus.FAILED

    cloned = api.rerun_task(original)

    original.refresh_from_db()
    assert original.status == TaskStatus.FAILED
    assert "执行异常: 402" in original.result
    assert cloned.id != original.id
    assert cloned.status == TaskStatus.PENDING
    assert cloned.title == original.title
    assert cloned.goal == original.goal
    assert cloned.attachment == original.attachment
    assert cloned.attachment_filename == original.attachment_filename
    assert cloned.device_serial == original.device_serial
    assert cloned.device_label == original.device_label
    assert cloned.created_by == "42"
    assert cloned.case_identity == original.case_identity


def test_list_row_uses_workflow_name_not_retired_agent(monkeypatch):
    task = api.create_task(title="t", goal="g", device_serial="S")
    task.result = '{"workflow_id": 7}'
    task.save(update_fields=["result"])
    monkeypatch.setattr(
        "backend.apps.ai_assistant.api.get_sop_workflow",
        lambda workflow_id: type("Workflow", (), {"id": workflow_id, "name": "新工作流"})(),
    )

    row = api.serialize_agent_task_row(task)

    assert row["workflow_name"] == "新工作流"
    assert row["title"] == "t"
