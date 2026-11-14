"""ae_harness 观测中间件：只读承诺与两条投递路径。

只测 `middleware/observer.py`：透传一致、压缩两态、hook 面、投递方式。
不测装配（`agents/creator.py`）与落盘（`event/record.py`），二者各有自己的测试。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from engines.ae_harness.middleware import (
    KIND_COMPRESS,
    KIND_SYSTEM_PROMPT,
    ObservationMiddleware,
    ObservationRecord,
)

pytestmark = [pytest.mark.unit]


class _Model:
    """替身：模型，只提供上下文窗口。"""

    context_size = 1000


class _ContextConfig:
    """替身：上下文配置，只提供触发比例。"""

    trigger_ratio = 0.7


@dataclass
class _State:
    """替身：智能体状态，只提供上下文消息列表。"""

    context: list = field(default_factory=list)


class _Agent:
    """替身：智能体，只提供观测用到的四个属性。"""

    def __init__(self, messages: int) -> None:
        self.name = "ui_executor"
        self.state = _State(context=list(range(messages)))
        self.context_config = _ContextConfig()
        self.model = _Model()


@dataclass
class _Hint:
    """替身：压缩指令块。"""

    hint: str


def test_only_two_hooks_implemented():
    """只实现两个观测 hook，不碰能力型 hook 与工具来源。"""
    observer = ObservationMiddleware()
    assert observer.is_implemented("on_system_prompt")
    assert observer.is_implemented("on_compress_context")
    for hook in ("list_tools", "on_reply", "on_model_call", "on_acting", "on_check_permission"):
        assert not observer.is_implemented(hook), hook


async def test_system_prompt_returned_unchanged():
    """变换式 hook 必须原样返回，同时记下全文与长度。"""
    observer = ObservationMiddleware()
    prompt = "你是执行者。\n严格遵守工具返回。"
    assert await observer.on_system_prompt(_Agent(0), prompt) == prompt

    record = observer.records[0].as_dict()
    assert record["kind"] == KIND_SYSTEM_PROMPT
    assert record["agent"] == "ui_executor"
    assert record["text"] == prompt
    assert record["length"] == len(prompt)


async def test_default_container_collects_records():
    """不注入回调时，记录进自有 records。"""
    observer = ObservationMiddleware()
    await observer.on_system_prompt(_Agent(0), "x")
    assert len(observer.records) == 1
    assert isinstance(observer.records[0], ObservationRecord)


async def test_emit_callback_takes_records():
    """注入回调时，记录交给回调，自有 records 保持为空。"""
    collected: list[ObservationRecord] = []
    observer = ObservationMiddleware(emit=collected.append)
    await observer.on_system_prompt(_Agent(0), "x")
    assert len(collected) == 1
    assert observer.records == []


async def test_compress_without_shrink_marks_not_compressed():
    """未达阈值（条数不变）时，记录为未压缩，但仍给阈值参数。"""
    observer = ObservationMiddleware()
    agent = _Agent(5)
    calls = 0

    async def next_handler(**kwargs):
        nonlocal calls
        calls += 1

    await observer.on_compress_context(
        agent, {"context_config": None, "instructions": None}, next_handler
    )

    assert calls == 1, "下游必须且只被调用一次"
    record = observer.records[0].as_dict()
    assert record["kind"] == KIND_COMPRESS
    assert record["messages_before"] == 5
    assert record["messages_after"] == 5
    assert record["compressed"] is False
    assert record["trigger_ratio"] == 0.7
    assert record["context_size"] == 1000
    assert record["threshold"] == pytest.approx(700.0)
    assert record["instructions"] == ""


async def test_compress_with_shrink_marks_compressed():
    """条数减少时，记录为已压缩并给出前后条数。"""
    observer = ObservationMiddleware()
    agent = _Agent(10)

    async def next_handler(**kwargs):
        agent.state.context = agent.state.context[:3]

    await observer.on_compress_context(
        agent, {"context_config": None, "instructions": _Hint("保留工具结论")}, next_handler
    )

    record = observer.records[0].as_dict()
    assert record["messages_before"] == 10
    assert record["messages_after"] == 3
    assert record["compressed"] is True
    assert record["instructions"] == "保留工具结论"


async def test_compress_survives_unknown_agent_shape():
    """智能体结构不符时只记空值，不抛异常打断运行。"""
    observer = ObservationMiddleware()

    async def next_handler(**kwargs):
        return None

    await observer.on_compress_context(object(), {"context_config": None}, next_handler)
    record = observer.records[0].as_dict()
    assert record["messages_before"] is None
    assert record["compressed"] is None
    assert record["agent"] == ""
