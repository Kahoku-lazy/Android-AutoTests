"""执行智能体角色。继承 BaseRole，挂上设备工具和执行技能。"""

from __future__ import annotations

from ..prompt_config import EXECUTOR_PROMPT
from ..prompts.verifier_prompt import verifier_system_prompt
from ..tools_config import (
    EXECUTOR_SKILLS_NAMES,
    build_executor_toolkit,
    build_verifier_toolkit,
    register_skills,
)
from .base import BaseRole
from .config import ModelConfig, RoleSpecConfig


class ExecutorRole(BaseRole):
    """设备执行角色"""

    def __init__(
        self,
        config: ModelConfig,
        *,
        system_prompt: str | None = None,
        name: str = "executor_role",
    ) -> None:
        role = RoleSpecConfig(
            name=name,
            system_prompt=system_prompt or EXECUTOR_PROMPT,
            toolkit=build_executor_toolkit(),
            vision=True,
        )
        super().__init__(config, role)
        register_skills(self.role.toolkit, EXECUTOR_SKILLS_NAMES, group_name="platform_business")


class VerifierRole(BaseRole):
    """验收角色"""

    def __init__(
        self,
        config: ModelConfig,
        *,
        system_prompt: str | None = None,
        name: str = "verifier_role",
    ) -> None:
        role = RoleSpecConfig(
            name=name,
            system_prompt=system_prompt or verifier_system_prompt(),
            toolkit=build_verifier_toolkit(),
            vision=True,
        )
        super().__init__(config, role)
