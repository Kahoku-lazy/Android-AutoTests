"""
文件名: ➡️ goal_case.py 🏁
路径: ➡️ engines/backend_bridge/workflow/goal_case.py 🏁
模块功能: ➡️ 用例编写的目标循环：编写、验收、退回一次，通过后交给入库函数 🏁
Python 调试: ➡️ python -m engines.backend_bridge.workflow.goal_case 🏁
时间: ➡️ 2026-11-24 🏁
作者: ➡️ kahoku 🏁
版本: ➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明: ➡️
1. run_goal_case: 用可替换的一轮执行模拟 GoalPipeline 的退回重做。
2. 通过后只调用一次入库函数，不创建下一段任务。
🏁
关联模块: ➡️
1. agentscope.pipeline: 生产调用方传入官方 GoalPipeline。
🏁
测试: ➡️
1. 暂无
🏁
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

__all__ = ["run_goal_case"]


async def run_goal_case(
    material: str,
    attempt: Callable[[str], Awaitable[dict]],
    save_cases,
    *,
    max_retries: int = 1,
) -> dict:
    """
    跑一次用例编写目标。

    Args:
        material: 一个模块的材料。
        attempt: 一轮编写加验收。返回 passed 与 rows。
        save_cases: 验收通过后写入用例库的函数。
        max_retries: 允许退回重做的次数。

    Returns:
        passed、rows 与入库结果。未通过时不调用入库。
    """
    feedback = ""
    outcome = {"passed": False, "rows": []}
    for _ in range(max_retries + 1):
        prompt = material if not feedback else f"{material}\n\n退回理由：{feedback}"
        outcome = await attempt(prompt)
        if outcome.get("passed"):
            saved = save_cases(outcome.get("rows") or [])
            return {**outcome, "saved": saved, "created_followup": False}
        feedback = str(outcome.get("reason") or "验收未通过")
    return {**outcome, "saved": None, "created_followup": False}
