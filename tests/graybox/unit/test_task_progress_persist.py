"""任务进度落库：必须能在 asyncio 事件循环内被工作流回调调用。"""

from __future__ import annotations

import asyncio
import json

import pytest
from django.core.exceptions import SynchronousOnlyOperation

from apps.ai_assistant.models import AIAgent, AITask
from apps.ai_assistant.views_drf import persist_task_progress_safe


@pytest.fixture
def running_task(db):
    agent = AIAgent.objects.create(name="progress-test-agent")
    return AITask.objects.create(
        agent=agent,
        title="进度测试",
        goal="启动 APP",
        status="running",
    )


@pytest.mark.unit
@pytest.mark.django_db(transaction=True)
def test_direct_orm_from_async_context_is_blocked(running_task):
    """对照：事件循环内直接 ORM 会被 Django 拦截（即线上空详情根因）。"""

    async def boom():
        AITask.objects.get(id=running_task.id)

    with pytest.raises(SynchronousOnlyOperation):
        asyncio.run(boom())


@pytest.mark.unit
@pytest.mark.django_db(transaction=True)
def test_persist_task_progress_safe_from_async_context(running_task):
    """工作流回调路径：async 上下文内落库成功，详情可读到 plans。"""
    payload = {
        "status": "running",
        "summary": "已规划 1 个目标",
        "plans": [{"goal": "启动", "steps": ["打开"], "verification": "在前台"}],
        "log": [],
        "usage": {"input_tokens": 1, "output_tokens": 2, "cache_input_tokens": 0, "models": {}},
        "models": {"planner": "m", "executor": "m", "verifier": "m", "max_loops": 3},
        "max_loops": 3,
    }

    async def call():
        persist_task_progress_safe(running_task.id, payload)

    asyncio.run(call())
    running_task.refresh_from_db()
    data = json.loads(running_task.result)
    assert data["summary"] == "已规划 1 个目标"
    assert data["plans"][0]["goal"] == "启动"
    assert running_task.input_tokens == 1
