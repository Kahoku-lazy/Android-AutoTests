"""
文件名: ➡️ event_log.py 🏁
路径: ➡️ engines/agents/event_log.py 🏁
模块功能：➡️ 写一行到事件日志。动作里的换行换成空格，保证一行一条 🏁
Python 调试：➡️ python -m engines.agents.event_log 🏁
时间：➡️ 2026-10-20 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. write_line: 把一行「模型 | 动作」交给统一日志，追加写入 logs/agents/agent_events.log。
🏁
关联模块：➡️
1. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. 暂无专门单测
🏁
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
