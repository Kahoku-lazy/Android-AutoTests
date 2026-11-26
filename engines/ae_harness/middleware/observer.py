from __future__ import annotations

import inspect
import json

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from typing import Any

from agentscope.middleware import MiddlewareBase

__all__ = [
    "KIND_ACTING",
    "KIND_COMPRESS",
    "KIND_MODEL_CALL",
    "KIND_MODEL_CALL_RETURN",
    "KIND_PERMISSION",
    "KIND_REASONING",
    "KIND_REPLY",
    "KIND_SYSTEM_PROMPT",
    "ObservationMiddleware",
    "ObservationRecord",
]

KIND_COMPRESS = "compress_context"
KIND_MODEL_CALL = "model_call"
KIND_MODEL_CALL_RETURN = "model_call_return"
KIND_SYSTEM_PROMPT = "system_prompt"
KIND_REPLY = "reply"
KIND_REASONING = "reasoning"
KIND_ACTING = "acting"
KIND_PERMISSION = "permission"

_INSTRUCTION_LIMIT = 500
_MEDIA_MIN_CHARS = 256
_STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S.%f"


def _sanitize(value: object, key: str = "") -> object:
    if isinstance(value, str):
        if key == "data" and len(value) > _MEDIA_MIN_CHARS:
            return {"base64_chars": len(value), "head": value[:24]}
        return value
    if isinstance(value, dict):
        return {str(name): _sanitize(item, str(name)) for name, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_sanitize(item, key) for item in value]
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return _sanitize(dump(mode="python"), key)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _stamp() -> str:
    return datetime.now().strftime(_STAMP_FORMAT)[:-3]


def _agent_name(agent: object) -> str:
    return str(getattr(agent, "name", "") or "")


def _context_len(agent: object) -> int | None:
    context = getattr(getattr(agent, "state", None), "context", None)
    try:
        return len(context)  # type: ignore[arg-type]
    except TypeError:
        return None


def _image_count(messages: Any) -> int:
    total = 0
    for message in messages or []:
        blocks = getattr(message, "content", None)
        if blocks is None and isinstance(message, dict):
            blocks = message.get("content")
        for block in blocks or []:
            if (
                getattr(block, "type", None) == "data"
                or isinstance(block, dict)
                and block.get("type") == "data"
            ):
                total += 1
            output = getattr(block, "output", None) or (
                block.get("output") if isinstance(block, dict) else None
            )
            for item in output or []:
                if (
                    getattr(item, "type", None) == "data"
                    or isinstance(item, dict)
                    and item.get("type") == "data"
                ):
                    total += 1
    return total


def _wire_rows(payload: Any) -> dict:
    rows: list[dict] = []
    images = 0
    for item in payload or []:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        parts: list[dict] = []
        if isinstance(content, str):
            parts.append({"type": "text", "chars": len(content)})
        for part in content if isinstance(content, list) else []:
            if not isinstance(part, dict):
                continue
            kind = str(part.get("type") or "")
            if kind == "image_url":
                url = str((part.get("image_url") or {}).get("url") or "")
                media = url.split(";", 1)[0].replace("data:", "") if url.startswith("data:") else ""
                parts.append({"type": "image", "chars": len(url), "media_type": media})
                images += 1
            elif kind == "text":
                parts.append({"type": "text", "chars": len(str(part.get("text") or ""))})
            else:
                parts.append({"type": kind})
        if item.get("tool_calls"):
            parts.append({"type": "tool_calls", "count": len(item.get("tool_calls") or [])})
        rows.append({"role": str(item.get("role") or ""), "parts": parts})
    return {"messages": rows, "images": images}


async def _wire_digest(model: Any, messages: Any) -> dict:
    formatter = getattr(model, "formatter", None)
    if formatter is None:
        return {"available": False}
    try:
        payload = formatter.format(messages)
        if inspect.isawaitable(payload):
            payload = await payload
    except Exception as exc:
        return {"available": True, "error": str(exc)[:300]}
    digest = _wire_rows(payload)
    return {"available": True, **digest}


def _state_snapshot(agent: object) -> dict:
    state = getattr(agent, "state", None)
    tasks: list = []
    for task in getattr(getattr(state, "tasks_context", None), "tasks", []) or []:
        dump = task.model_dump(mode="python") if hasattr(task, "model_dump") else {}
        rows = {
            key: dump.get(key)
            for key in ("id", "subject", "status", "owner", "blocked_by", "description")
            if key in dump and dump.get(key) not in (None, "", [], {})
        }
        tasks.append(rows or _sanitize(dump))
    permission = getattr(state, "permission_context", None)
    mode = getattr(permission, "mode", "")
    summary = str(getattr(state, "summary", "") or "")
    return {
        "session_id": str(getattr(state, "session_id", "") or ""),
        "reply_id": str(getattr(getattr(state, "reply_context", None), "reply_id", "") or ""),
        "context_len": _context_len(agent),
        "tasks": tasks[:20],
        "summary_chars": len(summary),
        "summary": summary[:2000],
        "permission_mode": str(getattr(mode, "value", mode) or ""),
        "permission_rules": {
            "allow": len(getattr(permission, "allow_rules", {}) or {}),
            "deny": len(getattr(permission, "deny_rules", {}) or {}),
            "ask": len(getattr(permission, "ask_rules", {}) or {}),
            "working_dirs": len(getattr(permission, "working_directories", []) or []),
        },
    }


