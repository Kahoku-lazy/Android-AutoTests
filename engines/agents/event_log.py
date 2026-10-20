"""
python -m 调试路径: engines.agents.event_log

本模块的业务功能如下：
1. write_line: 把一行「模型 | 动作」交给统一日志，追加写入 logs/agents/agent_events.log。
"""

from __future__ import annotations

from utils.logs import agent_event_log


def write_line(model: str, action: str) -> None:
    """写一行到事件日志。动作里的换行换成空格，保证一行一条。

    Args:
        model: 保留给调用方传入，正文只记动作。
        action: 这一行的动作或汇总文本。
    """
    del model
    text = " ".join(str(action or "").split())
    agent_event_log.info(text or "-")
