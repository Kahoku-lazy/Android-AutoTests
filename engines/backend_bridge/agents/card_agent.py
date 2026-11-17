"""
文件名: ➡️ card_agent.py 🏁
路径: ➡️ engines/backend_bridge/agents/card_agent.py 🏁
模块功能：➡️ 按名片参数装配一个可运行角色 🏁
Python 调试：➡️ python -m engines.backend_bridge.agents.card_agent 🏁
时间：➡️ 2026-11-16 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-16 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_card_agent: 用调用方传入的系统提示词创建角色，再挂过滤后的工具。
2. 不读库，不读本地提示词文件，不引用控制台入口。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: 导入 create_agent。
2. engines.backend_bridge.agents.tool_selection: 导入 select_tools。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_card_agent.py: 不引用控制台入口
🏁
"""

from __future__ import annotations

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.backend_bridge.agents.tool_selection import select_tools

__all__ = ["build_card_agent"]


async def build_card_agent(
    *,
    name: str,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    system_prompt: str = "",
    tools: list[dict] | None = None,
    observers: list | None = None,
) -> AgentBundle:
    """
    按名片参数装配角色。

    Args:
        name: 运行时角色名，来自运营配置名称。
        provider: 厂商名。
        api_key_env: 密钥环境变量名。
        model_name: 正式模型名。
        base_url: 基础地址。
        system_prompt: 运营配置的系统提示词正文，原样使用。
        tools: 工具勾选。
        observers: 额外中间件。

    Returns:
        已挂上勾选工具的 bundle。

    Raises:
        ValueError: 连接参数不合法，系统提示词为空，或工具勾选含未知名字。
    """
    bundle = create_agent(
        name,
        system_prompt,
        provider=provider,
        api_key_env=api_key_env,
        model_name=model_name,
        base_url=base_url,
        observers=list(observers or []),
    )
    for tool in select_tools(tools):
        await bundle.agent.toolkit.add_tool(tool)
    return bundle
