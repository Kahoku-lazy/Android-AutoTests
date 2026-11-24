"""名片绑定的团队流水线：队长与成员各装配一次，说明随成员传入。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import engines.backend_bridge.workflow.bound_team as bound_team

from engines.ae_harness.workflow.team import TeamResult
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


async def test_bound_team_builds_each_role_once(monkeypatch):
    """队长与每个成员只装配一次，成员说明原样传入。"""
    built: list[str] = []

    async def fake_build(binding, **kwargs):
        built.append(binding.run_name)
        return SimpleNamespace(
            agent=binding.run_name, api_key_env="DEEPSEEK_API_KEY"
        ), SimpleNamespace(records=[])

    async def fake_run(leader, members, task, **kwargs):
        return TeamResult(reply=f"{leader}:{','.join(item.description for item in members)}:{task}")

    monkeypatch.setattr(bound_team, "build_bound_agent", fake_build)
    monkeypatch.setattr(bound_team, "run_team", fake_run)
    monkeypatch.setattr(bound_team, "cancel_controls", lambda task_id: [])

    result = await bound_team.run_bound_team(
        "拆解需求",
        _binding("队长"),
        [(_binding("成员甲"), "写边界"), (_binding("成员乙"), "写测试点")],
    )

    assert built == ["队长", "成员甲", "成员乙"]
    assert result.reply == "队长:写边界,写测试点:拆解需求"
