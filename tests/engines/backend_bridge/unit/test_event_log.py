"""平台事件日志：分段标记与引擎侧一致、全量内容、增量折叠。

只测 `event_log.py`；日志落盘用替身接收器。
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

import engines.backend_bridge.event_log as event_log
from engines.agents.workflow.single.event_tail import SESSION_MARK as ENGINE_MARK

pytestmark = [pytest.mark.unit]


@dataclass
class ModelCallStartEvent:
    """替身：模型调用开始。"""

    model_name: str = "deepseek-flash"


@dataclass
class ModelCallEndEvent:
    """替身：模型调用结束。"""

    input_tokens: int = 100
    output_tokens: int = 5
    cache_input_tokens: int = 60


@dataclass
class ThinkingBlockDeltaEvent:
    """替身：思考增量。"""

    delta: str = ""
    block_id: str = "t1"


@dataclass
class ThinkingBlockEndEvent:
    """替身：思考块结束。"""

    block_id: str = "t1"


@dataclass
class TextBlockDeltaEvent:
    """替身：文本增量。"""

    delta: str = ""
    block_id: str = "b1"


@dataclass
class TextBlockEndEvent:
    """替身：文本块结束。"""

    text: object = None
    block_id: str = "b1"


@dataclass
class ToolCallStartEvent:
    """替身：工具调用开始（真实事件在此带工具名）。"""

    tool_call_id: str = "c1"
    tool_call_name: str = "adb_app_start"


@dataclass
class ToolCallDeltaEvent:
    """替身：工具入参增量（真实事件没有完整 input 字段）。"""

    tool_call_id: str = "c1"
    delta: str = ""


@dataclass
class ToolCallEndEvent:
    """替身：工具调用参数结束（真实事件只有 id）。"""

    tool_call_id: str = "c1"


@dataclass
class ToolResultStartEvent:
    """替身：工具开始执行（真实事件带工具名）。"""

    tool_call_id: str = "c1"
    tool_call_name: str = "adb_app_start"


@dataclass
class ToolResultTextDeltaEvent:
    """替身：工具输出增量。"""

    tool_call_id: str = "c1"
    delta: str = ""


@dataclass
class ToolResultEndEvent:
    """替身：工具结果结束（真实事件只有 id 与 state）。"""

    tool_call_id: str = "c1"
    state: str = "success"


def _feed(events: list) -> list[str]:
    """把一串事件喂给记录器，只收非空行。"""
    logger = event_log.TurnLogger()
    return [line for line in (logger.feed(event) for event in events) if line]


def test_session_mark_matches_engine():
    """分段标记必须与引擎侧一致，否则前端事件面板读不到平台会话。"""
    assert event_log.SESSION_MARK == ENGINE_MARK


def test_mark_writes_start_and_end(monkeypatch: pytest.MonkeyPatch):
    """开始行带模型名，结束行也带；空连接键不写。"""
    lines: list[str] = []
    monkeypatch.setattr(event_log, "_write", lines.append)

    event_log.mark("s-1", "开始", "deepseek-flash")
    event_log.mark("s-1", "结束", "deepseek-flash")
    event_log.mark("", "开始", "deepseek-flash")

    assert len(lines) == 2
    assert lines[0].endswith("| s-1 | 开始 | deepseek-flash")
    assert lines[1].endswith("| s-1 | 结束 | deepseek-flash")


def test_deltas_are_folded_into_block_lines():
    """全量口径：增量在内存累积，块结束时整段写出。"""
    lines = _feed(
        [
            ThinkingBlockDeltaEvent(delta="先看屏幕。", block_id="t1"),
            ThinkingBlockDeltaEvent(delta="可能是锁屏。", block_id="t1"),
            ThinkingBlockEndEvent(block_id="t1"),
            TextBlockDeltaEvent(delta="桌面已解锁", block_id="b1"),
            TextBlockDeltaEvent(delta="，直接启动。", block_id="b1"),
            TextBlockEndEvent(block_id="b1"),
        ]
    )

    assert lines == ["思考：先看屏幕。可能是锁屏。", "回复：桌面已解锁，直接启动。"]


def test_tool_lines_carry_full_payload():
    """工具入参与结果都带工具名与完整负载（名字与负载来自开始事件与增量）。"""
    lines = _feed(
        [
            ToolCallStartEvent(),
            ToolCallDeltaEvent(delta='{"package": '),
            ToolCallDeltaEvent(delta='"com.govee.home"}'),
            ToolCallEndEvent(),
            ToolResultStartEvent(),
            ToolResultTextDeltaEvent(delta='{"status": '),
            ToolResultTextDeltaEvent(delta="true}"),
            ToolResultEndEvent(),
        ]
    )

    assert lines[0] == '工具入参 adb_app_start {"package": "com.govee.home"}'
    assert lines[1] == '工具结果 adb_app_start success {"status": true}'


def test_model_lines_carry_tokens():
    """模型节点带模型名与四类 token 中的关键三项。"""
    lines = _feed([ModelCallStartEvent(), ModelCallEndEvent()])

    assert lines[0] == "调用模型 deepseek-flash"
    assert "输入 100" in lines[1]
    assert "输出 5" in lines[1]
    assert "缓存命中 60" in lines[1]


def test_empty_block_writes_prefix_only():
    """空块只写前缀，不写冒号后空串。"""
    assert _feed([ThinkingBlockEndEvent(block_id="缺失")]) == ["思考"]


def test_text_block_falls_back_to_event_text():
    """没有增量时用事件自带的最终文本。"""
    assert _feed([TextBlockEndEvent(text="最终结论", block_id="b9")]) == ["回复：最终结论"]
