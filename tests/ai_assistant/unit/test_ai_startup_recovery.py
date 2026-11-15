"""启动恢复：遗留 running 落“已中断”，回写费用，再拉起 pending。

背景：服务重启打断的任务曾被标记为 failed，导致基础设施问题伪装成用例失败、
测试报告通过率被污染。本组用例锁三件事：状态口径（interrupted 而非 failed）、
费用回写（先 rollup 再改状态）、排队任务仍可被拉起。
"""

from __future__ import annotations

import inspect

from decimal import Decimal

import pytest

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api as task_api
from backend.apps.task_list import apps as apps_module
from backend.apps.task_list.models import Task, TaskEvent
from backend.models.constants import TaskStatus

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_recover_orphaned_tasks_marks_running_interrupted():
    """遗留 running 变 interrupted；pending / completed 不动。"""
    agent = AIAgent.objects.create(name="recovery-agent")
    running = Task.objects.create(agent=agent, title="r", status=TaskStatus.RUNNING)
    pending = Task.objects.create(agent=agent, title="p", status=TaskStatus.PENDING)
    done = Task.objects.create(agent=agent, title="d", status=TaskStatus.COMPLETED)

    recovered = task_api.recover_orphaned_tasks()

    assert recovered == 1
    running.refresh_from_db()
    assert running.status == "interrupted"
    assert running.finished_at is not None
    assert "服务重启" in running.result
    assert Task.objects.get(id=pending.id).status == "pending"
    assert Task.objects.get(id=done.id).status == "completed"


def test_recover_orphaned_tasks_rolls_up_cost_before_interrupting():
    """中断前先用模型调用事件回写费用，避免中断任务费用为 0。"""
    agent = AIAgent.objects.create(name="recovery-agent")
    task = Task.objects.create(agent=agent, title="cost", status=TaskStatus.RUNNING)
    TaskEvent.objects.create(
        task=task,
        seq=1,
        event_type="ModelCallEndEvent",
        phase="",
        block_type="",
        cost_input=Decimal("0.10000000"),
        cost_cache=Decimal("0.20000000"),
        cost_output=Decimal("0.30000000"),
        cost_total=Decimal("0.60000000"),
    )

    task_api.recover_orphaned_tasks()

    task.refresh_from_db()
    assert task.status == "interrupted"
    assert task.cost_total == Decimal("0.60000000")


def test_recover_orphaned_tasks_is_exported_from_api():
    """写原语必须进 api 白名单（跨模块 / 装配层只能经 `__all__` 调用）。"""
    assert "recover_orphaned_tasks" in task_api.__all__
    assert callable(task_api.recover_orphaned_tasks)


def test_apps_config_has_no_direct_orm_write():
    """收敛断言：`apps.py` 源码不得再出现 ORM 写痕迹，且确实调用 api。"""
    src = inspect.getsource(apps_module)

    assert "objects.filter" not in src
    assert ".update(" not in src
    assert "recover_orphaned_tasks" in src
    assert "interrupted" in src
