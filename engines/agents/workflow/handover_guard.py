"""
python -m 调试路径: engines.agents.workflow.handover_guard

本模块的业务功能如下：
1. handover_self_declares_incomplete: 判断执行者的 handover 是否自述未完成。
2. IncompleteHandoverGuard: 包装执行者，自述未完成时在原尝试内回灌“继续执行”。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Type

from agentscope.event import RequireExternalExecutionEvent, RequireUserConfirmEvent
from agentscope.message import Msg, UserMsg
from pydantic import BaseModel

from engines.agents.event_log import write_line

# 自述未完成的措辞。“未达成”刻意不收：验收判据本身用“达成/未达成”，执行者逐条汇报会大量出现。
INCOMPLETE_MARKERS = (
    "未完成",
    "尚未",
    "还没",
    "未点击",
    "未执行",
    "部分完成",
    "请下一步",
    "下一步立即",
    "下一步执行",
)

# 同一次尝试里最多退回几次。超过后放行给验收者，避免无限循环。
MAX_HANDOVER_NUDGES = 2

# 回灌给执行者的继续指令。点名命中的措辞，避免它继续用同样的说法收尾。
NUDGE_TEMPLATE = (
    "<system-reminder>你刚交的 handover 里出现了「{marker}」，说明本步还没做完。"
    "这次尝试还没有结束：必须继续执行设备操作，把本步“必须达成的结果”全部做完，再重新交卷。"
    "禁止用“部分完成”“请下一步执行”“尚未…”这类说法收尾。</system-reminder>"
)


def handover_self_declares_incomplete(text: object) -> tuple[bool, str]:
    """
    判断一段 handover 文本是否自述未完成。

    Args:
        text: 执行者写在 handover 里的文本，非字符串按空串处理。

    Returns:
        (是否自述未完成, 命中的措辞)。未命中时措辞为空串。
    """
    raw = str(text or "").strip()
    if not raw:
        return False, ""
    for marker in INCOMPLETE_MARKERS:
        if marker in raw:
            return True, marker
    return False, ""


def _handover_text(final: Msg) -> str:
    """
    取出最终消息里的 handover 文本。

    Args:
        final: 执行者交出的最终消息。

    Returns:
        handover 文本；结构化输出不是字典或没有该字段时返回空串。
    """
    output = getattr(final, "structured_output", None)
    if not isinstance(output, dict):
        return ""
    return str(output.get("handover") or "")


def _schema_has_handover(structured_schema: Type[BaseModel] | None) -> bool:
    """
    这份结构化输出契约里是否有 handover 字段。

    Args:
        structured_schema: 本轮要求的结构化输出模型。

    Returns:
        有 handover 字段返回 True；没有契约或字段时返回 False。
    """
    fields = getattr(structured_schema, "model_fields", None)
    return bool(fields) and "handover" in fields


class IncompleteHandoverGuard:
    """
    执行者包装：把“自述未完成”的 handover 退回，让同一次尝试继续做完。

    只实现 SOP 需要的 AgentLike 最小面（name / model / reply_stream），
    事件原样透传，最终消息只在本次尝试真正结束时交给步骤。

    Attributes:
        nudges: 已发生的退回次数，供日志与测试观察。

    Raises:
        TypeError: 内层对象没有 reply_stream。
    """

    def __init__(self, agent: object, *, max_nudges: int = MAX_HANDOVER_NUDGES) -> None:
        """
        记录内层执行者与退回上限。

        Args:
            agent: 被包装的执行者，需提供 reply_stream。
            max_nudges: 同一次尝试里最多退回几次。

        Raises:
            TypeError: 内层对象没有可调用的 reply_stream。
        """
        if not callable(getattr(agent, "reply_stream", None)):
            raise TypeError("IncompleteHandoverGuard 需要一个提供 reply_stream 的执行者")
        self._agent = agent
        self._max_nudges = max(0, int(max_nudges))
        self.nudges = 0

    @property
    def name(self) -> str:
        """内层执行者名字；没有时用 executor。"""
        return str(getattr(self._agent, "name", "") or "executor")

    @property
    def model(self):
        """内层执行者的模型对象，供运行汇总取模型名。"""
        return getattr(self._agent, "model", None)

    async def reply_stream(
        self,
        inputs: object = None,
        structured_schema: Type[BaseModel] | None = None,
        yield_final_msg: bool = False,
    ) -> AsyncGenerator[object, None]:
        """
        跑一次尝试：命中未完成措辞就回灌继续指令，直到交出的 handover 不再自述未完成。

        Args:
            inputs: 步骤交给执行者的输入，或退回后要继续的那条指令。
            structured_schema: 本轮要求的结构化输出契约。
            yield_final_msg: 是否把最终消息一并 yield 给步骤。

        Returns:
            异步生成器：过程事件原样透出，最终消息在尝试结束时透出。

        Raises:
            asyncio.CancelledError: 任务被取消时由内层答复抛回，本层不吞。
        """
        current = inputs
        guarded = _schema_has_handover(structured_schema)
        for attempt in range(self._max_nudges + 1):
            final: Msg | None = None
            async for event in self._agent.reply_stream(
                inputs=current,
                structured_schema=structured_schema,
                yield_final_msg=True,
            ):
                if isinstance(event, Msg):
                    final = event
                    continue
                yield event
                if isinstance(event, (RequireUserConfirmEvent, RequireExternalExecutionEvent)):
                    # 需要外部应答：交给步骤停车，本轮不再回灌。
                    return
            if final is None:
                return
            incomplete, marker = handover_self_declares_incomplete(_handover_text(final))
            if not guarded or not incomplete or attempt >= self._max_nudges:
                if yield_final_msg:
                    yield final
                return
            self.nudges += 1
            model_name = str(getattr(self.model, "model", "") or "-")
            write_line(
                model_name,
                f"handover 自述未完成（命中「{marker}」），第 {self.nudges} 次退回继续执行",
            )
            current = UserMsg(name="sop", content=NUDGE_TEMPLATE.format(marker=marker))
