"""
文件名: ➡️ role_types.py 🏁
路径: ➡️ engines/agents/config/role_types.py 🏁
模块功能：➡️ Agent Harness 四分段配置类型（Role/Tools/Context/ReAct），供装载与装配单向依赖 🏁
Python 调试：➡️python -m engines.agents.config.role_types 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. RoleConfig: 角色配置（名称、系统提示词）
2. ToolsConfig: 工具配置（本角色 toolkit 占位；skills 延后）
3. ContextConfig: 上下文配置（role 侧参数）
4. ReActConfig: ReAct 配置（role 侧参数）
5. 本模块不依赖 agent_builders / models，用于拆掉 models↔builders 类型环
🏁
关联模块：➡️
1. agentscope.tool.Toolkit: ToolsConfig.toolkit 类型
🏁
测试：➡️
1. tests/engines/agents/test_agents.py: 经 Factory 消费四分段类型
2. tests/graybox/unit/test_case_authoring_roles.py: load_role_spec 装配用例角色
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.tool import Toolkit

__all__ = [
    "RoleConfig",
    "ToolsConfig",
    "ContextConfig",
    "ReActConfig",
]


@dataclass(frozen=True)
class RoleConfig:
    """
    角色配置：名称与系统提示词。

    Attributes:
        name: 角色名，用于 Agent 名与日志，如 executor_role、verifier_role。
        system_prompt: 本角色系统提示词正文。

    Raises:
        FrozenInstanceError: 角色配置不可变。
    """

    name: str
    system_prompt: str


@dataclass(frozen=True)
class ToolsConfig:
    """
    工具配置：本角色已装配的工具包（skills 产品字段本期不扩展）。

    Attributes:
        toolkit: 本角色已装配的工具包（每个角色一份，不共享）。

    Raises:
        FrozenInstanceError: 工具配置不可变。
    """

    toolkit: Toolkit


@dataclass(frozen=True)
class ContextConfig:
    """
    上下文配置（role 侧参数，由 AgentRoleFactory 映射到 agentscope.ContextConfig）。

    Attributes:
        trigger_ratio: 上下文压缩触发比例。
        reserve_ratio: 上下文压缩保留比例。
        tool_result_limit: 单条工具结果的长度上限。
        max_image_num: 上下文保留的图片数量上限。

    Raises:
        FrozenInstanceError: 上下文配置不可变。
    """

    trigger_ratio: float = 0.7
    reserve_ratio: float = 0.2
    tool_result_limit: int = 400000
    max_image_num: int = 5


@dataclass(frozen=True)
class ReActConfig:
    """
    ReAct 配置（role 侧参数，由 AgentRoleFactory 映射到 agentscope.ReActConfig）。

    Attributes:
        max_iters: ReAct 循环最大轮次。
        structured_output_grace_iters: 结构化输出的宽限轮次。
        stop_on_reject: 被驳回时是否停止。

    Raises:
        FrozenInstanceError: ReAct 配置不可变。
    """

    max_iters: int = 30
    structured_output_grace_iters: int = 5
    stop_on_reject: bool = True
