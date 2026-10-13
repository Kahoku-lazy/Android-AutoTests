"""SOP 步骤层：把「执行 + 验收 + 最多驳回 max_attempts 次」接进 AgentScope SOP。

`ExecutionSOPContext` 携带本步的平台依赖（回调 + 关键词）；
`ExecutorAdapter` / `VerifierAdapter` 把工作流的一次执行 / 一次验收包成框架要的 `AgentLike`
（只暴露 `reply_stream`），交付与结论按框架契约给出；`StepAttemptSink` 是本轮尝试的产出槽
（执行者写、验证者补、工作流在尝试结束时读）；`ExecutionSOPStep` 覆盖「问什么」两处文案钩子，
编排由 `SOPEngine` 推进。
"""

from __future__ import annotations

import json
import logging

from dataclasses import dataclass
from typing import Callable, ClassVar

from agentscope.message import AssistantMsg, Msg, UserMsg
from agentscope.sop import SOPStep, SOPStepRunState
from agentscope.types import ReplyFinishedReason

logger = logging.getLogger("ai_assistant.workflow")


# ── 平台上下文 ──


@dataclass
class ExecutionSOPContext:
    """一个执行步骤的平台依赖（工作流在每步开始前注入一次）。

    Attributes:
        index: 步骤序号（1 起）。
        total: 总步骤数。
        detail: planner 拆出的步骤（`Step`，按鸭子类型使用）。
        serial: 目标设备 serial。
        execute_step: 执行一步的调用点。
        verify_step: 验收一步的调用点。
        open_window: 动作前开日志窗，返回窗口 id（无提供者时空串）。
        close_window: 动作后读窗，返回证据块（无窗口 / 失败时 None）。
        action_times: 取本步副作用动作发出时刻（读窗基准）。
        build_log_check: 组装执行侧点击证据块。
        save_screenshot: 验证截图回退落盘（verifier 没回路径时用）。
        log_keywords: 当前日志关键词表文本（空 = 不附）。
    """

    index: int
    total: int
    detail: object
    serial: str
    execute_step: Callable
    verify_step: Callable
    open_window: Callable
    close_window: Callable
    action_times: Callable
    build_log_check: Callable
    save_screenshot: Callable
    log_keywords: str = ""


@dataclass
class StepAttemptSink:
    """本轮尝试产出的平台事实（执行者写、验证者补、工作流读）。

    Attributes:
        loop: 第几次尝试（1 起）。
        retry_hint: 上次驳回原因回灌给执行者的提示（空串 = 首次）。
        window_id: 动作前开的日志窗 id（空串 = 无窗口）。
        exec_out: 执行结果三字段。
        exec_screenshot: 执行回复里的截图块。
        exec_role: 执行角色的返回（点击证据与动作时刻的取数源）。
        verdict: 验收结论。
        screenshot: 本轮验收证据截图相对路径（取不到时空串）。
        executor_log_check: 执行侧点击证据块。
        log_evidence: 本轮设备日志证据块。
        usage_before: 本轮开始前的用量基线。
    """

    loop: int = 1
    retry_hint: str = ""
    window_id: str = ""
    exec_out: object = None
    exec_screenshot: object = None
    exec_role: object = None
    verdict: object = None
    screenshot: str = ""
    executor_log_check: dict | None = None
    log_evidence: dict | None = None
    usage_before: dict | None = None

    def reset(self, loop: int) -> None:
        """开一轮新尝试：设定轮次，其余事实清空。"""
        self.loop = loop
        self.retry_hint = ""
        self.window_id = ""
        self.exec_out = None
        self.exec_screenshot = None
        self.exec_role = None
        self.verdict = None
        self.screenshot = ""
        self.executor_log_check = None
        self.log_evidence = None


# ── AgentLike 适配器 ──


