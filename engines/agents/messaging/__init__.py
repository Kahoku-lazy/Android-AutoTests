"""对话稿记录包 —— 消费 `reply_stream` 的事件并落对话稿。

公开导出 `DialogueLog`、工具返回 → 可读文本的三个函数，以及一轮回复的
用量与费用（`reply_usage` / `reply_cost`）与上屏（`print_result` /
`render_reply_stream`）。
"""

from .dialogue import DialogueLog
from .messages import (
    print_result,
    render_reply_stream,
    reply_cost,
    reply_usage,
    sanitize_tool_output_text,
    screenshot_path_from_tool_output,
    tool_output_text_parts,
)

__all__ = [
    "DialogueLog",
    "print_result",
    "render_reply_stream",
    "reply_cost",
    "reply_usage",
    "sanitize_tool_output_text",
    "screenshot_path_from_tool_output",
    "tool_output_text_parts",
]
