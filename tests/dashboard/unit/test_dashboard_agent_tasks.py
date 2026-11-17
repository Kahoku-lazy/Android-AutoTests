"""仪表盘助手任务卡聚合：分日柱 / 摘要 / 最近列表。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.dashboard.ai_usage import (
    ai_recent_tasks,
    ai_task_daily_execution,
    ai_task_execution_summary,
)
from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind


@pytest.fixture
def visible_user(db):
    return get_user_model().objects.create_user(
        username="dash-agent-admin",
        password="x",
        is_superuser=True,
    )


@pytest.mark.unit
@pytest.mark.django_db
def test_daily_execution_counts_success_and_failed_on_create_day(visible_user):
    user = visible_user
    Task.objects.create(title="ok-1", status="success", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="ok-2", status="completed", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="fail-1", status="failed", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="wait", status="pending", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="retired", status="success", task_kind=TaskKind.DEVICE_CONTROL)

    series = ai_task_daily_execution(str(user.id), days=12)
    assert series["success"][-1] == 2
    assert series["failed"][-1] == 1
    assert len(series["labels"]) == 12

    summary = ai_task_execution_summary(str(user.id))
    assert summary["passed"] == 2
    assert summary["failed"] == 1


@pytest.mark.unit
@pytest.mark.django_db
def test_recent_tasks_maps_completed_to_success(visible_user):
    user = visible_user
    task = Task.objects.create(
        title="已完成", goal="目标", status="completed", task_kind=TaskKind.ASSISTANT_SOP
    )

    rows = ai_recent_tasks(str(user.id), limit=8)
    assert len(rows) == 1
    assert rows[0]["id"] == task.id
    assert rows[0]["title"] == "已完成"
    assert rows[0]["case_label"] == ""
    assert rows[0]["status"] == "success"
    assert rows[0]["time"]


@pytest.mark.unit
@pytest.mark.django_db
def test_recent_tasks_keep_interrupted_and_cancelled(visible_user):
    Task.objects.create(title="中断", status="interrupted", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="取消", status="cancelled", task_kind=TaskKind.ASSISTANT_SOP)

    rows = {row["title"]: row["status"] for row in ai_recent_tasks(str(visible_user.id))}
    assert rows == {"中断": "interrupted", "取消": "cancelled"}
