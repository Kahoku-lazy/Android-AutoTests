"""智能体包 —— 只负责「配一个 Agent」：name / system_prompt / model / toolkit。

包内 `base` 提供模型创建与角色基类，`planner` / `executor` / `verifier` 继承它，
`config` 提供提示词与工具子集。本文件是公开出口，另含装配工厂 `build_device_models`。
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
    media_root: str = "",
    log_path: str = "",
    task_id: int = 0,
) -> tuple[PlannerRole, ExecutorRole, VerifierRole]:
    """按三角色配置创建三个角色对象（planner / executor / verifier）。

    Args:
        config: 三角色模型连接配置 + max_loops。
        tools: 平台全量工具（各角色按自己的 `RoleSpec.tool_names` 取子集；
            同名设备动作工具由引擎自带，注入的条目被跳过）。
        user_id: 注入工具包装层，用于写工具的鉴权与归属。
        skill_dirs: 启用的 skill 文件夹绝对路径。
        media_root: 截图等证据的落盘根目录；空则用引擎默认目录。
        log_path: 过程日志基路径；空则用 `<当前目录>/logs/agents.log`。
        task_id: 任务 id（只用于过程日志的任务与步骤标识；0 表示无任务上下文）。

    Returns:
        (planner, executor, verifier) 三个角色对象。
    """
    dirs = skill_dirs or []
    shared = {
        "user_id": user_id,
        "skill_dirs": dirs,
        "media_root": media_root,
        "log_path": log_path,
        "task_id": task_id,
    }
    return (
        PlannerRole(config.planner, tools, **shared),
        ExecutorRole(config.executor, tools, **shared),
        VerifierRole(config.verifier, tools, **shared),
    )
