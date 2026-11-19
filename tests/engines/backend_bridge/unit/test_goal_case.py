"""用例编写目标循环：退回一次后通过才入库，不创建后续任务。"""

from __future__ import annotations

import pytest

from engines.backend_bridge.workflow.goal_case import run_goal_case

pytestmark = [pytest.mark.unit]


async def test_goal_retries_once_then_saves_without_followup():
    calls = []

    async def attempt(prompt: str) -> dict:
        calls.append(prompt)
        if len(calls) == 1:
            return {"passed": False, "reason": "缺少前置条件", "rows": []}
        return {"passed": True, "rows": [{"title": "开机"}]}

    saved = []
    result = await run_goal_case("模块：开关", attempt, saved.append, max_retries=1)

    assert len(calls) == 2
    assert "缺少前置条件" in calls[1]
    assert result["passed"] is True
    assert saved == [[{"title": "开机"}]]
    assert result["created_followup"] is False
