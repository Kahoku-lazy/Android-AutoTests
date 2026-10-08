"""智能体包 —— 只负责「配一个 Agent」：name / system_prompt / model / toolkit。

包内结构：`base` 提供模型创建（`create_model`）与角色基类（`RoleSpec` / `AgentRole`），
`planner` / `executor` / `verifier` 三个角色**继承**它，`config` 提供提示词与工具子集。

本文件是公开出口，另含装配工厂 `build_device_models`。工厂放包入口而非 `base`：工厂要构造
三个子类、子类又要继承 `base`，写在 `base` 会形成 `base ↔ 三角色` 的循环导入（变更设计 D1）。

MUST NOT 在此导出引擎入口（`engines.ai.engine.AgentScopeEngine`）：组合根反过来 import 本包，
再导出会形成 `agents ↔ engine` 的循环导入。
"""

from __future__ import annotations

from engines.ai.base import ToolSpec

from .base import AgentRole, RoleSpec
from .config import (
    DEVICE_PLANNER_TOOLS,
    PLANNER_PROMPT,
    VERIFIER_PROMPT,
    VERIFIER_TOOLS,
    VISION_PROMPT,
    VISION_TOOLS,
    DeviceExecutionConfig,
    ModelConfig,
)
from .executor import ExecutorRole
from .planner import PlannerRole
from .verifier import VerifierRole

__all__ = [
    "DEVICE_PLANNER_TOOLS",
    "PLANNER_PROMPT",
    "VERIFIER_PROMPT",
    "VERIFIER_TOOLS",
    "VISION_PROMPT",
    "VISION_TOOLS",
    "AgentRole",
    "DeviceExecutionConfig",
    "ExecutorRole",
    "ModelConfig",
    "PlannerRole",
    "RoleSpec",
    "VerifierRole",
    "build_device_models",
]


# ── 装配工厂 ──


def build_device_models(
    config: DeviceExecutionConfig,
    tools: list[ToolSpec],
    user_id: str = "",
    skill_dirs: list[str] | None = None,
) -> tuple[PlannerRole, ExecutorRole, VerifierRole]:
    """按三角色配置创建三个角色对象（planner / executor / verifier）。

    Args:
        config: 三角色模型连接配置 + max_loops。
        tools: 平台全量工具（各角色按自己的 RoleSpec.tool_names 子集取用）。
        user_id: 注入工具包装层（写工具鉴权/归属）。
        skill_dirs: 启用的 skill 文件夹绝对路径。

    Returns:
        (planner, executor, verifier) 三个角色对象；系统提示词各自取自角色 spec（config.py）。
    """
    dirs = skill_dirs or []
    return (
        PlannerRole(config.planner, tools, user_id, dirs),
        ExecutorRole(config.executor, tools, user_id, dirs),
        VerifierRole(config.verifier, tools, user_id, dirs),
    )
