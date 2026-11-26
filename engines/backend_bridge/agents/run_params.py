from __future__ import annotations

from agentscope.agent import ContextConfig, ReActConfig

__all__ = [
    "MAX_IMAGE_NUM",
    "MAX_ITERS",
    "TOOL_RESULT_LIMIT",
    "apply_run_params",
]

MAX_IMAGE_NUM = 2
TOOL_RESULT_LIMIT = 20000
MAX_ITERS = 20


def apply_run_params(agent: object) -> None:
    agent.context_config = ContextConfig(
        max_image_num=MAX_IMAGE_NUM,
        tool_result_limit=TOOL_RESULT_LIMIT,
    )
    agent.react_config = ReActConfig(max_iters=MAX_ITERS)
