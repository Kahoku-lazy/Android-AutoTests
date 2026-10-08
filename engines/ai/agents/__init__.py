"""智能体包 —— 只负责「配一个 Agent」：name / system_prompt / model / toolkit。

公开导出：角色规格与三个角色类、装配工厂、角色配置（含提示词常量所在的 `config` 模块）。

MUST NOT 在此导出引擎入口（`engines.ai.engine.AgentScopeEngine`）：组合根反过来
import 本包，再导出会形成 `agents ↔ engine` 的循环导入（见变更设计 D3）。
"""

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
from .model import (
    AgentRole,
    ExecutorRole,
    PlannerRole,
    RoleSpec,
    VerifierRole,
    build_device_models,
)

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
