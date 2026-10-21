"""交卷拦截：自述未完成的 handover 在同一尝试内被退回继续。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agentscope.message import AssistantMsg, Msg
from pydantic import BaseModel

from engines.agents.workflow.handover_guard import (
    IncompleteHandoverGuard,
    handover_self_declares_incomplete,
)

pytestmark = [pytest.mark.unit]


class _Handover(BaseModel):
    """SOP 步骤用的交付契约。"""

    handover: str


class _Plain(BaseModel):
    """不含 handover 字段的契约，用来确认不误拦。"""

    answer: str


def _final(text: str):
    return AssistantMsg(name="executor_role", content="done", structured_output={"handover": text})


class _FakeAgent:
    """按顺序吐出给定的 handover，记录每次被调用时收到的输入。"""

    name = "executor_role"
    model = SimpleNamespace(model="fake-model")

    def __init__(self, handovers: list[str]) -> None:
        self._handovers = handovers
        self.calls: list[object] = []

    async def reply_stream(self, inputs=None, structured_schema=None, yield_final_msg=False):
        index = len(self.calls)
        self.calls.append(inputs)
        text = self._handovers[min(index, len(self._handovers) - 1)]
        yield _final(text)


def _msg_text(message) -> str:
    """把消息正文取成纯文本，正文可能是字符串或内容块列表。"""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(str(text))
    return "\n".join(parts)


async def _drain(guard: IncompleteHandoverGuard, schema=_Handover):
    """跑一次 guard，返回 (yield 出的最终消息列表, 事件列表)。"""
    finals, events = [], []
    async for item in guard.reply_stream(
        inputs="开始", structured_schema=schema, yield_final_msg=True
    ):
        if isinstance(item, Msg):
            finals.append(item)
        else:
            events.append(item)
    return finals, events


def test_marker_detection_covers_incomplete_wording():
    assert handover_self_declares_incomplete("【本步：部分完成 —— 尚未点击右上角 ✓】")[0] is True
    assert handover_self_declares_incomplete("请下一步立即执行")[1] == "请下一步"
    assert handover_self_declares_incomplete("已完成，页面回到设备页")[0] is False
    assert handover_self_declares_incomplete("")[0] is False


def test_met_judgement_word_is_not_a_marker():
    """“未达成”是验收判据用语，执行者逐条汇报时会出现，不能当自述未完成。"""
    assert handover_self_declares_incomplete("逐条对照：第 1 条达成，第 2 条未达成")[0] is False


@pytest.mark.asyncio
async def test_clean_handover_passes_through_once():
    agent = _FakeAgent(["已完成，页面已在设备页"])
    guard = IncompleteHandoverGuard(agent)

    finals, _ = await _drain(guard)

    assert len(agent.calls) == 1
    assert guard.nudges == 0
    assert finals[0].structured_output["handover"] == "已完成，页面已在设备页"


@pytest.mark.asyncio
async def test_incomplete_handover_is_sent_back_with_a_continue_instruction():
    agent = _FakeAgent(["尚未点击右上角 ✓，请下一步执行", "已完成，样式栏消失"])
    guard = IncompleteHandoverGuard(agent)

    finals, _ = await _drain(guard)

    assert len(agent.calls) == 2
    assert guard.nudges == 1
    assert agent.calls[0] == "开始"
    nudge = _msg_text(agent.calls[1])
    assert "继续执行" in nudge
    assert "尚未" in nudge
    assert finals[-1].structured_output["handover"] == "已完成，样式栏消失"


@pytest.mark.asyncio
async def test_repeated_incomplete_wording_stops_at_the_cap_and_passes_to_verifier():
    agent = _FakeAgent(["部分完成"])
    guard = IncompleteHandoverGuard(agent, max_nudges=2)

    finals, _ = await _drain(guard)

    assert len(agent.calls) == 3
    assert guard.nudges == 2
    assert finals[-1].structured_output["handover"] == "部分完成"


@pytest.mark.asyncio
async def test_schema_without_handover_is_not_guarded():
    agent = _FakeAgent(["尚未完成"])
    guard = IncompleteHandoverGuard(agent)

    finals, _ = await _drain(guard, schema=_Plain)

    assert len(agent.calls) == 1
    assert guard.nudges == 0
    assert finals[0].structured_output["handover"] == "尚未完成"


def test_guard_rejects_an_object_without_reply_stream():
    with pytest.raises(TypeError):
        IncompleteHandoverGuard(object())
