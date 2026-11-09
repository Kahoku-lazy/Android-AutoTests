"""
文件名: ➡️ case_roles.py 🏁
路径: ➡️ engines/agents/case_roles.py 🏁
模块功能：➡️ 用例编写/验收角色的成对装配：建好两个角色并挂上产物工具 🏁
Python 调试：➡️ python -m engines.agents.case_roles 🏁
时间：➡️ 2026-11-09 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-09 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_case_authoring_roles: 编写角色（可写产物）与验收角色（只读产物）一次装配好。
2. 只做装配、不做编排：流水线怎么跑、驳回几次由 workflow 决定。
3. 产物存储按对象传入，不 import workflow 的数据契约，保持依赖方向为 agents → workflow。
🏁
关联模块：➡️
1. engines.agents.agent_builders: 导入 build_case_writer / build_case_verifier，建两个角色
2. engines.agents.tools_config: 导入 build_case_artifact_tools，取产物增量工具
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_roles.py: 成对装配：两侧工具集与只读标记
2. tests/graybox/unit/test_workflow_boundary.py: workflow 不直接建角色的契约断言
🏁
"""

from __future__ import annotations

from agentscope.agent import Agent

from .agent_builders import build_case_verifier, build_case_writer
from .tools_config import build_case_artifact_tools

__all__ = ["build_case_authoring_roles"]


async def build_case_authoring_roles(
    store: object,
    *,
    requirement_text: str = "",
) -> tuple[Agent, Agent]:
    """装配用例编写的执行者与验收者：两个角色各自挂好产物工具。

    工具按角色分工：执行者可写产物（保存状态机、追加场景/用例），验收者只读。
    流水线只负责编排，角色与工具的绑定收在这里，避免 workflow 里既建角色又挂工具。

    Args:
        store: 本次任务共享的产物存储（`ArtifactStore` 实例）；按对象使用，不依赖其类型定义。
        requirement_text: 需求正文；验收角色用它开启事实预检，编写角色用不到。

    Returns:
        (编写角色, 验收角色) 两个已装配好的 Agent，工具集不共享。
    """
    writer = build_case_writer()
    verifier = build_case_verifier()
    await writer.toolkit.add_tool(build_case_artifact_tools(store))
    await verifier.toolkit.add_tool(
        build_case_artifact_tools(store, read_only=True, requirement_text=requirement_text)
    )
    return writer, verifier
