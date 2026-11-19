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
        case_identity={
            "source": "platform",
            "rows": [{"project": "灯", "id": "1", "title": "定时"}],
        },
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
    assert cloned.result == ""
    assert cloned.workflow_id == original.workflow_id
    assert cloned.orchestration == original.orchestration
    assert cloned.kind == original.kind


def test_rerun_keeps_workflow_id_and_drops_previous_failure():
    original = api.create_task(
        title="Android-UI-SOP",
        goal="",
        device_serial="RF8N21MSW7A",
        task_kind="assistant_sop",
        created_by="42",
        workflow_id=1,
        orchestration="sop",
        kind="ui_automation",
    )
    original.result = api.dump_task_run_payload(
        {
            "workflow_id": 1,
            "status": "fail",
            "reason": "模型网关不可用",
            "report_path": "logs/old.html",
        }
    )
    original.status = TaskStatus.FAILED
    original.save(update_fields=["result", "status"])

    cloned = api.rerun_task(original)

    assert api.parse_task_result(cloned.result) == {"workflow_id": 1}
    original.refresh_from_db()
    assert "模型网关不可用" in original.result


def test_rerun_recovers_workflow_id_lost_by_an_earlier_clone():
    source = api.create_task(
        title="Android-UI-SOP",
        goal="",
        device_serial="RF8N21MSW7A",
        task_kind="assistant_sop",
        case_identity={"source": "platform", "rows": [{"id": "9"}]},
    )
    source.result = api.dump_task_run_payload({"workflow_id": 1, "status": "fail"})
    source.status = TaskStatus.FAILED
    source.save(update_fields=["result", "status"])
    lost = api.create_task(
        title=source.title,
        goal="",
        device_serial=source.device_serial,
        task_kind=source.task_kind,
        case_identity=source.case_identity,
    )
    lost.status = TaskStatus.FAILED
    lost.result = api.dump_task_run_payload({"status": "fail", "reason": "任务没有工作流编号"})
    lost.save(update_fields=["status", "result"])

    cloned = api.rerun_task(lost)

    assert api.parse_task_result(cloned.result) == {"workflow_id": 1}


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
