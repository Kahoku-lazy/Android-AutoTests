from __future__ import annotations

from utils.logs import agent_event_log

__all__ = ["SESSION_MARK", "TurnLogger", "log_event", "mark"]

SESSION_MARK = "单智能体对话"


def _write(text: str) -> None:
    agent_event_log.info(" ".join(str(text or "").split()) or "-")


def mark(session_id: str, stage: str, model: str) -> None:
    if not session_id:
        return
    _write(f"{SESSION_MARK} | {session_id} | {stage} | {model or '-'}")


def log_event(text: str) -> None:
    _write(text)


class TurnLogger:
    def __init__(self) -> None:
        self._thought: dict[str, str] = {}
        self._text: dict[str, str] = {}
        self._tool_name: dict[str, str] = {}
        self._tool_args: dict[str, str] = {}
        self._tool_out: dict[str, str] = {}
        self._tool_media: dict[str, int] = {}

    def feed(self, event: object) -> str:
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
        body = " ".join(str(text or "").split())
        return f"{prefix}：{body}" if body else prefix

    @staticmethod
    def _tool_line(prefix: str, name: str, tool_call_id: str, payload: str, tail: str) -> str:
        head = " ".join(part for part in (name or tool_call_id, tail) if part)
        body = " ".join(str(payload or "").split())
        return f"{prefix} {head} {body}".strip()
