"""
文件名: ➡️ memory.py 🏁
路径: ➡️ engines/agents/middleware/memory.py 🏁
模块功能：➡️ 接入点（TODO，另行立单）： 🏁
Python 调试：➡️ python -m engines.agents.middleware.memory 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. build_memory_middleware: 长期记忆的装配入口（当前只留入口，不实现）。
🏁
关联模块：➡️
1. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from __future__ import annotations

import os

from agentscope.middleware import MiddlewareBase

from utils.logs import agent_event_log

MEMORY_ENV = "AGENT_MEMORY_BACKEND"
"""预留的长期记忆后端选择；当前配置也不会生效，只会记一条警告。"""


def build_memory_middleware() -> MiddlewareBase | None:
    """长期记忆装配入口：当前恒返回 None。

    Returns:
        None。该能力尚未实现，调用方据此跳过装配。
    """
    backend = os.environ.get(MEMORY_ENV, "").strip()
    if backend:
        agent_event_log.warning("长期记忆尚未实现，已忽略 %s=%s", MEMORY_ENV, backend)
    return None