class ExecutorAdapter:
    """执行者适配器：把工作流的一次执行包成框架要的 `AgentLike`。

    一次调用 = 本步的一次尝试：动作前开日志窗 → 交给工作流执行 → 记下本轮产出。
    """

    name: ClassVar[str] = "executor"

    def __init__(self, context: ExecutionSOPContext, sink: StepAttemptSink):
        self._ctx = context
        self._sink = sink

    async def reply_stream(
        self,
        inputs=None,
        structured_schema=None,
        yield_final_msg: bool = False,
    ):
        """做一次本步的执行，交出交付文本。

        Args:
            inputs: 框架派发的输入（只从中取回灌的驳回原因）。
            structured_schema: 框架要求的交付 schema（`_Handover`，本适配器不读）。
            yield_final_msg: 是否在末尾交出最终消息。

        Yields:
            `Msg`: 交付文本挂在 `structured_output["handover"]`。
        """
        del structured_schema
        ctx, sink = self._ctx, self._sink
        sink.retry_hint = retry_hint_from(inputs)
        sink.window_id = ctx.open_window(ctx.index)
        exec_out, screenshot, role = await ctx.execute_step(
            ctx.detail, ctx.index, ctx.total, sink.retry_hint
        )
        sink.exec_out, sink.exec_screenshot, sink.exec_role = exec_out, screenshot, role
        if yield_final_msg:
            yield _handover_msg(exec_out)


class VerifierAdapter:
    """验证者适配器：把工作流的一次验收包成框架要的 `AgentLike`。

    消费上一步交付与平台装配的证据块，调验收角色，把 PASS / FAIL 映射成框架结论。
    """

    name: ClassVar[str] = "verifier"

    def __init__(self, context: ExecutionSOPContext, sink: StepAttemptSink):
        self._ctx = context
        self._sink = sink

    async def reply_stream(
        self,
        inputs=None,
        structured_schema=None,
        yield_final_msg: bool = False,
    ):
        """验收一次本步的执行，交出结论。

        Args:
            inputs: 框架派发的输入（本适配器不消费）。
            structured_schema: 框架要求的结论 schema（`_Verdict`，本适配器不读）。
            yield_final_msg: 是否在末尾交出最终消息。

        Yields:
            `Msg`: 结论挂在 `structured_output`（`{"passed", "message"}`）。
        """
        del inputs, structured_schema
        ctx, sink = self._ctx, self._sink
        sink.log_evidence = close_evidence(ctx, sink)
        sink.executor_log_check = record_executor_log_check(ctx, sink)
        verdict, verifier_shot, role = await ctx.verify_step(
            ctx.detail,
            ctx.index,
            ctx.total,
            sink.exec_out,
            sink.exec_screenshot,
            sink.log_evidence,
        )
        shot_rel = (getattr(role, "screenshot_path", "") or "").strip()
        if not shot_rel:
            # 回退：从 DataBlock 再落一份 ai_tasks/ 证据
            shot_rel = ctx.save_screenshot(
                ctx.index,
                sink.loop,
                verifier_shot if verifier_shot is not None else sink.exec_screenshot,
            )
        sink.verdict, sink.screenshot = verdict, shot_rel
        if yield_final_msg:
            yield _verdict_msg(verdict)


# ── 步骤 ──


