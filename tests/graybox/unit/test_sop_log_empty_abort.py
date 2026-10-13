"""日志为空时记成引擎的一次驳回，次数用尽后才失败。"""

from __future__ import annotations

import asyncio

import pytest

from agentscope.exception import DeveloperOrientedException
from agentscope.message import AssistantMsg, UserMsg
from agentscope.sop import SOP, SOPPhase, SOPStep
from agentscope.types import ReplyFinishedReason

from engines.agents.messaging.dialogue import DialogueLog
from engines.agents.tools.tool_serial import LOG_EMPTY
from engines.agents.tools.tool_wrapper import PlatformFunctionTool
from engines.agents.workflow import SopRunner, SopStepInput, SopSteps
from engines.ai.base import ToolSpec

pytestmark = [pytest.mark.unit]


class _Role:
    def __init__(self, agent) -> None:
        self.agent = agent


class _Agent:
    name = "stub"

    async def reply_stream(self, *args, **kwargs):
        if False:
            yield None


class _Verifier:
    name = "verifier"

    async def reply_stream(self, inputs=None, structured_schema=None, yield_final_msg=False):
        if yield_final_msg:
            yield AssistantMsg(
                name="verifier",
                content="通过",
                finished_reason=ReplyFinishedReason.COMPLETED,
                structured_output={"passed": True, "message": ""},
            )


class _Executor:
    name = "executor"

    def __init__(self, failures: list[BaseException]) -> None:
        self.failures = list(failures)
        self.calls = 0

    async def reply_stream(self, inputs=None, structured_schema=None, yield_final_msg=False):
        self.calls += 1
        if self.calls <= len(self.failures):
            raise self.failures[self.calls - 1]
        if yield_final_msg:
            yield AssistantMsg(
                name="executor",
                content="已点击",
                finished_reason=ReplyFinishedReason.COMPLETED,
                structured_output={"handover": "已点击开关"},
            )


def _run(failures: list[BaseException], max_attempts: int) -> SopRunner:
    sop = SopSteps(
        _Role(_Executor(failures)),
        _Role(_Verifier()),
        [SopStepInput("关灯", "日志出现关闭成功")],
        max_attempts=max_attempts,
    ).build()
    runner = SopRunner(sop, model="deepseek-flash", provider="local", dialogue_enabled=False)
    asyncio.run(runner._drive(UserMsg(name="user", content="设备ID")))
    return runner


def test_one_empty_log_does_not_fail_the_run() -> None:
    """上限为 2 时，第一次日志为空只驳回这一次，运行阶段还不是失败。"""
    runner = _run([DeveloperOrientedException(LOG_EMPTY)], max_attempts=2)

    assert runner.phase is not SOPPhase.FAILED
    record = runner.engine.state.steps[0]
    assert record.phase is not SOPPhase.FAILED
    assert record.verifications[0].passed is False
    assert record.verifications[0].message == LOG_EMPTY


def test_empty_logs_fail_the_run_when_attempts_run_out() -> None:
    """连续日志为空达到上限后，由引擎把该步标为失败。"""
    runner = _run(
        [DeveloperOrientedException(LOG_EMPTY), DeveloperOrientedException(LOG_EMPTY)],
        max_attempts=2,
    )

    record = runner.engine.state.steps[0]
    assert runner.phase is SOPPhase.FAILED
    assert record.phase is SOPPhase.FAILED
    assert len(record.verifications) == 2
    assert record.verifications[-1].passed is False
    assert record.verifications[-1].message == LOG_EMPTY


def test_grouped_log_empty_is_one_refusal() -> None:
    """并发工具把异常包进 ExceptionGroup 时，同样只记一次驳回。"""
    grouped = ExceptionGroup("tools", [DeveloperOrientedException(LOG_EMPTY)])
    runner = _run([grouped], max_attempts=2)

    assert runner.phase is not SOPPhase.FAILED
    assert runner.engine.state.steps[0].verifications[0].message == LOG_EMPTY


def test_other_developer_error_still_propagates() -> None:
    """不是「日志为空」的开发异常继续抛出，不改写成步骤失败。"""
    sop = SopSteps(
        _Role(_Executor([DeveloperOrientedException("别的故障")])),
        _Role(_Verifier()),
        [SopStepInput("关灯", "日志出现关闭成功")],
        max_attempts=2,
    ).build()
    runner = SopRunner(sop, model="deepseek-flash", provider="local", dialogue_enabled=False)

    with pytest.raises(DeveloperOrientedException, match="别的故障"):
        asyncio.run(runner._drive(UserMsg(name="user", content="设备ID")))
    assert runner.engine.state.steps[0].phase is SOPPhase.RUNNING


def test_drive_accepts_user_message_factory(tmp_path) -> None:
    """UserMsg 是工厂函数，开跑时仍能把启动输入写进对话稿。"""
    sop = SOP(
        name="device-check",
        description="检查",
        steps=[
            SOPStep(
                subject="关灯",
                description="日志出现关闭成功",
                executor=_Agent(),
                verifier=_Agent(),
                max_attempts=2,
            )
        ],
    )
    runner = SopRunner(sop, model="deepseek-flash", provider="local", dialogue_enabled=False)
    runner.dialogue = DialogueLog(str(tmp_path), run_id="sop-user")

    async def _stream(inputs=None):
        if False:
            yield None

    runner.engine.reply_stream = _stream
    asyncio.run(runner._drive(UserMsg(name="user", content="设备ID是：R5CT62RH88F")))

    text = runner.dialogue.path.read_text(encoding="utf-8")
    assert "设备ID是：R5CT62RH88F" in text


def test_tool_wrapper_turns_log_empty_into_developer_exception() -> None:
    """包装层把「日志为空」抬成框架不会吞掉的异常。"""

    def _empty() -> str:
        raise ValueError(LOG_EMPTY)

    tool = PlatformFunctionTool(ToolSpec(name="check_device_log", handler=_empty, read_only=True))
    with pytest.raises(DeveloperOrientedException, match=LOG_EMPTY):
        asyncio.run(tool.call())


def test_tool_wrapper_keeps_other_value_errors() -> None:
    """其它 ValueError 仍按原样抛出，不中断流程。"""

    def _other() -> str:
        raise ValueError("时间点无法解析")

    tool = PlatformFunctionTool(ToolSpec(name="check_device_log", handler=_other, read_only=True))
    with pytest.raises(ValueError, match="时间点无法解析"):
        asyncio.run(tool.call())