def _hint_text(instructions: object) -> str:
    hint = getattr(instructions, "hint", None)
    if hint is None:
        return ""
    if isinstance(hint, str):
        text = hint
    elif isinstance(hint, list):
        text = "".join(str(getattr(block, "text", "") or "") for block in hint)
    else:
        text = str(hint)
    text = text.strip()
    if len(text) > _INSTRUCTION_LIMIT:
        return f"{text[:_INSTRUCTION_LIMIT]}…（共 {len(text)} 字符）"
    return text


@dataclass
class ObservationRecord:
    kind: str
    at: str
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "at": self.at, **self.payload}


class ObservationMiddleware(MiddlewareBase):
    def __init__(
        self,
        emit: Callable[[ObservationRecord], None] | None = None,
        *,
        capture_messages: bool = False,
    ) -> None:
        self._emit = emit
        self._capture_messages = bool(capture_messages)
        self._rounds = 0
        self._wire_probed = False
        self._wire_supported: bool | None = None
        self._reply_id = ""
        self.records: list[ObservationRecord] = []

    def attach(self, emit: Callable[[ObservationRecord], None]) -> None:
        self._emit = emit
        while self.records:
            emit(self.records.pop(0))

    def _record(self, record: ObservationRecord) -> None:
        if not record.payload.get("reply_id") and self._reply_id:
            record.payload["reply_id"] = self._reply_id
        if self._emit is not None:
            self._emit(record)
            return
        self.records.append(record)

    def _sync_reply_id(self, agent: object) -> str:
        reply_id = str(
            getattr(getattr(getattr(agent, "state", None), "reply_context", None), "reply_id", "")
            or ""
        )
        if reply_id:
            self._reply_id = reply_id
        return self._reply_id

    def _messages(self, messages: Any) -> list:
        rows = []
        for item in messages or []:
            dump = _sanitize(item)
            if isinstance(dump, dict):
                dump.pop("metadata", None)
            rows.append(dump)
        return rows

    async def on_system_prompt(self, agent: object, current_prompt: str) -> str:
        text = str(current_prompt or "")
        self._record(
            ObservationRecord(
                kind=KIND_SYSTEM_PROMPT,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "length": len(text),
                    "text": text,
                },
            )
        )
        return current_prompt

    async def on_compress_context(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> None:
        begin = perf_counter()
        config = input_kwargs.get("context_config") or getattr(agent, "context_config", None)
        instructions = input_kwargs.get("instructions")
        before = _context_len(agent)
        ratio = getattr(config, "trigger_ratio", None)
        window = getattr(getattr(agent, "model", None), "context_size", None)
        threshold = ratio * window if (ratio is not None and window) else None

        await next_handler(**input_kwargs)

        after = _context_len(agent)
        compressed = None if (before is None or after is None) else after < before
        self._record(
            ObservationRecord(
                kind=KIND_COMPRESS,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "messages_before": before,
                    "messages_after": after,
                    "compressed": compressed,
                    "trigger_ratio": ratio,
                    "context_size": window,
                    "threshold": threshold,
                    "instructions": _hint_text(instructions),
                    "cost_ms": round((perf_counter() - begin) * 1000, 1),
                },
            )
        )

    async def on_model_call(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        messages = input_kwargs.get("messages") or []
        tools = input_kwargs.get("tools") or []
        self._sync_reply_id(agent)
        payload: dict[str, Any] = {
            "agent": _agent_name(agent),
            "model": str(getattr(input_kwargs.get("current_model"), "model", "") or ""),
            "context_len": _context_len(agent),
            "tool_names": [
                str((item.get("function") or {}).get("name") or item.get("name") or "")
                for item in tools
                if isinstance(item, dict)
            ],
            "tool_choice": _sanitize(input_kwargs.get("tool_choice")),
            "message_count": len(messages),
        }
        if self._capture_messages:
            rows = self._messages(messages)
            payload["messages"] = rows
            payload["messages_chars"] = len(json.dumps(rows, ensure_ascii=False, default=str))
        payload["state"] = _state_snapshot(agent)
        images = _image_count(messages)
        payload["framework_images"] = images
        if images and not self._wire_probed:
            wire = await _wire_digest(input_kwargs.get("current_model"), messages)
            payload["wire"] = wire
            self._wire_supported = int(wire.get("images") or 0) > 0
            self._wire_probed = True
        if images:
            supported = bool(self._wire_supported)
            payload["images_sent"] = images if supported else 0
            payload["images_dropped"] = not supported
        self._record(ObservationRecord(kind=KIND_MODEL_CALL, at=_stamp(), payload=payload))

        begin = perf_counter()
        try:
            result = await next_handler(**input_kwargs)
        except Exception as exc:
            self._record(
                ObservationRecord(
                    kind=KIND_MODEL_CALL_RETURN,
                    at=_stamp(),
                    payload={
                        "agent": _agent_name(agent),
                        "cost_ms": round((perf_counter() - begin) * 1000, 1),
                        "error": str(exc)[:500],
                    },
                )
            )
            raise
        self._record(
            ObservationRecord(
                kind=KIND_MODEL_CALL_RETURN,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "cost_ms": round((perf_counter() - begin) * 1000, 1),
                    "stream": inspect.isasyncgen(result),
                    "usage": _sanitize(getattr(result, "usage", None)),
                },
            )
        )
        return result

    async def on_reply(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        begin = perf_counter()
        self._sync_reply_id(agent)
        inputs = input_kwargs.get("inputs")
        payload: dict[str, Any] = {
            "agent": _agent_name(agent),
            "phase": "start",
            "context_len": _context_len(agent),
            "input_count": len(inputs) if isinstance(inputs, list) else (1 if inputs else 0),
            "structured_schema": bool(input_kwargs.get("structured_schema")),
        }
        if isinstance(inputs, list) and inputs:
            payload["input_roles"] = [str(getattr(item, "role", "") or "") for item in inputs]
        self._record(ObservationRecord(kind=KIND_REPLY, at=_stamp(), payload=payload))
        try:
            async for item in next_handler(**input_kwargs):
                yield item
        finally:
            self._record(
                ObservationRecord(
                    kind=KIND_REPLY,
                    at=_stamp(),
                    payload={
                        "agent": _agent_name(agent),
                        "phase": "end",
                        "context_len": _context_len(agent),
                        "cost_ms": round((perf_counter() - begin) * 1000, 1),
                    },
                )
            )

    async def on_reasoning(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        self._rounds += 1
        round_index = self._rounds
        begin = perf_counter()
        self._sync_reply_id(agent)
        self._record(
            ObservationRecord(
                kind=KIND_REASONING,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "round": round_index,
                    "phase": "start",
                    "tool_choice": _sanitize(input_kwargs.get("tool_choice")),
                    "state": _state_snapshot(agent),
                },
            )
        )
        try:
            async for item in next_handler(**input_kwargs):
                yield item
        finally:
            self._record(
                ObservationRecord(
                    kind=KIND_REASONING,
                    at=_stamp(),
                    payload={
                        "agent": _agent_name(agent),
                        "round": round_index,
                        "phase": "end",
                        "context_len": _context_len(agent),
                        "cost_ms": round((perf_counter() - begin) * 1000, 1),
                    },
                )
            )

    async def on_acting(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        call = input_kwargs.get("tool_call")
        name = str(getattr(call, "name", "") or "")
        call_id = str(getattr(call, "id", "") or "")
        self._sync_reply_id(agent)
        begin = perf_counter()
        chunks = 0
        state = ""
        output = ""
        try:
            async for item in next_handler(**input_kwargs):
                chunks += 1
                state = str(getattr(item, "state", "") or state)
                text = getattr(item, "text", None)
                if isinstance(text, str) and len(output) < 500:
                    output += text
                yield item
        finally:
            self._record(
                ObservationRecord(
                    kind=KIND_ACTING,
                    at=_stamp(),
                    payload={
                        "agent": _agent_name(agent),
                        "tool": name,
                        "tool_call_id": call_id,
                        "input": _sanitize(getattr(call, "input", "")),
                        "output": output[:500],
                        "chunks": chunks,
                        "state": state,
                        "cost_ms": round((perf_counter() - begin) * 1000, 1),
                    },
                )
            )

    async def on_check_permission(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> Any:
        decision = await next_handler(**input_kwargs)
        call = input_kwargs.get("tool_call")
        self._sync_reply_id(agent)
        tool_input = _sanitize(getattr(call, "input", ""))
        if isinstance(tool_input, str):
            tool_input = tool_input[:300]
        self._record(
            ObservationRecord(
                kind=KIND_PERMISSION,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "tool": str(getattr(call, "name", "") or ""),
                    "tool_call_id": str(getattr(call, "id", "") or ""),
                    "input": tool_input,
                    "decision": _sanitize(decision),
                },
            )
        )
        return decision


if __name__ == "__main__":
    import asyncio

    observer = ObservationMiddleware()
    asyncio.run(observer.on_system_prompt(None, "你是执行者。"))
    print(observer.records[0].as_dict())  # noqa: T201 - 模块自测入口
