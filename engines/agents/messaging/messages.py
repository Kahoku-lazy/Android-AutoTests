"""
python -m 调试路径: engines.agents.messaging.messages

本模块的业务功能如下：
1. ReplyStreamParser: 从流式模型调用结束事件解析用量三元组。
2. AgentEventsShow: 把事件流写成文本日志，并把结构化记录交给接收方。
"""

from __future__ import annotations

from utils.logs import agent_event_log

from ..event_log import write_line
from ..event_sink import current_sink
from .fold import step

__all__ = [
    "AgentEventsShow",
    "ReplyStreamParser",
]


def _token_triple(input_tokens, output_tokens, cache_hit_tokens) -> tuple[int, int, int]:
    """把三项用量收成整数三元组。空值按 0。不读取缓存写入 token。"""
    return (
        int(input_tokens or 0),
        int(output_tokens or 0),
        int(cache_hit_tokens or 0),
    )


class ReplyStreamParser:
    """从 `reply_stream` 的单条事件解析用量。"""

    def tokens(self, event) -> tuple[int, int, int] | None:
        """读取一条模型调用结束事件上的用量。

        Args:
            event: `reply_stream` 产出的一条事件。

        Returns:
            类名为 `ModelCallEndEvent` 时返回 (输入 token, 输出 token, 缓存命中 token)，
            字段缺失或为 0 时为 (0, 0, 0)。其它事件返回 None。
        """
        if type(event).__name__ != "ModelCallEndEvent":
            return None
        return _token_triple(
            getattr(event, "input_tokens", 0),
            getattr(event, "output_tokens", 0),
            getattr(event, "cache_input_tokens", 0),
        )


class AgentEventsShow:
    """把事件流写成文本日志，并把同一份折叠结果交给接收方。"""

    @staticmethod
    def show(event, buf: dict, models: dict[str, str] | None = None) -> None:
        """折叠一条事件：先写文本日志，再把记录交给当前接收方。

        Args:
            event: AgentScope 事件流里的一条事件。
            buf: 增量累积器。块碎片、工具入参与返回、本轮模型名和起点都攒在这里。
            models: 角色名到模型名。发言开始早于模型调用，用它填「开始」行。

        Returns:
            None。接收方失败时只记警告。
        """
        result = step(event, buf, models)
        for model, action in result.log_lines:
            write_line(model, action)
        try:
            sink = current_sink()
            for record in result.records:
                sink.emit(record, record.image_b64)
        except Exception as exc:
            agent_event_log.warning(f"事件接收方失败：{type(exc).__name__}: {exc}")
