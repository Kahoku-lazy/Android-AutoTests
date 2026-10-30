"""
文件名: ➡️ record.py 🏁
路径: ➡️ engines/agents/messaging/record.py 🏁
模块功能：➡️ 一条结构化事件。费用为 8 位小数；图片 base64 只放在本对象上 🏁
Python 调试：➡️ python -m engines.agents.messaging.record 🏁
时间：➡️ 2026-10-20 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. EventRecord: 一条可交给接收方的结构化事件，不含任何写入。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/api/test_task_event_store.py: 任务事件落库：事件、缩略图、小时用量和任务费用
2. tests/engines/agents/test_event_fold.py: 事件折叠：增量合并、工具逐条、角色继承、8 位费用与图片
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

_ZERO = Decimal("0.00000000")


@dataclass
class EventRecord:
    """一条结构化事件。费用为 8 位小数；图片 base64 只放在本对象上。"""

    event_type: str
    phase: str
    block_type: str
    is_delta: bool = False
    role_name: str = ""
    role_kind: str = ""
    model: str = ""
    payload: dict = field(default_factory=dict)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int = 0
    cost_input: Decimal = field(default_factory=lambda: _ZERO)
    cost_output: Decimal = field(default_factory=lambda: _ZERO)
    cost_cache: Decimal = field(default_factory=lambda: _ZERO)
    pricing_snapshot: dict | None = None
    media_type: str = ""
    image_b64: str = ""
