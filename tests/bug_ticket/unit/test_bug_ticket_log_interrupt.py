"""被设备日志打断的任务，要在 BUG 台账里单独开一张「设备日志中断」单。"""

from __future__ import annotations

from datetime import datetime

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.bug_manager.extract import build_bug_drafts
from backend.apps.task_list.models import Task, TaskEvent
from engines.agents.tools.tool_serial import LOG_EMPTY

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _task(owner) -> Task:
    """建一条失败任务。"""
    agent = AIAgent.objects.create(name="台账助手", owner=owner)
    return Task.objects.create(
        agent=agent,
        title="定时功能测试-04",
        case_title="H6810 定时功能测试",
        status="failed",
        device_label="测试机",
        result='{"status": "fail", "reason": "未完成", "completed": [], "failed": ["H6810 定时功能测试"]}',
    )


def _interrupt(task, reason: str = LOG_EMPTY, step: int = 2) -> None:
    """写一条打断事件。"""
    TaskEvent.objects.create(
        task=task,
        seq=1,
        event_type="StepInterruptedEvent",
        phase="结束",
        block_type="interrupt",
        is_delta=False,
        role_name="ui_verifier_role",
        step_seq=step,
        attempt=1,
        payload={"reason": reason, "exc_type": "DeveloperOrientedException"},
        started_at=datetime(2026, 11, 4, 17, 57, 30),
        ended_at=datetime(2026, 11, 4, 17, 57, 30),
        duration_ms=0,
    )


def test_interrupt_creates_extra_log_ticket():
    """打断事件存在时，除按用例失败的单子外，再开一张设备日志中断单。"""
    owner = get_user_model().objects.create_user(username="bug-int-owner", password="pass")
    task = _task(owner)
    _interrupt(task)

    drafts = build_bug_drafts(task)
    refs = {draft.source_ref: draft for draft in drafts}

    assert "task:log-interrupt" in refs
    ticket = refs["task:log-interrupt"]
    assert ticket.title.startswith("设备日志中断")
    assert "第 2 步" in ticket.detail
    assert "日志为空" in ticket.detail


def test_task_without_interrupt_has_no_log_ticket():
    """没有打断事件时不开这张单。"""
    owner = get_user_model().objects.create_user(username="bug-int-owner-2", password="pass")
    task = _task(owner)

    refs = {draft.source_ref for draft in build_bug_drafts(task)}

    assert "task:log-interrupt" not in refs
