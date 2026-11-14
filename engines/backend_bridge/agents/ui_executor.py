"""
文件名: ➡️ ui_executor.py 🏁
路径: ➡️ engines/backend_bridge/agents/ui_executor.py 🏁
模块功能：➡️ 平台侧 UI 执行角色：调 ae_harness 原语装配智能体并挂设备工具 🏁
Python 调试：➡️ python -m engines.backend_bridge.agents.ui_executor 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. PlatformRole: 平台角色的固定三要素——角色键、提示词文件名、默认模型短名。
2. build_ui_executor: 调 ae_harness.create_agent 建角色、挂全量设备工具，返回 bundle 与观测中间件。
3. 只装配不运行：不跑任务、不打印、不落盘。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: 导入 create_agent，唯一的角色创建出口。
2. engines.ae_harness.middleware: 导入 ObservationMiddleware，平台运行默认挂观测。
3. engines.ae_harness.tools: 导入 build_adb_tools，给执行角色挂全量设备工具。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_ui_executor.py: 设备工具数量、密钥名、观测中间件
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
        prompt_name: ae_harness 提示词文件名，不带 `.md`。
        model_short: 默认模型短名，调用方可用 `AIAgent` 配置覆盖。
    """

    role_key: str
    prompt_name: str
    model_short: str


UI_EXECUTOR_ROLE = PlatformRole(
    role_key="ui_executor",
    prompt_name="UI_EXECUTOR_PROMPT",
    model_short="govee_chat_flash",
)


async def build_ui_executor(
    *,
    model_short: str | None = None,
    observer: ObservationMiddleware | None = None,
) -> tuple[AgentBundle, ObservationMiddleware]:
    """
    装配平台侧 UI 执行角色。

    只装配不运行：返回的智能体已带全量设备工具，可直接交给运行入口。

    Args:
        model_short: 模型短名；不传则用角色的默认值。
        observer: 观测中间件；不传则新建一个。

    Returns:
        (角色 bundle, 观测中间件)；观测中间件已挂到智能体上。

    Raises:
        ValueError: 模型短名不存在或密钥没配。
        FileNotFoundError: 提示词文件不存在。
    """
    watcher = observer if observer is not None else ObservationMiddleware()
    bundle = create_agent(
        UI_EXECUTOR_ROLE.role_key,
        UI_EXECUTOR_ROLE.prompt_name,
        model_short or UI_EXECUTOR_ROLE.model_short,
        observers=[watcher],
    )
    for tool in build_adb_tools():
        await bundle.agent.toolkit.add_tool(tool)
    return bundle, watcher
