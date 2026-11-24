"""
文件名: ➡️ ui_executor.py 🏁
路径: ➡️ engines/backend_bridge/agents/ui_executor.py 🏁
模块功能：➡️ 平台侧 UI 执行角色：调 ae_harness 原语装配智能体并挂设备工具 🏁
Python 调试：➡️ python -m engines.backend_bridge.agents.ui_executor 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. PlatformRole: 平台角色的运行名。连接参数与提示词由调用方传入。
2. build_ui_executor: 调 ae_harness.create_agent 建角色、挂全量设备工具，返回 bundle 与观测中间件。
3. 只装配不运行：不跑任务、不打印、不落盘。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: 导入 create_agent，唯一的角色创建出口。
2. engines.ae_harness.middleware: 导入 ObservationMiddleware，平台运行默认挂观测。
3. engines.ae_harness.tools: 导入 build_adb_tools，给执行角色挂全量设备工具。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_tools

__all__ = ["PlatformRole", "UI_EXECUTOR_ROLE", "build_ui_executor"]


@dataclass(frozen=True)
class PlatformRole:
    """
    平台角色的三要素。

    Attributes:
        role_key: 智能体名称，同时写进报告与事件归属。
    """

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
) -> tuple[AgentBundle, ObservationMiddleware]:
    """
    装配平台侧 UI 执行角色。

    只装配不运行：返回的智能体已带全量设备工具，可直接交给运行入口。

    Args:
        system_prompt: 系统提示词正文，由平台运营配置传入。
        provider: 厂商名，由平台运营配置传入。
        api_key_env: 密钥环境变量名，由平台运营配置传入。
        model_name: 正式模型名，由平台运营配置传入。
        base_url: 基础地址；空串时用厂商默认。
        observer: 观测中间件；不传则新建一个。
        controls: 额外的中间件（重试 / 预算 / 取消）；不传则只挂观测。

    Returns:
        (角色 bundle, 观测中间件)；观测中间件已挂到智能体上。

    Raises:
        ValueError: 厂商与密钥名不匹配，密钥没配，或系统提示词为空。
    """
    watcher = observer if observer is not None else ObservationMiddleware()
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
    for tool in build_adb_tools():
        await bundle.agent.toolkit.add_tool(tool)
    return bundle, watcher
