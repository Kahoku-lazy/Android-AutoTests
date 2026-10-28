"""
python -m 调试路径: engines.agents.middleware.budget

本模块的业务功能如下：
1. build_budget_middleware: 按环境变量装配「单次回复 token 预算」中间件。
"""

from __future__ import annotations

from agentscope.middleware import ReplyBudgetControlMiddleware

from .envs import env_float, env_int

BUDGET_ENV = "AGENT_REPLY_TOKEN_BUDGET"
"""单次回复的加权 token 上限；0 表示关闭该护栏。"""

INPUT_WEIGHT_ENV = "AGENT_REPLY_INPUT_WEIGHT"
"""输入 token 的权重。"""

OUTPUT_WEIGHT_ENV = "AGENT_REPLY_OUTPUT_WEIGHT"
"""输出 token 的权重；通常高于输入。"""

DEFAULT_TOKEN_BUDGET = 600_000
"""默认上限：按「失控护栏」而不是「成本控制」取值。

执行者一轮最多 60 次 ReAct，视图片段每轮都会重发上下文，正常长用例也可能
累计到几十万加权 token；20 万会误杀正常步骤，60 万只在真的打转时才触发。
想按成本收紧，按需改环境变量即可。
"""

DEFAULT_INPUT_WEIGHT = 1.0
DEFAULT_OUTPUT_WEIGHT = 2.0

HINT_MESSAGE = (
    "<system-reminder>本轮回复的 token 预算已用尽。请立即收尾：给出当前结论，"
    "不要再调用任何工具。</system-reminder>"
)


def build_budget_middleware() -> ReplyBudgetControlMiddleware | None:
    """按环境变量装配单次回复的 token 预算中间件。

    Returns:
        预算中间件；预算配成 0 或负数时返回 None（关闭护栏）。
    """
    budget = env_int(BUDGET_ENV, DEFAULT_TOKEN_BUDGET)
    if budget <= 0:
        return None
    return ReplyBudgetControlMiddleware(
        token_budget=budget,
        input_token_weight=env_float(INPUT_WEIGHT_ENV, DEFAULT_INPUT_WEIGHT),
        output_token_weight=env_float(OUTPUT_WEIGHT_ENV, DEFAULT_OUTPUT_WEIGHT),
        hint_message=HINT_MESSAGE,
    )
