"""步骤规划角色：接受用户需求，输出步骤计划（goal + steps）。

继承 `base.AgentRole`，只填自己的配方（提示词与工具子集取自 `config.py`）；
公共主干（装配 / 接受任务 / 执行 / 出报告）在基类，不在此文件。
"""

from __future__ import annotations

from engines.ai.messaging import RoleResult

from .base import AgentRole, RoleSpec
from .config import DEVICE_PLANNER_TOOLS, PLANNER_PROMPT


class PlannerRole(AgentRole):
    """规划角色：接受用户需求，输出步骤计划（goal + steps）。"""

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
        return await self._execute(goal)
