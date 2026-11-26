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
    bundle = create_agent(
        name,
        system_prompt=system_prompt,
        provider=provider,
        api_key_env=api_key_env,
        model_name=model_name,
        base_url=base_url,
        observers=list(observers or []),
    )
    for tool in select_tools(tools):
        await bundle.agent.toolkit.add_tool(tool)
    return bundle
