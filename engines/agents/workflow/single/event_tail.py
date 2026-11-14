"""
文件名: ➡️ event_tail.py 🏁
路径: ➡️ engines/agents/workflow/single/event_tail.py 🏁
模块功能：➡️ 从本地事件日志里取一段单智能体对话的模型事件 🏁
Python 调试：➡️ python -m engines.agents.workflow.single.event_tail 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. read_session_events: 按会话标记从事件日志里取最近一段，供前端展示。
2. 只读：不写库、不改日志；日志缺失时返回空列表。
🏁
关联模块：➡️
1. utils.logs: 导入 AGENT_EVENT_LOG_PATH，取事件日志路径
🏁
测试：➡️
1. tests/engines/agents/unit/test_single_agent_workflow.py: 会话段落解析与缺失日志
🏁
"""

from __future__ import annotations

from pathlib import Path

from utils.logs import AGENT_EVENT_LOG_PATH

__all__ = ["SESSION_MARK", "read_session_events"]

SESSION_MARK = "单智能体对话"
"""会话标记前缀：`单智能体对话 | {session} | 开始/结束`。"""

_LINE_SEPARATOR = " - "
_MAX_LINES = 400


def _mark_prefix(session_id: str) -> str:
    """
    拼会话行的公共前缀。

    Args:
        session_id: 前端本次对话的连接键。

    Returns:
        形如 `单智能体对话 | abc` 的前缀。
    """
    return f"{SESSION_MARK} | {session_id} | "


def _message_of(line: str) -> str:
    """
    从一行日志里取消息正文。

    Args:
        line: 形如 `时间 - agent_event - INFO - 消息` 的一行。

    Returns:
        时间与消息；格式不符时原样返回整行。
    """
    parts = line.split(_LINE_SEPARATOR, 3)
    if len(parts) < 4:
        return line.strip()
    return f"{parts[0]} {parts[3]}".strip()


def _session_segment(lines: list[str], session_id: str) -> list[str]:
    """
    取该会话最后一次「开始」到「结束」之间的行，首行是带模型名的开始行。

    Args:
        lines: 日志全文按行拆开的结果。
        session_id: 会话键。

    Returns:
        段落内的行；找不到开始标记时返回空列表。
    """
    prefix = _mark_prefix(session_id)
    start = -1
    for index, line in enumerate(lines):
        if f"{prefix}开始" in line:
            start = index
    if start < 0:
        return []
    head = _start_head(lines[start].rstrip())
    segment: list[str] = [head] if head else []
    for line in lines[start + 1 :]:
        text = line.rstrip()
        if f"{prefix}结束" in text:
            break
        if text:
            segment.append(text)
    return segment


def _start_head(line: str) -> str:
    """
    把开始行里的模型名抽出来。

    Args:
        line: `... - 单智能体对话 | 会话 | 开始 | 模型名`。

    Returns:
        `对话开始 · 模型 xxx`；没有模型名时返回 `对话开始`。
    """
    parts = [part.strip() for part in line.split("|")]
    model = parts[-1] if len(parts) >= 4 else ""
    return f"对话开始 · 模型 {model}" if model and model != "-" else "对话开始"


def read_session_events(
    session_id: str,
    *,
    path: Path | None = None,
    limit: int = 120,
) -> list[str]:
    """
    读取一次会话的模型事件行。

    Args:
        session_id: 前端本次对话的连接键。
        path: 日志路径；None 用统一事件日志。
        limit: 最多返回多少行，保留最近的部分。

    Returns:
        事件行（时间 + 消息）；日志不存在或没有该会话时返回空列表。

    Raises:
        ValueError: 会话键为空。
    """
    key = session_id.strip()
    if not key:
        raise ValueError("session_id 不能为空")
    target = Path(path) if path is not None else AGENT_EVENT_LOG_PATH
    if not target.is_file():
        return []
    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()[-_MAX_LINES:]
    segment = _session_segment(lines, key)
    return [_message_of(line) for line in segment[-limit:]]
