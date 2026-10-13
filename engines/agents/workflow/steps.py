"""SOP 步骤：执行动作与验收结果，装配成可反复运行的流程。"""

from __future__ import annotations

from collections.abc import Sequence

from agentscope.event import (
    ExternalExecutionResultEvent,
    UserConfirmResultEvent,
    UserInterruptEvent,
)
from agentscope.exception import DeveloperOrientedException
from agentscope.message import Msg, TextBlock, UserMsg
from agentscope.sop import SOP, SOPStep, SOPStepRunState

from ..role.base import BaseRole
from ..tools.tool_serial import LOG_EMPTY
from .context_trim import KEEP_SCREENSHOT_STEPS, trim_agent_context


class SopStepInput:
    """一步的输入：执行动作，以及验收要核对的结果。"""

    def __init__(self, subject: str, description: str) -> None:
        self.subject = str(subject or "")
        self.description = str(description or "")


class SopSteps:
    """把已启动的执行角色、验收角色和步骤输入装配成一份 SOP。"""

    def __init__(
        self,
        executor: BaseRole,
        verifier: BaseRole,
        steps: Sequence[SopStepInput],
        *,
        name: str = "device-check",
        max_attempts: int = 3,
    ) -> None:
        self.executor = executor
        self.verifier = verifier
        self.steps = list(steps)
        self.name = name
        self.max_attempts = max_attempts

    def build(self) -> SOP:
        """校验输入并返回流程定义。

        Returns:
            不保存运行状态的 SOP，可反复用于多次运行。

        Raises:
            ValueError: 步骤列表为空，或某步缺少短名、必须达成的结果。
            RuntimeError: 执行角色或验收角色还没 start()。
        """
        if not self.steps:
            raise ValueError("步骤列表为空，无法装配")
        for item in self.steps:
            if not item.subject.strip() or not item.description.strip():
                raise ValueError("步骤动作和要核对的结果都不能为空")
        worker = _require_agent(self.executor, "执行")
        judge = _require_agent(self.verifier, "验收")
        return SOP(
            name=self.name,
            description="按里程碑逐个验收的设备 UI 检查流程",
            steps=[
                _CheckedStep(
                    subject=item.subject,
                    description=item.description,
                    executor=worker,
                    verifier=judge,
                    max_attempts=self.max_attempts,
                )
                for item in self.steps
            ],
        )


class _CheckedStep(SOPStep):
    """标准执行加验收。日志为空时把这一次尝试记成驳回，再交还引擎。"""

    def _brief(
        self,
        inputs: Msg
        | list[Msg]
        | UserConfirmResultEvent
        | UserInterruptEvent
        | ExternalExecutionResultEvent
        | None,
        state: SOPStepRunState,
    ) -> list[Msg] | UserConfirmResultEvent | UserInterruptEvent | ExternalExecutionResultEvent:
        """问执行角色这一步的动作。驳回说明只加在这里。

        Args:
            inputs: 本步开场输入；挂起恢复事件原样交回。
            state: 这一步已经记下的结论。

        Returns:
            交给执行角色的消息，或尚未结束的恢复事件。
        """
        if inputs is not None and not isinstance(inputs, (Msg, list)):
            return inputs

        text = f"<system-reminder>You are running one step of the SOP.\n\n## {self.subject}\n\n"
        if state.verifications:
            last = state.verifications[-1]
            text += (
                f"\nYour last attempt was not accepted:\n{last.message}\n"
                f"This is attempt {len(state.verifications) + 1} of "
                f"{self.max_attempts}."
            )
        text += "</system-reminder>"
        brief = UserMsg(name="sop", content=text)
        if inputs is None:
            return [brief]
        return [brief, *(inputs if isinstance(inputs, list) else [inputs])]

    def _question(
        self,
        inputs: Msg
        | list[Msg]
        | UserConfirmResultEvent
        | UserInterruptEvent
        | ExternalExecutionResultEvent
        | None,
        state: SOPStepRunState,
    ) -> list[Msg] | UserConfirmResultEvent | UserInterruptEvent | ExternalExecutionResultEvent:
        """问验收角色这一步要核对的结果，并附上执行者交出的内容。

        Args:
            inputs: 挂起恢复事件；有则原样交回，不再包一层提示。
            state: 这一步收到的输入和执行者交接。

        Returns:
            交给验收角色的消息，或尚未结束的恢复事件。
        """
        if inputs is not None:
            return inputs
        return [
            UserMsg(
                name="sop",
                content=(
                    "<system-reminder>Judge the work below against what "
                    f"this step had to prove.\n\n{self.description}</system-reminder>"
                ),
            ),
            *state.given,
            UserMsg(
                name="sop",
                content=[
                    TextBlock(text="<submission>"),
                    *(state.submission or []),
                    TextBlock(text="</submission>"),
                ],
            ),
        ]

    async def reply_stream(self, inputs, state: SOPStepRunState):
        """做一次尝试。日志为空时记下未通过并结束这次尝试。"""
        self._trim_context(inputs, state)
        try:
            async for event in super().reply_stream(inputs, state):
                yield event
        except BaseExceptionGroup as exc:
            message = _log_empty_message(exc)
            if message is None:
                raise
            self.record(state, False, message, "sop")
        except DeveloperOrientedException as exc:
            if exc.message != LOG_EMPTY:
                raise
            self.record(state, False, exc.message, "sop")

    def _trim_context(self, inputs, state: SOPStepRunState) -> None:
        """新的一次执行开始前，只留最近几步截图，更早步骤收成文字结论。

        挂起恢复和验收半程不裁：那一次尝试还没结束，截图仍是当前证据。
        """
        if state.submission is not None or not isinstance(inputs, (Msg, list, type(None))):
            return
        trim_agent_context(
            self.executor,
            f"exec:{self.subject.strip()}",
            keep_steps=KEEP_SCREENSHOT_STEPS,
        )
        if self.verifier is not None:
            trim_agent_context(
                self.verifier,
                f"ver:{self.description.strip()}",
                keep_steps=KEEP_SCREENSHOT_STEPS,
            )


def _require_agent(role: BaseRole, label: str):
    """取出角色内部的 Agent。

    Args:
        role: 已 start() 的角色对象。
        label: 报错时用的角色称谓。

    Returns:
        AgentScope Agent。

    Raises:
        RuntimeError: 角色还没调用 start()。
    """
    if role.agent is None:
        raise RuntimeError(f"{label}角色还没 start()，无法装进 SOP")
    return role.agent


def _log_empty_message(exc: BaseException) -> str | None:
    """从异常里取出「日志为空」；没有则返回 None。

    Args:
        exc: 工具抛出的异常，可能包在 ExceptionGroup 里。

    Returns:
        命中时返回「日志为空」，否则返回 None。
    """
    if isinstance(exc, DeveloperOrientedException) and exc.message == LOG_EMPTY:
        return exc.message
    if isinstance(exc, BaseExceptionGroup):
        for item in exc.exceptions:
            found = _log_empty_message(item)
            if found is not None:
                return found
    return None
