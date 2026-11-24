"""名片绑定的目标流水线：两侧绑定原样交给装配，验收结论原样返回。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import engines.backend_bridge.workflow.bound_goal as bound_goal

from engines.ae_harness.workflow.goal import GoalResult
from engines.backend_bridge.workflow.bound_roles import RoleBinding

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _binding(name: str) -> RoleBinding:
    return RoleBinding(
        run_name=name,
        system_prompt=f"{name} 的提示词",
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
    )


async def test_bound_goal_uses_both_bindings(monkeypatch):
    """执行者与验收者都来自各自的绑定，任务正文原样传入。"""
    seen: dict = {}

    async def fake_build(executor, verifier, **kwargs):
        seen["executor"] = executor.run_name
        seen["verifier"] = verifier.run_name
        seen["kind"] = kwargs["kind"]
        return SimpleNamespace(
            executor=SimpleNamespace(agent="执行者", api_key_env="DEEPSEEK_API_KEY"),
            verifier=SimpleNamespace(agent="验收者"),
            observer=SimpleNamespace(records=[]),
        )

    async def fake_run(executor, verifier, task, **kwargs):
        seen["agents"] = (executor, verifier)
        seen["task"] = task
        return GoalResult(passed=True, verdict="pass", message="通过")

    monkeypatch.setattr(bound_goal, "build_bound_roles", fake_build)
    monkeypatch.setattr(bound_goal, "run_goal", fake_run)
    monkeypatch.setattr(bound_goal, "cancel_controls", lambda task_id: [])

    result = await bound_goal.run_bound_goal("编写用例", _binding("编写"), _binding("验收"))

    assert result.passed is True
    assert seen == {
        "executor": "编写",
        "verifier": "验收",
        "kind": "case_authoring",
        "agents": ("执行者", "验收者"),
        "task": "编写用例",
    }
