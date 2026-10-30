"""
文件名: ➡️ tool_case_plan.py 🏁
路径: ➡️ engines/agents/tools/tool_case_plan.py 🏁
模块功能：➡️ 构造计划模式四件套，供写用例角色挂到 Toolkit 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_case_plan 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. build_case_plan_tools: 构造 AgentScope 计划模式内置工具（建/查/列/改）。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_case_plan_tools.py: 计划模式工具：装配四件套，并验证它们读写同一份 AgentState
🏁
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
