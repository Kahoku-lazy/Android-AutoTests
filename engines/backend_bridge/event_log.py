"""
文件名: ➡️ event_log.py 🏁
路径: ➡️ engines/backend_bridge/event_log.py 🏁
模块功能：➡️ 把平台一轮对话的过程写进前端事件面板读的那份日志（全量颗粒度） 🏁
Python 调试：➡️ python -m engines.backend_bridge.event_log 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. SESSION_MARK: 会话分段标记，必须与引擎侧 event_tail 的同名常量一致（有单测守护）。
2. TurnLogger: 一轮对话的过程记录器——增量先在内存累积，块结束时按全量写出。
3. 全量口径：思考全文、阶段结论全文、工具入参与输出全文都进日志，不截断。
🏁
关联模块：➡️
1. utils.logs: 导入 agent_event_log，与引擎侧共用同一份事件日志。
2. 分段标记与历史引擎侧实现保持一致；引擎侧已退役（变更 retire-engines-agents）。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from utils.logs import agent_event_log

__all__ = ["SESSION_MARK", "TurnLogger", "log_event", "mark"]

# 与 engines/agents/workflow/single/event_tail.py 的 SESSION_MARK 必须一致；
# 前端事件面板按这一标记切段，改一处不改另一处会让面板读不到平台会话。
SESSION_MARK = "单智能体对话"


def _write(text: str) -> None:
    """
    写一行到事件日志，换行折叠成空格保证一行一条。

    Args:
        text: 这一行的正文；空串写成 `-`。
    """
    agent_event_log.info(" ".join(str(text or "").split()) or "-")


def mark(session_id: str, stage: str, model: str) -> None:
    """
    写会话分段标记。

    Args:
        session_id: 前端本次对话的连接键；空串时不写。
        stage: `开始` 或 `结束`。
        model: 本次使用的模型名；空串写成 `-`。
    """
    if not session_id:
        return
    _write(f"{SESSION_MARK} | {session_id} | {stage} | {model or '-'}")


def log_event(text: str) -> None:
    """
    写一条过程行。

    Args:
        text: 过程描述。
    """
    _write(text)


class TurnLogger:
    """
    一轮对话的过程记录器。

    增量事件先在内存累积到各自块上，块结束时整段写出；其余关键节点即时写出。
    同一实例只服务一轮，轮末由调用方丢弃。
    """

    def __init__(self) -> None:
        """初始化累积缓冲。"""
        self._thought: dict[str, str] = {}
        self._text: dict[str, str] = {}
        self._tool_name: dict[str, str] = {}
        self._tool_args: dict[str, str] = {}
        self._tool_out: dict[str, str] = {}
        self._tool_media: dict[str, int] = {}

    def feed(self, event: object) -> str:
        """
        吃一个事件，返回要写进日志的一行（不需要写时返回空串）。

        真实事件里 `ToolCallEndEvent` 与 `ToolResultEndEvent` 不带名字与负载，
        两者只能靠开始事件与增量累积，所以这里按 id 缓冲。

        Args:
            event: 事件对象。

        Returns:
            过程描述；增量与无需记录的事件返回空串。
        """
        kind = type(event).__name__
        if kind == "ThinkingBlockDeltaEvent":
            key = str(getattr(event, "block_id", ""))
            self._thought[key] = self._thought.get(key, "") + str(getattr(event, "delta", ""))
            return ""
        if kind == "ThinkingBlockEndEvent":
            key = str(getattr(event, "block_id", ""))
            return self._with_prefix("思考", self._thought.pop(key, ""))
        if kind == "TextBlockDeltaEvent":
            key = str(getattr(event, "block_id", ""))
            self._text[key] = self._text.get(key, "") + str(getattr(event, "delta", ""))
            return ""
        if kind == "TextBlockEndEvent":
            key = str(getattr(event, "block_id", ""))
            text = self._text.pop(key, "") or str(getattr(event, "text", "") or "")
            return self._with_prefix("回复", text)
        if kind == "ModelCallStartEvent":
            return f"调用模型 {getattr(event, 'model_name', '')}"
        if kind == "ModelCallEndEvent":
            return (
                f"模型返回 输入 {getattr(event, 'input_tokens', 0)}"
                f" 输出 {getattr(event, 'output_tokens', 0)}"
                f" 缓存命中 {getattr(event, 'cache_input_tokens', 0)}"
            )
        if kind in {"ToolCallStartEvent", "ToolResultStartEvent"}:
            key = str(getattr(event, "tool_call_id", ""))
            self._tool_name[key] = str(getattr(event, "tool_call_name", "") or "")
            return ""
        if kind == "ToolCallDeltaEvent":
            key = str(getattr(event, "tool_call_id", ""))
            self._tool_args[key] = self._tool_args.get(key, "") + str(getattr(event, "delta", ""))
            return ""
        if kind == "ToolResultTextDeltaEvent":
            key = str(getattr(event, "tool_call_id", ""))
            self._tool_out[key] = self._tool_out.get(key, "") + str(getattr(event, "delta", ""))
            return ""
        if kind == "ToolResultDataDeltaEvent":
            key = str(getattr(event, "tool_call_id", ""))
            self._tool_media[key] = self._tool_media.get(key, 0) + 1
            return ""
        if kind == "ToolCallEndEvent":
            key = str(getattr(event, "tool_call_id", ""))
            return self._tool_line(
                "工具入参", self._tool_name.get(key, ""), key, self._tool_args.pop(key, ""), ""
            )
        if kind == "ToolResultEndEvent":
            key = str(getattr(event, "tool_call_id", ""))
            media = self._tool_media.pop(key, 0)
            note = f"（含 {media} 张图片）" if media else ""
            return self._tool_line(
                "工具结果",
                self._tool_name.get(key, ""),
                key,
                self._tool_out.pop(key, ""),
                str(getattr(event, "state", "") or "") + note,
            )
        if kind == "HintBlockEvent":
            return self._with_prefix("运行时提示", str(getattr(event, "hint", "") or ""))
        if kind == "ReplyEndEvent":
            return f"本轮结束（{getattr(event, 'finished_reason', '')}）"
        return ""

    @staticmethod
    def _with_prefix(prefix: str, text: str) -> str:
        """
        拼「前缀：正文」的行。

        Args:
            prefix: 行前缀。
            text: 正文。

        Returns:
            拼好的行；正文为空时只留前缀。
        """
        body = " ".join(str(text or "").split())
        return f"{prefix}：{body}" if body else prefix

    @staticmethod
    def _tool_line(prefix: str, name: str, tool_call_id: str, payload: str, tail: str) -> str:
        """
        拼工具入参或结果的行：工具名 + 负载全文 + 尾部（状态或图片数）。

        Args:
            prefix: `工具入参` 或 `工具结果`。
            name: 工具名；取不到时退回调用 id。
            tool_call_id: 工具调用标识。
            payload: 参数或输出的全文。
            tail: 追加在末尾的状态说明。

        Returns:
            一行过程描述。
        """
        head = " ".join(part for part in (name or tool_call_id, tail) if part)
        body = " ".join(str(payload or "").split())
        return f"{prefix} {head} {body}".strip()
