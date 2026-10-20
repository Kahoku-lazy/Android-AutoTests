"""
python -m 调试路径: engines.agents.messaging.record

本模块的业务功能如下：
1. EventRecord: 一条可交给接收方的结构化事件，不含任何写入。
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
