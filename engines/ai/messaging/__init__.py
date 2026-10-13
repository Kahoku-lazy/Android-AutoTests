"""消息与事件包 —— 智能体回复与上下文的读取与记录。

公开导出角色任务报告 `RoleResult`、消息块与上下文 → 语义记录的函数，
以及消费 `reply_stream` 事件流的 `EventStreamRecorder`。
"""

from .events import EventStreamRecorder
from .messages import (
    RoleResult,
    collect_from_blocks,
    collect_trace,
    context_summary,
    extract_screenshot,
    extract_screenshot_path,
    prompt_to_input_text,
    sanitize_tool_output_text,
    screenshot_path_from_tool_output,
    tool_output_text_parts,
)

__all__ = [
    "EventStreamRecorder",
    "RoleResult",
    "collect_from_blocks",
    "collect_trace",
    "context_summary",
    "extract_screenshot",
    "extract_screenshot_path",
    "prompt_to_input_text",
    "sanitize_tool_output_text",
    "screenshot_path_from_tool_output",
    "tool_output_text_parts",
]
