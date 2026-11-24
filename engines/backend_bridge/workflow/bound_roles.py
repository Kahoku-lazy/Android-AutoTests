from __future__ import annotations

from dataclasses import dataclass

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_readonly_tools
from engines.backend_bridge.agents.tool_selection import select_tools
from engines.backend_bridge.workflow.roles import SopRoles

__all__ = ["RoleBinding", "build_bound_roles"]


@dataclass(frozen=True)
class RoleBinding:
    run_name: str
    system_prompt: str
    provider: str
    api_key_env: str
    model_name: str
    base_url: str = ""
    tools: tuple[dict, ...] = ()


def _readonly_intersection(selections: tuple[dict, ...] | list[dict]) -> list:
    selected = select_tools(list(selections))
    readonly = {tool.name for tool in build_adb_readonly_tools()}
    return [tool for tool in selected if tool.name in readonly]


async def _mount(bundle: AgentBundle, tools: list) -> AgentBundle:
    for tool in tools:
        await bundle.agent.toolkit.add_tool(tool)
    return bundle


async def build_bound_agent(
    binding: RoleBinding,
    *,
    observer: ObservationMiddleware | None = None,
    controls: list | None = None,
    kind: str = "ui_automation",
    readonly: bool = False,
) -> tuple[AgentBundle, ObservationMiddleware]:
    watcher = observer if observer is not None else ObservationMiddleware()
    bundle = create_agent(
        binding.run_name,
        system_prompt=binding.system_prompt,
        provider=binding.provider,
        api_key_env=binding.api_key_env,
        model_name=binding.model_name,
        base_url=binding.base_url,
        observers=[watcher, *list(controls or [])],
    )
    tools = (
        _readonly_intersection(binding.tools)
        if readonly
        else select_tools(list(binding.tools), kind=kind)
    )
    return await _mount(bundle, tools), watcher


async def build_bound_roles(
    executor: RoleBinding,
    verifier: RoleBinding,
    *,
    observer: ObservationMiddleware | None = None,
    controls: list | None = None,
    kind: str = "ui_automation",
) -> SopRoles:
    executor_bundle, watcher = await build_bound_agent(
        executor, observer=observer, controls=controls, kind=kind
    )
    verifier_bundle, _ = await build_bound_agent(
        verifier, observer=watcher, controls=controls, kind=kind, readonly=True
    )
    return SopRoles(executor=executor_bundle, verifier=verifier_bundle, observer=watcher)
