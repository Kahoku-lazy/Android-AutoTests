"""消息与事件包（叶子）—— 智能体通信的读取与记录。

公开导出：角色任务报告 `RoleResult` 与把消息块/上下文读成语义记录的函数。
后续变更的事件流出口（消费 AgentScope `reply_stream` 并打印日志）落在本包。
"""

from .messages import (
    RoleResult,
    collect_from_blocks,
    collect_trace,
    context_summary,
    count_tool_results,
    extract_screenshot,
    extract_screenshot_path,
    prompt_to_input_text,
    sanitize_tool_output_text,
    screenshot_path_from_tool_output,
    tool_output_text_parts,
)

__all__ = [
    "RoleResult",
    "collect_from_blocks",
    "collect_trace",
    "context_summary",
    "count_tool_results",
    "extract_screenshot",
    "extract_screenshot_path",
    "prompt_to_input_text",
    "sanitize_tool_output_text",
    "screenshot_path_from_tool_output",
    "tool_output_text_parts",
]
