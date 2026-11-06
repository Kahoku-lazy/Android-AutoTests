"""任务报告：被引擎打断的步骤要带上原因，供前端标「日志中断」。"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.models import Task, TaskEvent
from backend.apps.task_list.task_reports import build_task_flow
from engines.agents.tools.tool_serial import LOG_EMPTY

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _task(owner) -> Task:
    """建一条失败任务。"""
    agent = AIAgent.objects.create(name="中断助手", owner=owner)
    return Task.objects.create(
        agent=agent,
        title="中断任务",
        case_title="卡片页",
        status="failed",
        device_label="测试机",
    )


def _event(task, seq, event_type, *, step_seq=1, payload=None, started_at=None):
    """写一条事件。"""
    return TaskEvent.objects.create(
        task=task,
        seq=seq,
        event_type=event_type,
        phase="结束",
        block_type="interrupt" if event_type == "StepInterruptedEvent" else "reply",
        is_delta=False,
        role_name="ui_verifier_role",
        step_seq=step_seq,
        attempt=1,
        payload=payload or {},
        started_at=started_at,
        ended_at=started_at,
        duration_ms=0,
    )


def test_interrupted_step_carries_reason():
    """打断事件落在第 2 步时，报告的该步带 interrupt 原因与中断类别。"""
    owner = get_user_model().objects.create_user(username="int-owner", password="pass")
    task = _task(owner)
    start = datetime(2026, 11, 4, 17, 57, 0)
    _event(task, 1, "ReplyStartEvent", step_seq=1, started_at=start)
    _event(task, 2, "ReplyStartEvent", step_seq=2, started_at=start + timedelta(seconds=20))
    _event(
        task,
        3,
        "StepInterruptedEvent",
        step_seq=2,
        payload={
            "reason": LOG_EMPTY,
            "exc_type": "exception",
            "kind": "log",
            "tool": "check_device_log",
        },
        started_at=start + timedelta(seconds=30),
    )

    flow = build_task_flow(str(owner.id), str(task.id))

    steps = flow["cases"][0]["steps"]
    assert steps[0]["interrupt"] == ""
    assert steps[0]["interrupt_kind"] == ""
    assert steps[1]["interrupt"] == LOG_EMPTY
    assert steps[1]["interrupt_kind"] == "log"
    assert steps[1]["interrupt_tool"] == "check_device_log"
    # 中断即未通过：计入失败统计
    assert steps[1]["outcome"] == "FAIL"
    assert flow["cases"][0]["outcome"] == "FAIL"


def test_exception_interrupt_is_labelled_separately():
    """执行层异常与证据不可用分开标注，原因里带异常类型。"""
    owner = get_user_model().objects.create_user(username="int-owner-3", password="pass")
    task = _task(owner)
    start = datetime(2026, 11, 6, 11, 17, 0)
    _event(task, 1, "ReplyStartEvent", step_seq=1, started_at=start)
    _event(
        task,
        2,
        "StepInterruptedEvent",
        step_seq=1,
        payload={
            "reason": "ExceptionGroup: One or more tool calls raised an exception (2 sub-exceptions)",
            "kind": "exception",
        },
        started_at=start + timedelta(seconds=30),
    )

    flow = build_task_flow(str(owner.id), str(task.id))

    step = flow["cases"][0]["steps"][0]
    assert step["interrupt_kind"] == "exception"
    assert step["interrupt_tool"] == ""
    assert "ExceptionGroup" in step["interrupt"]
    assert step["outcome"] == "FAIL"


def test_task_without_interrupt_has_empty_field():
    """没有打断事件时该字段为空串，前端据此不渲染标记。"""
    owner = get_user_model().objects.create_user(username="int-owner-2", password="pass")
    task = _task(owner)
    start = datetime(2026, 11, 4, 18, 0, 0)
    _event(task, 1, "ReplyStartEvent", step_seq=1, started_at=start)

    flow = build_task_flow(str(owner.id), str(task.id))

    assert flow["cases"][0]["steps"][0]["interrupt"] == ""
