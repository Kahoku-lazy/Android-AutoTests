"""目标流水线抽象：角色透传、验收结论取最后一次、记录落盘。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import engines.ae_harness.workflow.goal as goal_module

from engines.ae_harness.workflow.goal import run_goal

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _FakeGoal:
    """替身流水线：按预设结论逐条产出，记下构造参数。"""

    built: dict = {}

    def __init__(self, executor, verifier, **kwargs):
        self.executor = executor
        self.verifier = verifier
        _FakeGoal.built = {"executor": executor, "verifier": verifier, **kwargs}

    async def reply_stream(self, _message):
        yield SimpleNamespace(structured_output={"result": "fail", "message": "缺边界"})
        yield SimpleNamespace(structured_output={"result": "pass", "message": "通过"})


async def test_run_goal_keeps_last_verdict(monkeypatch, tmp_path):
    """退回后再通过时，结果取最后一次验收。"""
    monkeypatch.setattr(goal_module, "GoalPipeline", _FakeGoal)
    executor, verifier = SimpleNamespace(name="writer"), SimpleNamespace(name="reviewer")

    result = await run_goal(executor, verifier, "编写用例", max_iters=2, log_dir=tmp_path)

    assert result.passed is True
    assert result.verdict == "pass"
    assert result.message == "通过"
    assert _FakeGoal.built["executor"] is executor
    assert _FakeGoal.built["max_iters"] == 2
    assert result.record is not None
    assert result.record.html_path.exists()
