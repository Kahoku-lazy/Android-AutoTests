"""
python -m 调试路径: engines.agents.middleware.memory

本模块的业务功能如下：
1. build_memory_middleware: 长期记忆的装配入口（当前只留入口，不实现）。

接入点（TODO，另行立单）：
- 记忆中间件应在 `on_reply` 前检索历史事实、在 `on_reply` 后写入本轮新增事实；
- 存储位置建议 `data/agent_memory/`，与资料目录、索引目录分开；
- 未实现前 MUST NOT 读取或写入任何外部存储，也 MUST NOT 引入新依赖。
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
