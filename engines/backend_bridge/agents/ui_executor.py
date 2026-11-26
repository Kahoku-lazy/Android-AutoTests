from __future__ import annotations

from dataclasses import dataclass

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_tools

__all__ = ["PlatformRole", "UI_EXECUTOR_ROLE", "build_ui_executor"]


@dataclass(frozen=True)
class PlatformRole:
    role_key: str


UI_EXECUTOR_ROLE = PlatformRole(role_key="ui_executor")


async def build_ui_executor(
    *,
    system_prompt: str,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    observer: ObservationMiddleware | None = None,
    controls: list | None = None,
    capture_messages: bool = False,
) -> tuple[AgentBundle, ObservationMiddleware]:
    watcher = (
        observer
        if observer is not None
        else ObservationMiddleware(capture_messages=capture_messages)
    )
    role = UI_EXECUTOR_ROLE
    bundle = create_agent(
        role.role_key,
        system_prompt=system_prompt,
        provider=provider,
        api_key_env=api_key_env,
        model_name=model_name,
        base_url=base_url,
        observers=[watcher, *(controls or [])],
    )
    for tool in build_adb_tools(include_devices=False):
        await bundle.agent.toolkit.add_tool(tool)
    return bundle, watcher
