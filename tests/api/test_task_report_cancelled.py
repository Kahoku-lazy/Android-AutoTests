"""任务报告：用户关闭的任务标为「主动关闭」，不与引擎驳回的「未完成」混用。"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.models import Task, TaskAttachment, TaskEvent
from backend.apps.task_list.task_reports import build_task_flow

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

CONFIG_YAML = """
- title: 定时功能
  steps:
    - action: 启动应用
      assert: 应用已启动
    - action: 设置定时
      assert: 定时已保存
""".strip()


def _task(owner, *, with_config: bool = False) -> Task:
    """建一条被用户关闭的任务；可选地挂一份两步用例配置。"""
    agent = AIAgent.objects.create(name=f"关闭助手-{owner.id}", owner=owner)
    task = Task.objects.create(
        agent=agent,
        title="关闭任务",
        case_title="定时功能" if with_config else "卡片页",
        status="cancelled",
        device_label="测试机",
    )
    if with_config:
        TaskAttachment.objects.create(
            task=task,
            kind=TaskAttachment.KIND_CONFIG,
            filename="cases.yaml",
            body=CONFIG_YAML,
        )
    return task


def _event(task, seq, event_type, *, step_seq=1, payload=None, started_at=None):
    """写一条事件。"""
    return TaskEvent.objects.create(
        task=task,
        seq=seq,
        event_type=event_type,
        phase="结束",
        block_type="reply",
        is_delta=False,
        role_name="ui_executor_role",
        step_seq=step_seq,
        attempt=1,
        payload=payload or {},
        started_at=started_at,
        ended_at=started_at,
        duration_ms=0,
    )


def test_cancelled_task_marks_reached_step_as_actively_closed():
    """已开始但没出判决的步骤标「主动关闭」，用例同理。"""
    owner = get_user_model().objects.create_user(username="cancel-owner", password="pass")
    task = _task(owner)
    _event(task, 1, "ReplyStartEvent", started_at=datetime(2026, 11, 6, 10, 40, 50))

    flow = build_task_flow(str(owner.id), str(task.id))

    case = flow["cases"][0]
    assert case["steps"][0]["outcome"] == "主动关闭"
    assert case["outcome"] == "主动关闭"


def test_cancelled_task_keeps_unstarted_step_as_unexecuted():
    """从未开始的步骤仍是「未执行」，不能因为整条任务被关闭就跟着改口。"""
    owner = get_user_model().objects.create_user(username="cancel-owner-2", password="pass")
    task = _task(owner, with_config=True)
    start = datetime(2026, 11, 6, 10, 40, 50)
    _event(task, 1, "ReplyStartEvent", started_at=start)
    _event(task, 2, "ReplyStartEvent", step_seq=1, started_at=start + timedelta(seconds=5))

    flow = build_task_flow(str(owner.id), str(task.id))

    steps = flow["cases"][0]["steps"]
    assert steps[0]["outcome"] == "主动关闭"
    assert steps[1]["outcome"] == "未执行"
    assert flow["cases"][0]["outcome"] == "主动关闭"


def test_cancelled_task_keeps_failed_step_as_fail():
    """已经判过 FAIL 的步骤仍是 FAIL：关闭不粉饰已出结论的失败。"""
    owner = get_user_model().objects.create_user(username="cancel-owner-3", password="pass")
    task = _task(owner, with_config=True)
    start = datetime(2026, 11, 6, 10, 40, 50)
    _event(
        task,
        1,
        "ToolCallEndEvent",
        step_seq=1,
        payload={
            "tool_name": "GenerateStructuredOutput",
            "args": {"passed": False, "message": "没达标"},
        },
        started_at=start,
    )

    flow = build_task_flow(str(owner.id), str(task.id))

    steps = flow["cases"][0]["steps"]
    assert steps[0]["outcome"] == "FAIL"
    assert flow["cases"][0]["outcome"] == "FAIL"
