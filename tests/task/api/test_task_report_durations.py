"""任务报告：步骤耗时拆成模型 / 工具 / 空档三项。"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.models import Task, TaskEvent
from backend.apps.task_list.task_reports import build_task_flow

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _task(owner) -> Task:
    """建一条已完成的任务，供报告聚合使用。"""
    agent = AIAgent.objects.create(name="耗时助手", owner=owner)
    return Task.objects.create(
        agent=agent,
        title="耗时任务",
        case_title="卡片页",
        status="completed",
        device_label="测试机",
    )


def _event(
    task,
    seq,
    event_type,
    *,
    started_at=None,
    ended_at=None,
    duration_ms=0,
    payload=None,
    step_seq=1,
    attempt=1,
):
    """写一条带时间的事件。"""
    return TaskEvent.objects.create(
        task=task,
        seq=seq,
        event_type=event_type,
        phase="执行",
        block_type="reply",
        is_delta=False,
        role_name="executor_role",
        step_seq=step_seq,
        attempt=attempt,
        payload=payload or {},
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
    )


def _step_payload(owner, task) -> dict:
    """取报告里第一条用例的第一个步骤。"""
    flow = build_task_flow(str(owner.id), str(task.id))
    assert flow is not None
    assert flow["cases"], flow
    return flow["cases"][0]["steps"][0]


def test_step_splits_duration_into_model_tool_idle():
    """步骤墙钟 4s、模型 1s、工具 0.5s 时，空档为 2.5s。"""
    owner = get_user_model().objects.create_user(username="dur-owner", password="pass")
    task = _task(owner)
    start = datetime(2026, 11, 4, 12, 0, 0)
    _event(task, 1, "ReplyStartEvent", started_at=start)
    _event(task, 2, "ModelCallEndEvent", started_at=start, ended_at=start + timedelta(seconds=1),
           duration_ms=1000)
    _event(task, 3, "ToolResultEndEvent",
           started_at=start + timedelta(seconds=1),
           ended_at=start + timedelta(seconds=1, milliseconds=500),
           duration_ms=500)
    _event(task, 4, "ReplyEndEvent", started_at=start, ended_at=start + timedelta(seconds=4),
           duration_ms=4000)

    step = _step_payload(owner, task)

    assert step["duration_ms"] == 4000
    assert step["model_ms"] == 1000
    assert step["tool_ms"] == 500
    assert step["idle_ms"] == 2500


def test_idle_is_never_negative():
    """模型与工具之和超过墙钟时，空档截断为 0。"""
    owner = get_user_model().objects.create_user(username="dur-owner-2", password="pass")
    task = _task(owner)
    start = datetime(2026, 11, 4, 12, 5, 0)
    _event(task, 1, "ReplyStartEvent", started_at=start)
    _event(task, 2, "ModelCallEndEvent", started_at=start, ended_at=start + timedelta(seconds=3),
           duration_ms=3000)
    _event(task, 3, "ToolResultEndEvent", started_at=start, ended_at=start + timedelta(seconds=3),
           duration_ms=3000)
    _event(task, 4, "ReplyEndEvent", started_at=start, ended_at=start + timedelta(seconds=2),
           duration_ms=2000)

    step = _step_payload(owner, task)

    assert step["idle_ms"] == 0
    assert step["tool_ms"] == 3000


def test_legacy_task_without_tool_events_reports_zero_tool():
    """存量任务只有模型事件时，工具与空档为 0，墙钟照常下发。"""
    owner = get_user_model().objects.create_user(username="dur-owner-3", password="pass")
    task = _task(owner)
    start = datetime(2026, 11, 4, 12, 10, 0)
    _event(task, 1, "ReplyStartEvent", started_at=start)
    _event(task, 2, "ModelCallEndEvent", started_at=start, ended_at=start + timedelta(seconds=2),
           duration_ms=2000)
    _event(task, 3, "ReplyEndEvent", started_at=start, ended_at=start + timedelta(seconds=2),
           duration_ms=2000)

    step = _step_payload(owner, task)

    assert step["duration_ms"] == 2000
    assert step["model_ms"] == 2000
    assert step["tool_ms"] == 0
    assert step["idle_ms"] == 0
