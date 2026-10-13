"""事件流 → 过程记录：思考 / 工具调用 / 工具返回的实时落盘与汇总（零网络、零设备）。"""

from __future__ import annotations

import asyncio
import json

from types import SimpleNamespace

import pytest

from agentscope.message import TextBlock

from engines.ai.agents import AgentRole, ModelConfig, RoleSpec
from engines.ai.messaging import EventStreamRecorder
from engines.ai.process_log import AgentProcessLog


def _event(name: str, **fields):
    """构造一个"事件"：类名即事件名（记录器按事件类名分发），字段直接放属性。"""
    cls = type(name, (), {"__init__": lambda self, **kwargs: self.__dict__.update(kwargs)})
    return cls(**fields)


def _recorder(
    tmp_path, *, scope="任务 12 · 步骤 3/8"
) -> tuple[EventStreamRecorder, AgentProcessLog]:
    log = AgentProcessLog(str(tmp_path / "agents.log"))
    return EventStreamRecorder(log, role="executor", model="deepseek-flash", scope=scope), log


@pytest.mark.unit
def test_thinking_block_is_written_when_it_ends(tmp_path):
    """思考在块结束时整块落一条，并进入汇总。"""
    recorder, log = _recorder(tmp_path)

    recorder.consume(_event("ThinkingBlockDeltaEvent", block_id="b1", delta="先截图看当前页面"))
    assert log.path and not log.current_path().exists()  # 未结束前不落盘
    recorder.consume(_event("ThinkingBlockEndEvent", block_id="b1"))

    assert recorder.thinking == ["先截图看当前页面"]
    line = log.current_path().read_text(encoding="utf-8").splitlines()[0]
    assert line.split(" | ")[4:] == ["思考", "先截图看当前页面"]


@pytest.mark.unit
def test_tool_call_and_result_are_paired(tmp_path):
    """工具调用落完整入参；工具返回落状态与返回内容，并抽出截图路径。"""
    recorder, log = _recorder(tmp_path)

    recorder.consume(
        _event("ToolCallStartEvent", tool_call_id="t1", tool_call_name="screenshot_page")
    )
    recorder.consume(
        _event("ToolCallDeltaEvent", tool_call_id="t1", delta='{"serial": "R5CT62RH88F"}')
    )
    recorder.consume(_event("ToolCallEndEvent", tool_call_id="t1"))
    recorder.consume(
        _event(
            "ToolResultTextDeltaEvent",
            tool_call_id="t1",
            delta=json.dumps(
                {
                    "screenshot_path": "inspector/shots/a.png",
                    "screenshot_name": "a.png",
                    "base64": "AAAABBBB",
                }
            ),
        )
    )
    recorder.consume(_event("ToolResultEndEvent", tool_call_id="t1", state="success"))

    assert recorder.tool_usage[0] == {
        "type": "call",
        "name": "screenshot_page",
        "input": {"serial": "R5CT62RH88F"},
    }
    result = recorder.tool_usage[1]
    assert result["type"] == "result"
    assert result["state"] == "success"
    assert result["screenshot_path"] == "inspector/shots/a.png"
    assert "base64" not in result["output"]
    assert recorder.screenshot_path == "inspector/shots/a.png"

    text = log.current_path().read_text(encoding="utf-8")
    assert "工具调用" in text and "工具返回" in text
    assert "AAAABBBB" not in text  # 图片二进制不入日志


@pytest.mark.unit
def test_image_event_records_no_binary(tmp_path):
    """图片数据事件只记一行说明，不含二进制。"""
    recorder, log = _recorder(tmp_path)

    recorder.consume(_event("ToolResultDataDeltaEvent", tool_call_id="t1", delta=b"\x89PNG"))

    text = log.current_path().read_text(encoding="utf-8")
    assert "截图" in text
    assert "PNG" not in text


@pytest.mark.unit
def test_unknown_event_is_ignored(tmp_path):
    """未知事件不抛异常、不落盘（框架加新事件时不影响执行）。"""
    recorder, log = _recorder(tmp_path)

    recorder.consume(_event("SomeFutureEvent", anything=1))

    assert not log.current_path().exists()


@pytest.mark.unit
def test_finish_flushes_blocks_without_end_event(tmp_path):
    """流被截断（只有增量、没有结束事件）时，finish 兜底补记。"""
    recorder, log = _recorder(tmp_path)

    recorder.consume(_event("ThinkingBlockDeltaEvent", block_id="b1", delta="半截思考"))
    recorder.consume(_event("ToolCallStartEvent", tool_call_id="t1", tool_call_name="tap_screen"))
    recorder.consume(_event("ToolCallDeltaEvent", tool_call_id="t1", delta='{"x": 1}'))
    recorder.finish()

    assert recorder.thinking == ["半截思考"]
    assert recorder.tool_usage[0]["name"] == "tap_screen"


class _StubRole(AgentRole):
    """最小角色：只用行为骨架，工具子集为空。"""

    spec = RoleSpec(role="executor", prompt="测试提示词", tool_names=())


class _StubAgent:
    """冒充 AgentScope Agent：回放给定事件，并在末尾给出最终消息。"""

    def __init__(self, events, message):
        self._events = events
        self._message = message
        self.state = SimpleNamespace(context=[message])

    async def reply_stream(self, inputs, yield_final_msg: bool = False):
        for event in self._events:
            yield event
        if yield_final_msg:
            yield self._message


@pytest.mark.unit
def test_role_executes_through_event_stream(tmp_path):
    """角色执行走事件流：过程实时落日志，结果对象仍按老字段组装。"""
    message = SimpleNamespace(
        content=[TextBlock(type="text", text='{"result": "PASS"}')],
        usage=SimpleNamespace(
            input_tokens=11,
            output_tokens=3,
            cache_input_tokens=5,
            cache_creation_input_tokens=0,
        ),
        role="assistant",
        name="executor",
    )
    events = [
        _event("ThinkingBlockDeltaEvent", block_id="b1", delta="先点开关"),
        _event("ThinkingBlockEndEvent", block_id="b1"),
        _event("ToolCallStartEvent", tool_call_id="t1", tool_call_name="tap_screen"),
        _event("ToolCallDeltaEvent", tool_call_id="t1", delta='{"x": 100, "y": 200}'),
        _event("ToolCallEndEvent", tool_call_id="t1"),
        _event("ToolResultTextDeltaEvent", tool_call_id="t1", delta='{"clicked": true}'),
        _event("ToolResultEndEvent", tool_call_id="t1", state="success"),
    ]
    role = _StubRole(
        ModelConfig(provider="deepseek", model_name="deepseek-flash", api_key="test-key"),
        [],
        log_path=str(tmp_path / "agents.log"),
        task_id=12,
    )
    role.agent = _StubAgent(events, message)
    role.mark_scope("步骤 3/8")

    result = asyncio.run(role._execute("点一下开关"))

    assert result.output == '{"result": "PASS"}'
    assert result.thinking == ["先点开关"]
    assert result.tool_usage[0]["name"] == "tap_screen"
    assert result.usage["input_tokens"] == 11
    text = role.process_log.current_path().read_text(encoding="utf-8")
    assert "任务 12 · 步骤 3/8" in text
    assert "deepseek-flash" in text