class ExecutionSOPStep(SOPStep):
    """「执行 + 验收 + 最多驳回 max_attempts 次」的 SOP 步骤，接本平台的证据装配。

    只覆盖两处文案钩子：`_brief` 只回灌驳回原因（执行侧输入前缀由 `ExecutorRole` 自己拼）；
    `_question` 不把交付文本塞进验收输入（验收输入由平台按证据装配）。
    编排由 `SOPEngine` 负责。
    """

    def __init__(
        self,
        subject: str,
        description: str,
        context: ExecutionSOPContext,
        max_attempts: int = 3,
    ) -> None:
        """Args:
        subject: 步骤标识（进度事件与日志用）。
        description: 这一步要证明什么（断言）。
        context: 本步的平台上下文。
        max_attempts: 本步最多驳回次数。
        """
        self.context = context
        self.sink = StepAttemptSink()
        super().__init__(
            subject,
            description,
            ExecutorAdapter(context, self.sink),
            VerifierAdapter(context, self.sink),
            max_attempts,
        )

    def prepare(self, context: ExecutionSOPContext) -> None:
        """刷新本步的平台上下文（工作流在每步开始前调用）。"""
        self.context = context
        self.sink = StepAttemptSink()
        self.executor = ExecutorAdapter(context, self.sink)
        self.verifier = VerifierAdapter(context, self.sink)
        logger.info(
            "【② SOP 步骤 %d/%d】action=%r assert=%r max_attempts=%d",
            context.index,
            context.total,
            getattr(context.detail, "action", ""),
            getattr(context.detail, "assertion", ""),
            self.max_attempts,
        )

    def _brief(self, inputs, state: SOPStepRunState):  # noqa: ANN001 - 框架钩子
        """执行侧输入：只补平台口径的重试提示（驳回原因回灌）。"""
        del inputs
        last = state.verifications[-1] if state.verifications else None
        reason = (last.message if last is not None else "") or ""
        attempt = len(state.verifications) + 1
        text = (
            f"<feedback>上次执行未通过验收，请修正后重做：\n{reason}</feedback>" if reason else ""
        )
        return [UserMsg(name="sop", content=f"第 {attempt}/{self.max_attempts} 次尝试。{text}")]

    def _question(self, inputs, state: SOPStepRunState):  # noqa: ANN001 - 框架钩子
        """验收侧输入：原样返回框架派发的 inputs（交付文本不进验收输入）。"""
        return inputs if inputs is not None else []


# ── 辅助 ──


def retry_hint_from(inputs) -> str:  # noqa: ANN001 - 框架派发的输入
    """从框架派发的输入里取本平台回灌的重试提示；取不到返回空串。

    只认平台写入的 feedback 段，框架自带的英文提醒不算。
    """
    for msg in inputs if isinstance(inputs, list) else [inputs]:
        content = getattr(msg, "content", None)
        for block in content if isinstance(content, list) else []:
            text = getattr(block, "text", "") or ""
            if "<feedback>" not in text:
                continue
            body = text.split("<feedback>", 1)[1].split("</feedback>", 1)[0]
            return body.split("：", 1)[-1].strip()
    return ""


def close_evidence(ctx: ExecutionSOPContext, sink: StepAttemptSink) -> dict | None:
    """读窗取证据（以本步全部动作时刻为基准）；无窗口时返回 None。"""
    if not sink.window_id:
        return None
    return ctx.close_window(ctx.index, sink.window_id, ctx.action_times(sink.exec_role))


def record_executor_log_check(ctx: ExecutionSOPContext, sink: StepAttemptSink) -> dict:
    """执行侧点击证据：点击前时间点 + 点击后截图路径（+ 需日志时的同一份窗口证据）。"""
    need_log = bool(getattr(ctx.detail, "log_check", False))
    return ctx.build_log_check(sink.exec_role, sink.log_evidence, need_log)


def handover_text(exec_out) -> str:  # noqa: ANN001 - 只读 model_dump
    """交付文本：执行三字段的 JSON。"""
    return json.dumps({"execution": exec_out.model_dump()}, ensure_ascii=False)


def _handover_msg(exec_out) -> Msg:  # noqa: ANN001 - 只读 model_dump
    """框架要求的最终消息：交付文本挂在 `structured_output["handover"]`。"""
    return AssistantMsg(
        name="executor",
        content="已执行本步操作。",
        finished_reason=ReplyFinishedReason.COMPLETED,
        structured_output={"handover": handover_text(exec_out)},
    )


def verdict_payload(verdict) -> dict:  # noqa: ANN001 - 只读字段
    """框架结论：是否通过 + 说明（说明取验收结论的 actual）。"""
    return {"passed": verdict.result == "PASS", "message": verdict.actual}


def _verdict_msg(verdict) -> Msg:  # noqa: ANN001 - 只读字段
    """框架要求的最终消息：结论挂在 `structured_output`。"""
    return AssistantMsg(
        name="verifier",
        content="已给出本步验收结论。",
        finished_reason=ReplyFinishedReason.COMPLETED,
        structured_output=verdict_payload(verdict),
    )
