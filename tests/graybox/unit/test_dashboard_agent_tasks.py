"""仪表盘助手任务卡聚合：分日柱 / 摘要 / 最近列表。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant.models import AIAgent, AITask
from apps.dashboard.ai_usage import (
    ai_recent_tasks,
    ai_task_daily_execution,
    ai_task_execution_summary,
)


@pytest.fixture
def visible_agent(db):
    user = get_user_model().objects.create_user(
        username="dash-agent-admin",
        password="x",
        is_superuser=True,
    )
    agent = AIAgent.objects.create(name="dash-agent", owner=user)
    return user, agent


@pytest.mark.unit
@pytest.mark.django_db
def test_daily_execution_counts_success_and_failed_on_create_day(visible_agent):
    user, agent = visible_agent
    AITask.objects.create(agent=agent, title="ok-1", status="success")
    AITask.objects.create(agent=agent, title="ok-2", status="completed")
    AITask.objects.create(agent=agent, title="fail-1", status="failed")
    AITask.objects.create(agent=agent, title="wait", status="pending")

    series = ai_task_daily_execution(str(user.id), days=12)
    assert series["success"][-1] == 2
    assert series["failed"][-1] == 1
    assert len(series["labels"]) == 12

    summary = ai_task_execution_summary(str(user.id))
    assert summary["passed"] == 2
    assert summary["failed"] == 1


@pytest.mark.unit
@pytest.mark.django_db
def test_recent_tasks_maps_completed_to_success(visible_agent):
    user, agent = visible_agent
    task = AITask.objects.create(agent=agent, title="已完成", goal="目标", status="completed")

    rows = ai_recent_tasks(str(user.id), limit=8)
    assert len(rows) == 1
    assert rows[0]["id"] == task.id
    assert rows[0]["title"] == "已完成"
    assert rows[0]["status"] == "success"
    assert rows[0]["time"]
