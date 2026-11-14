"""
文件名: ➡️ roles.py 🏁
路径: ➡️ engines/backend_bridge/workflow/roles.py 🏁
模块功能：➡️ 为平台 SOP 装配执行者与验收者两个角色 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.roles 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. SopRoles: 一次运行用到的两个角色 bundle 与共用的观测中间件。
2. build_sop_roles: 执行者挂全量设备工具，验收者只挂只读工具；两者共用同一个观测中间件。
3. 只装配不运行：不跑任务、不打印、不落盘。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: 导入 create_agent，唯一的角色创建出口。
2. engines.ae_harness.tools: 导入全量工具与只读工具集。
3. engines.ae_harness.middleware: 导入 ObservationMiddleware，两角色共用一个实例。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_sop_roles.py: 验收者只读、共用观察者、密钥名可读
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_readonly_tools, build_adb_tools

__all__ = ["SopRoles", "build_sop_roles"]

# 两个角色复用的提示词与默认模型：与控制台同一套，不另维护副本。
EXECUTOR_PROMPT = "UI_EXECUTOR_PROMPT"
VERIFIER_PROMPT = "UI_VERIFIER_PROMPT"
DEFAULT_MODEL_SHORT = "govee_chat_flash"


@dataclass(frozen=True)
class SopRoles:
    """
    一次 SOP 运行用到的两个角色。

    Attributes:
        executor: 执行者：挂全量设备工具，负责动手。
        verifier: 验收者：只挂只读工具，负责核对「必须达成的结果」。
        observer: 两个角色共用的观测中间件；记录里带角色名，仍能分清是谁的。
    """

    executor: AgentBundle
    verifier: AgentBundle
    observer: ObservationMiddleware


async def build_sop_roles(
    *,
    model_short: str | None = None,
    observer: ObservationMiddleware | None = None,
    controls: list | None = None,
) -> SopRoles:
    """
    装配执行者与验收者。

    只装配不运行：返回的两个智能体已挂好对应工具集。

    Args:
        model_short: 模型短名；不传则用默认值。两个角色共用同一个模型。
        observer: 观测中间件；不传则新建一个。
        controls: 额外的中间件（重试 / 预算 / 取消）；不传则只挂观测。两个角色共用同一批。

    Returns:
        含两个角色 bundle 与共用观测中间件的 `SopRoles`。

    Raises:
        ValueError: 模型短名不存在或密钥没配。
        FileNotFoundError: 提示词文件不存在。
    """
    watcher = observer if observer is not None else ObservationMiddleware()
    short = model_short or DEFAULT_MODEL_SHORT

    extra = list(controls or [])
    executor = create_agent("ui_executor", EXECUTOR_PROMPT, short, observers=[watcher, *extra])
    for tool in build_adb_tools():
        await executor.agent.toolkit.add_tool(tool)

    verifier = create_agent("ui_verifier", VERIFIER_PROMPT, short, observers=[watcher, *extra])
    for tool in build_adb_readonly_tools():
        await verifier.agent.toolkit.add_tool(tool)

    return SopRoles(executor=executor, verifier=verifier, observer=watcher)
