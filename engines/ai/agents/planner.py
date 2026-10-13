"""步骤规划角色：接受用户需求，输出步骤计划（plan.steps）。

提示词与工具子集取自 `config.py`，公共主干在 `base.AgentRole`。
"""

from __future__ import annotations

from engines.ai.messaging import RoleResult

from .base import AgentRole, RoleSpec
from .config import CHINESE_DEMAND, DEVICE_PLANNER_TOOLS, PLANNER_PROMPT


class PlannerRole(AgentRole):
    """规划角色：接受用户需求，输出步骤计划（plan.steps）。"""

    spec = RoleSpec(
        role="planner",
        prompt=PLANNER_PROMPT,
        tool_names=tuple(DEVICE_PLANNER_TOOLS),
    )

    async def run(self, goal: str) -> RoleResult:
        """接受任务：用户一句话 UI 操作需求。

        Args:
            goal: 用户一句话 UI 操作需求。

        Returns:
            RoleResult（output 为 {"plan": {...}} 的 JSON 文本）。
        """
        self.mark_scope("规划")
        return await self._execute(goal + CHINESE_DEMAND)
