"""
文件名: ➡️ event_log.py 🏁
路径: ➡️ engines/agents/event_log.py 🏁
模块功能：➡️ 事件日志写入的过渡入口 🏁
Python 调试：➡️ python -m engines.agents.event_log 🏁
时间：➡️ 2026-10-20 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本文件只再导出 messaging.event_log.write_line。
🏁
关联模块：➡️
1. engines.agents.messaging.event_log: 事件日志写入的实现。
🏁
测试：➡️
1. tests/engines/agents/unit/test_sop_event_stream.py: 旧路径与新路径导出同一函数
🏁
"""

from engines.agents.messaging.event_log import write_line

__all__ = ["write_line"]
