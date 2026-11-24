"""团队流水线抽象：成员透传、队长回复取最后一条、构造错误原样抛出。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import engines.ae_harness.workflow.team as team_module

from engines.ae_harness.workflow.team import TeamRole, run_team

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _Event:
    """替身事件：带一段队长回复。"""

    def __init__(self, text):
        self._text = text

    def get_text_content(self):
        return self._text


class _Member:
    """替身成员：只记下智能体与说明，不做类型校验。"""

    def __init__(self, agent, description):
        self.agent = agent
        self.description = description


class _FakeTeam:
    """替身流水线：记下成员并产出两段回复。"""

    built: dict = {}

    def __init__(self, leader, members, **kwargs):
        _FakeTeam.built = {"leader": leader, "members": members, **kwargs}

    async def reply_stream(self, _message):
        yield _Event("先分派")
        yield _Event("拆成两个模块")


async def test_run_team_returns_leader_reply(monkeypatch, tmp_path):
    """队长的最终回复取事件流里的最后一段正文。"""
    monkeypatch.setattr(team_module, "TeamPipeline", _FakeTeam)
    monkeypatch.setattr(team_module, "TeamMember", _Member)
    leader = SimpleNamespace(name="lead")
    member = TeamRole(agent=SimpleNamespace(name="writer"), description="写边界")

    result = await run_team(leader, [member], "拆解需求", log_dir=tmp_path)

    assert result.reply == "拆成两个模块"
    assert _FakeTeam.built["leader"] is leader
    assert _FakeTeam.built["members"][0].description == "写边界"
    assert result.record is not None
    assert result.record.html_path.exists()


async def test_run_team_propagates_duplicate_name(monkeypatch, tmp_path):
    """成员重名时构造抛出的错误原样传出。"""

    class _Reject:
        def __init__(self, leader, members, **kwargs):
            raise ValueError("成员重名")

    monkeypatch.setattr(team_module, "TeamPipeline", _Reject)
    with pytest.raises(ValueError, match="成员重名"):
        await run_team(SimpleNamespace(name="lead"), [], "拆解需求", log_dir=tmp_path)
