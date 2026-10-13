"""AgentScope 事件流 → 过程记录：实时落盘并汇总思考与工具记录。

思考在 `ThinkingBlockEnd` 整块落一条，工具调用在 `ToolCallEnd` 落一条（含完整入参），
工具返回在 `ToolResultEnd` 落一条（含状态与返回）。只依赖 AgentScope 消息类型与同包的
脱敏函数，不 import 角色包。
"""

from __future__ import annotations

import json
import logging

from .messages import sanitize_tool_output_text, screenshot_path_from_tool_output

logger = logging.getLogger(__name__)

EVENT_THINKING = "思考"
EVENT_TOOL_CALL = "工具调用"
EVENT_TOOL_RESULT = "工具返回"
EVENT_OUTPUT = "输出"
EVENT_MODEL_CALL = "模型调用"
EVENT_IMAGE = "截图"


class EventStreamRecorder:
    """消费一次 `reply_stream` 的事件：边写过程日志，边汇总思考与工具记录。"""

    def __init__(self, log, *, role: str, model: str, scope: str = "") -> None:
        self._log = log
        self._role = str(role or "")
        self._model = str(model or "")
        self._scope = str(scope or "")
        self._thinking_parts: dict[str, list[str]] = {}
        self._call_parts: dict[str, list[str]] = {}
        self._call_names: dict[str, str] = {}
        self._result_parts: dict[str, list[str]] = {}
        # 汇总产物（供角色结果对象使用）
        self.thinking: list[str] = []
        self.tool_usage: list[dict] = []
        self.screenshot_path = ""
        self.model_calls = 0

    # ── 事件入口 ──

    def consume(self, event: object) -> None:
        """处理一个事件；未知事件忽略（不影响执行）。"""
        name = type(event).__name__
        handler = getattr(self, f"_on_{name}", None)
        if handler is None:
            return
        try:
            handler(event)
        except Exception:  # noqa: BLE001 - 记录失败不得打断模型执行
            logger.exception("过程记录失败：事件 %s", name)

    def finish(self) -> None:
        """流结束时兜底：把只收到增量、没收到结束事件的块补记。"""
        for block_id, parts in list(self._thinking_parts.items()):
            self._flush_thinking(block_id, parts)
        for call_id, parts in list(self._call_parts.items()):
            self._flush_tool_call(call_id, parts)
        for call_id, parts in list(self._result_parts.items()):
            self._flush_tool_result(call_id, parts)

    # ── 思考 ──

    def _on_ThinkingBlockDeltaEvent(self, event) -> None:
        self._thinking_parts.setdefault(event.block_id, []).append(str(event.delta or ""))

    def _on_ThinkingBlockEndEvent(self, event) -> None:
        parts = self._thinking_parts.pop(event.block_id, [])
        self._flush_thinking(event.block_id, parts)

    def _flush_thinking(self, block_id: str, parts: list[str]) -> None:
        text = "".join(parts).strip()
        if not text:
            return
        self.thinking.append(text)
        self._write(EVENT_THINKING, text)

    # ── 工具调用 ──

    def _on_ToolCallStartEvent(self, event) -> None:
        self._call_names[event.tool_call_id] = str(event.tool_call_name or "")

    def _on_ToolCallDeltaEvent(self, event) -> None:
        self._call_parts.setdefault(event.tool_call_id, []).append(str(event.delta or ""))

    def _on_ToolCallEndEvent(self, event) -> None:
        parts = self._call_parts.pop(event.tool_call_id, [])
        self._flush_tool_call(event.tool_call_id, parts)

    def _flush_tool_call(self, call_id: str, parts: list[str]) -> None:
        name = self._call_names.get(call_id, "") or "未知工具"
        raw = "".join(parts).strip()
        payload: object = raw
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw
        self.tool_usage.append({"type": "call", "name": name, "input": payload})
        self._write(EVENT_TOOL_CALL, f"{name} {raw or '{}'}")

    # ── 工具返回 ──

    def _on_ToolResultTextDeltaEvent(self, event) -> None:
        self._result_parts.setdefault(event.tool_call_id, []).append(str(event.delta or ""))

    def _on_ToolResultDataDeltaEvent(self, event) -> None:
        # 图片二进制不进日志：只记事件本身，路径由工具返回的 summary 提供
        self._write(EVENT_IMAGE, "工具返回了图片数据（二进制不入日志，路径见工具返回）")

    def _on_ToolResultEndEvent(self, event) -> None:
        parts = self._result_parts.pop(event.tool_call_id, [])
        self._flush_tool_result(event.tool_call_id, parts, state=getattr(event, "state", ""))

    def _flush_tool_result(self, call_id: str, parts: list[str], state: object = "") -> None:
        name = self._call_names.get(call_id, "") or "未知工具"
        raw = "".join(parts).strip()
        text = sanitize_tool_output_text(raw) if raw else ""
        row: dict = {"type": "result", "name": name, "state": str(state or "")}
        if text:
            row["output"] = text
        path = screenshot_path_from_tool_output(raw)
        if path:
            row["screenshot_path"] = path
            self.screenshot_path = path
        self.tool_usage.append(row)
        state_text = str(state or "-")
        self._write(EVENT_TOOL_RESULT, f"{name} state={state_text} {text or '(无返回文本)'}")

    # ── 模型调用与文本输出 ──

    def _on_ModelCallEndEvent(self, event) -> None:
        self.model_calls += 1
        self._write(
            EVENT_MODEL_CALL,
            "输入 {} / 输出 {} / 缓存命中 {} tokens".format(
                getattr(event, "input_tokens", 0),
                getattr(event, "output_tokens", 0),
                getattr(event, "cache_input_tokens", 0),
            ),
        )

    def _on_TextBlockDeltaEvent(self, event) -> None:
        self._output_parts = getattr(self, "_output_parts", [])
        self._output_parts.append(str(event.delta or ""))

    def _on_TextBlockEndEvent(self, event) -> None:
        parts = getattr(self, "_output_parts", [])
        self._output_parts = []
        text = "".join(parts).strip()
        if text:
            self._write(EVENT_OUTPUT, text)

    # ── 内部 ──

    def _write(self, event: str, content: str) -> None:
        self._log.write(
            role=self._role,
            model=self._model,
            scope=self._scope,
            event=event,
            content=content,
        )


__all__ = [
    "EVENT_MODEL_CALL",
    "EVENT_OUTPUT",
    "EVENT_THINKING",
    "EVENT_TOOL_CALL",
    "EVENT_TOOL_RESULT",
    "EventStreamRecorder",
]
