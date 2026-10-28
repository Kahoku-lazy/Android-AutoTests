"""计划模式工具：装配四件套，并验证它们读写同一份 AgentState。"""

from __future__ import annotations

import pytest

from agentscope.state import AgentState
from agentscope.tool import TaskCreate, TaskGet, TaskList, TaskUpdate

from engines.agents.tools.tool_case_plan import build_case_plan_tools
from engines.agents.tools_config import build_case_writer_toolkit

pytestmark = [pytest.mark.unit]


def test_build_case_plan_tools_returns_four_tools():
    tools = build_case_plan_tools()

    assert [tool.name for tool in tools] == ["TaskCreate", "TaskGet", "TaskList", "TaskUpdate"]
    assert all(isinstance(tool, (TaskCreate, TaskGet, TaskList, TaskUpdate)) for tool in tools)


def test_writer_toolkit_has_only_plan_tools():
    toolkit = build_case_writer_toolkit()

    assert [group.name for group in toolkit.tool_groups] == ["basic"]
    assert {tool.name for tool in toolkit.tool_groups[0].tools} == {
        "TaskCreate",
        "TaskGet",
        "TaskList",
        "TaskUpdate",
    }


@pytest.mark.asyncio
async def test_plan_tools_share_agent_state():
    state = AgentState()
    tools = {tool.name: tool for tool in build_case_plan_tools()}

    await tools["TaskCreate"].call(
        _agent_state=state,
        subject="拆需求原子",
        description="把模块需求拆成 REQ 原子",
    )
    await tools["TaskUpdate"].call(_agent_state=state, task_id="1", status="in_progress")
    listed = await tools["TaskList"].call(_agent_state=state)
    fetched = await tools["TaskGet"].call(_agent_state=state, task_id="1")

    assert "1 [in_progress] 拆需求原子" in listed.content[0].text
    assert "拆需求原子" in fetched.content[0].text
    assert state.tasks_context.tasks[0].state == "in_progress"
