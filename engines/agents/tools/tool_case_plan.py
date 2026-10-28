"""
python -m 调试路径: engines.agents.tools.tool_case_plan

本模块的业务功能如下：
1. build_case_plan_tools: 构造 AgentScope 计划模式内置工具（建/查/列/改）。
"""

from __future__ import annotations

from agentscope.tool import TaskCreate, TaskGet, TaskList, TaskUpdate

__all__ = ["build_case_plan_tools"]


def build_case_plan_tools() -> list:
    """构造计划模式四件套，供写用例角色挂到 Toolkit。

    Returns:
        ``TaskCreate`` / ``TaskGet`` / ``TaskList`` / ``TaskUpdate`` 的新实例。
    """
    return [TaskCreate(), TaskGet(), TaskList(), TaskUpdate()]
