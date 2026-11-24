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
