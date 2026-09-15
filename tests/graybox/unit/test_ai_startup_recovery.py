"""D3 写库收敛：启动恢复的写操作经 `api.recover_orphaned_tasks`，`apps.py` 不再直写 ORM。

背景：`AppConfig.ready` 起的后台线程原本自己 `AITask.objects.filter(...).update(...)`，
绕过 `api.py`（`apps/AGENTS.md` §1.2 / 本模块 `api.py` 文件头的写库归口铁律）。
本用例锁两件事：**行为等价**（只把 running 置 failed）与**不再直写**（静态断言）。
"""

from __future__ import annotations

import inspect

import pytest

from apps.ai_assistant import api as ai_api
from apps.ai_assistant import apps as apps_module
from apps.ai_assistant.models import AIAgent, AITask
from models.constants import TaskStatus

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_recover_orphaned_tasks_only_fails_running_tasks():
    """行为等价：只把 running 置 failed，其余状态不动；finished_at 与文案落库。"""
    agent = AIAgent.objects.create(name="recovery-agent")
    running = AITask.objects.create(agent=agent, title="r", status=TaskStatus.RUNNING)
    pending = AITask.objects.create(agent=agent, title="p", status=TaskStatus.PENDING)
    done = AITask.objects.create(agent=agent, title="d", status=TaskStatus.COMPLETED)

    recovered = ai_api.recover_orphaned_tasks()

    assert recovered == 1
    running.refresh_from_db()
    assert running.status == "failed"
    assert running.finished_at is not None
    assert "服务重启" in running.result
    assert AITask.objects.get(id=pending.id).status == "pending"
    assert AITask.objects.get(id=done.id).status == "completed"


def test_recover_orphaned_tasks_is_exported_from_api():
    """写原语必须进 api 白名单（跨模块 / 装配层只能经 `__all__` 调用）。"""
    assert "recover_orphaned_tasks" in ai_api.__all__
    assert callable(ai_api.recover_orphaned_tasks)


def test_apps_config_has_no_direct_orm_write():
    """收敛断言：`apps.py` 源码不得再出现 ORM 写痕迹，且确实调用 api。

    行为测试无法证明「写没有偷偷回到 apps.py」——即使再写一次等价直写，行为测试仍会通过。
    """
    src = inspect.getsource(apps_module)

    assert "objects.filter" not in src
    assert ".update(" not in src
    assert "recover_orphaned_tasks" in src
