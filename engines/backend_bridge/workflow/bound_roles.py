"""
文件名: ➡️ bound_roles.py 🏁
路径: ➡️ engines/backend_bridge/workflow/bound_roles.py 🏁
模块功能：➡️ 按名片绑定参数装配一对 SOP 角色 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.bound_roles 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-17 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. RoleBinding: 一侧名片解析后的运行参数。
2. build_bound_roles: 用提示词正文和连接参数建一对角色，执行侧按勾选挂工具，验收侧只留只读交集。
3. 不读库，不读提示词文件，不传模型短名。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: 导入 create_agent，唯一的角色创建出口。
2. engines.ae_harness.tools: 导入只读工具集，用来取验收侧交集。
3. engines.backend_bridge.agents.tool_selection: 导入 select_tools，校验勾选。
4. engines.ae_harness.middleware: 导入 ObservationMiddleware，两角色共用一个实例。
🏁
测试：➡️
1. 暂无
🏁
"""

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
    """
    一侧名片解析后的运行参数。

    Attributes:
        run_name: 运行时角色名。两侧显示名相同时由调用方先消歧。
        system_prompt: 系统提示词正文。
        provider: 厂商名。
        api_key_env: 密钥环境变量名。
        model_name: 正式模型名。
        base_url: 基础地址。
        tools: 名片上的工具勾选，原样传入，本类不改写。
    """

    run_name: str
    system_prompt: str
    provider: str
    api_key_env: str
    model_name: str
    base_url: str = ""
    tools: tuple[dict, ...] = ()


def _readonly_intersection(selections: tuple[dict, ...] | list[dict]) -> list:
    """
    取勾选与只读目录的交集。

    Args:
        selections: 名片上的工具勾选，函数内不改写。

    Returns:
        只读工具列表；交集为空时返回空列表。

    Raises:
        ToolSelectionError: 勾选含目录不认识的名字。
    """
    selected = select_tools(list(selections))
    readonly = {tool.name for tool in build_adb_readonly_tools()}
    return [tool for tool in selected if tool.name in readonly]


async def _mount(bundle: AgentBundle, tools: list) -> AgentBundle:
    """
    把工具挂到已创建的角色上。

    Args:
        bundle: 工具包仍为空的角色。
        tools: 要挂的工具。

    Returns:
        同一份 bundle。
    """
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
    """
    按一份绑定装配一个角色。

    Args:
        binding: 这一侧的运行参数。
        observer: 观测中间件；不传则新建。
        controls: 额外中间件；不传则只挂观测。
        kind: 工作流类型，决定工具目录。
        readonly: 为真时只挂勾选与只读目录的交集。

    Returns:
        角色 bundle 与实际使用的观测中间件。

    Raises:
        ValueError: 连接参数不合法，或系统提示词为空。
        ToolSelectionError: 勾选含未知工具名。
    """
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
    """
    按绑定参数装配一对角色。

    两次创建都只传提示词正文和连接参数。执行侧走勾选校验；验收侧只挂勾选与只读目录的交集。

    Args:
        executor: 执行侧绑定。
        verifier: 验收侧绑定。
        observer: 观测中间件；不传则新建一个，两个角色共用。
        controls: 额外中间件；不传则只挂观测。两个角色共用同一批。
        kind: 工作流类型，决定执行侧工具目录；默认 UI 自动化。

    Returns:
        含两个角色 bundle 与共用观测中间件的 `SopRoles`。

    Raises:
        ValueError: 连接参数不合法，或系统提示词为空。
        ToolSelectionError: 任一侧勾选含未知工具名。
    """
    executor_bundle, watcher = await build_bound_agent(
        executor, observer=observer, controls=controls, kind=kind
    )
    verifier_bundle, _ = await build_bound_agent(
        verifier, observer=watcher, controls=controls, kind=kind, readonly=True
    )
    return SopRoles(executor=executor_bundle, verifier=verifier_bundle, observer=watcher)
