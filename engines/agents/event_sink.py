"""
文件名: ➡️ event_sink.py 🏁
路径: ➡️ engines/agents/event_sink.py 🏁
模块功能：➡️ 事件接收方的过渡入口 🏁
Python 调试：➡️ python -m engines.agents.event_sink 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本文件只再导出 messaging.event_sink 的公开符号。
🏁
关联模块：➡️
1. engines.agents.messaging.event_sink: 接收方绑定、运行上下文与预算的实现。
🏁
测试：➡️
1. tests/task/api/test_task_event_store.py: 旧路径与新路径导出同一组符号
🏁
"""

import sys
import types

from engines.agents.messaging import event_sink as _sink
from engines.agents.messaging.event_sink import *  # noqa: F403
from engines.agents.messaging.event_sink import __all__ as _SINK_ALL

_PATCHED = ("MAX_MODEL_CALLS", "MAX_MODEL_CALLS_PER_CASE", "MAX_RUN_SECONDS")


class _CompatModule(types.ModuleType):
    """过渡模块：预算常量的补丁同步写到实现模块。"""

    def __setattr__(self, name: str, value: object) -> None:
        """写入本模块，并把预算常量同步到实现模块。

        Args:
            name: 属性名。
            value: 新值。
        """
        if name in _PATCHED:
            setattr(_sink, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CompatModule
__all__ = [*_SINK_ALL]
