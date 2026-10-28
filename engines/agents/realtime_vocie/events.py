"""
python -m 调试路径: engines.agents.realtime_vocie.events

本模块的业务功能如下：
1. VoiceLogSink: 引擎对对话日志写入方的最小协议（message / event）。
2. TranscriptBridge: 把 AgentScope 的 AgentEvent 翻译成前端线格式，并落最终文本。

桥接层只做事件翻译与落日志，不持有模型或传输；日志写入方由调用方注入，
因此引擎不依赖 backend.apps。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agentscope.event import (
    ModelCallEndEvent,
    ModelCallStartEvent,
    ReplyEndEvent,
    ReplyStartEvent,
    TextBlockDeltaEvent,
    TextBlockEndEvent,
)
from agentscope.types import ReplyFinishedReason


class VoiceLogSink(Protocol):
    """对话日志写入方需要提供的最小能力。"""

    @property
    def session_id(self) -> str:
        """本次会话 id。"""

    @property
    def display_path(self) -> str:
        """可展示给用户的日志路径。"""

    def message(self, role: str, text: str, reply_id: str = "") -> None:
        """写入一条最终对话消息。"""

    def event(self, name: str, **fields: object) -> None:
        """写入一条会话事件。"""


@dataclass
class _PendingMessage:
    """一条正在收尾的消息。"""

    role: str
    text: str = ""
    logged: bool = False


class TranscriptBridge:
    """
    把 AgentScope 事件翻译成浏览器可消费的消息。

    Attributes:
        log: 本次会话的对话日志写入方。
    """

    def __init__(self, log: VoiceLogSink, model: str = "") -> None:
        """
        初始化桥接器。

        Args:
            log: 本次会话的对话日志写入方。
            model: 当前实时模型名，写入用量事件。
        """
        self.log = log
        self.model = model
        self._messages: dict[str, _PendingMessage] = {}
        self._state = ""
        self.usage_input = 0
        self.usage_output = 0
        self.usage_cache_input = 0
        self.usage_cache_creation = 0

    def handle(self, event: object) -> list[dict]:
        """
        处理一个 AgentScope 事件，返回要发给浏览器的消息列表。

        Args:
            event: AgentScope 的 AgentEvent。

        Returns:
            零到多条线格式消息；无法识别的事件返回空列表。
        """
        if isinstance(event, ReplyStartEvent):
            payloads = self._on_reply_start(event)
        elif isinstance(event, TextBlockDeltaEvent):
            payloads = self._on_text_delta(event)
        elif isinstance(event, TextBlockEndEvent):
            payloads = self._on_text_end(event)
        elif isinstance(event, ReplyEndEvent):
            payloads = self._on_reply_end(event)
        elif isinstance(event, ModelCallStartEvent):
            # _start_reply 先发 ReplyStart（speaking）再发 ModelCallStart；
            # 后者不能再把状态压回 thinking，否则用户会看到「说话中 → 思考中」抖动。
            payloads = [] if self._state == "speaking" else [self._state_event("thinking")]
        elif isinstance(event, ModelCallEndEvent):
            payloads = self._on_model_usage(event)
        else:
            return []
        return [payload for payload in payloads if not payload.get("unchanged")]

    def _on_reply_start(self, event: ReplyStartEvent) -> list[dict]:
        """打开一条用户/助手消息。"""
        message = self._ensure(event.reply_id, event.role)
        payload = {
            "type": "reply_start",
            "reply_id": event.reply_id,
            "role": message.role,
            "name": event.name,
        }
        if message.role == "user":
            self.log.event("vad_start", reply_id=event.reply_id)
        state = "listening" if message.role == "user" else "speaking"
        return [payload, self._state_event(state)]

    def _on_model_usage(self, event: ModelCallEndEvent) -> list[dict]:
        """记录一次模型调用的 token 用量；全 0 时不写伪造记录。"""
        if not any(
            (
                event.input_tokens,
                event.output_tokens,
                event.cache_input_tokens,
                event.cache_creation_input_tokens,
            ),
        ):
            return []
        self.usage_input += event.input_tokens
        self.usage_output += event.output_tokens
        self.usage_cache_input += event.cache_input_tokens
        self.usage_cache_creation += event.cache_creation_input_tokens
        self.log.event(
            "model_usage",
            provider="dashscope",
            category="Realtime",
            model=self.model,
            reply_id=event.reply_id,
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
            cache_input_tokens=event.cache_input_tokens,
            cache_creation_input_tokens=event.cache_creation_input_tokens,
        )
        return []

    def _on_text_delta(self, event: TextBlockDeltaEvent) -> list[dict]:
        """追加一段文本增量。"""
        message = self._ensure(event.reply_id, "assistant")
        message.text += event.delta
        return [
            {
                "type": "transcript_delta",
                "reply_id": event.reply_id,
                "role": message.role,
                "delta": event.delta,
            },
        ]

    def _on_text_end(self, event: TextBlockEndEvent) -> list[dict]:
        """收敛文本块并落日志。"""
        message = self._ensure(event.reply_id, "assistant")
        if event.text is not None:
            message.text = event.text
        self._log_message(event.reply_id, message)
        return [
            {
                "type": "transcript_final",
                "reply_id": event.reply_id,
                "role": message.role,
                "text": message.text,
            },
        ]

    def _on_reply_end(self, event: ReplyEndEvent) -> list[dict]:
        """结束一条回复，切换状态并按需补落日志。"""
        message = self._messages.get(event.reply_id)
        role = message.role if message is not None else "assistant"
        reason = getattr(event.finished_reason, "value", event.finished_reason)
        payloads: list[dict] = [
            {
                "type": "reply_end",
                "reply_id": event.reply_id,
                "role": role,
                "reason": str(reason),
            },
        ]
        if message is not None:
            self._log_message(event.reply_id, message)

        error = _error_message(event.error)
        if error:
            payloads.append({"type": "error", "message": error})

        if role == "user":
            self.log.event("vad_end", reply_id=event.reply_id, reason=str(reason))
            payloads.append(self._state_event("thinking"))
        elif event.finished_reason == ReplyFinishedReason.ERROR:
            payloads.append(self._state_event("error"))
        else:
            payloads.append(self._state_event("listening"))
        return payloads

    def flush(self) -> None:
        """会话结束时补写尚未收尾的消息（用户中途结束 / 通道断开）。"""
        for reply_id, message in self._messages.items():
            self._log_message(reply_id, message)

    def _ensure(self, reply_id: str, role: str) -> _PendingMessage:
        """取得或创建一条消息状态。"""
        message = self._messages.get(reply_id)
        if message is None:
            message = _PendingMessage(role=role)
            self._messages[reply_id] = message
        return message

    def _log_message(self, reply_id: str, message: _PendingMessage) -> None:
        """最终文本只落一次日志。"""
        if message.logged or not message.text.strip():
            return
        message.logged = True
        self.log.message(message.role, message.text, reply_id)

    def _state_event(self, value: str) -> dict:
        """生成状态事件；相同状态不重复发送。"""
        if value == self._state:
            return {"type": "state", "value": value, "unchanged": True}
        self._state = value
        return {"type": "state", "value": value}


def _error_message(error: object) -> str:
    """
    从 ReplyEndEvent.error 里提取可读消息。

    Args:
        error: AgentScope 的错误对象或 None。

    Returns:
        可读错误文本；没有错误时返回空字符串。
    """
    if error is None:
        return ""
    message = getattr(error, "message", None)
    if isinstance(message, str) and message:
        return message
    text = str(error).strip()
    return text
