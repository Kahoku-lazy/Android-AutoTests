"""UI 执行角色：接受单个操作步骤，在设备上执行并输出结果与截图。

继承 `base.AgentRole`，只填自己的配方（提示词与工具子集取自 `config.py`）；
多模态与 ReAct 参数由本文件的 RoleSpec 声明，公共主干在基类。
"""

from __future__ import annotations

from engines.ai.messaging import RoleResult

from .base import AgentRole, RoleSpec
from .config import VISION_PROMPT, VISION_TOOLS


class ExecutorRole(AgentRole):
    """执行角色：接受单个操作步骤，在设备上执行并输出结果与截图。

    多模态（vision=True）：靠截图看图定位元素；ReAct 最多 8 轮（max_iters=8）；
    上下文最多保留 5 张图（max_image_num=5）控制 token。
    """

    spec = RoleSpec(
        role="executor",
        prompt=VISION_PROMPT,
        tool_names=tuple(VISION_TOOLS),
        vision=True,
        context_config={"max_image_num": 5},
        react_config={"max_iters": 8},
    )

    async def run(
        self,
        serial: str,
        action: str,
        idx: int,
        total: int,
        retry_hint: str = "",
    ) -> RoleResult:
        """接受任务：在指定设备上执行一个操作步骤。

        Args:
            serial: 目标设备 serial。
            action: 本步骤要执行的一个操作。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            retry_hint: 上次验收失败回灌的修正提示（空串 = 首次执行）。

        Returns:
            RoleResult（output 为 {"result","click_timer","screenshot"} JSON；screenshot 为操作结果截图）。
        """
        prompt = f"当前设备 serial：{serial}\n请执行以下操作（第 {idx}/{total} 步）：\n{action}"
        if retry_hint:
            prompt += f"\n<feedback>上次执行未通过验收，请修正后重做：\n{retry_hint}</feedback>"
        return await self._execute(prompt)
