from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from typing import Any

from agentscope.middleware import MiddlewareBase

__all__ = [
    "KIND_COMPRESS",
    "KIND_SYSTEM_PROMPT",
    "ObservationMiddleware",
    "ObservationRecord",
]

KIND_COMPRESS = "compress_context"
KIND_SYSTEM_PROMPT = "system_prompt"

_INSTRUCTION_LIMIT = 500
_STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S.%f"


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
    def __init__(self, emit: Callable[[ObservationRecord], None] | None = None) -> None:
        self._emit = emit
        self.records: list[ObservationRecord] = []

    def _record(self, record: ObservationRecord) -> None:
        if self._emit is not None:
            self._emit(record)
            return
        self.records.append(record)

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


if __name__ == "__main__":
    import asyncio

    observer = ObservationMiddleware()
    asyncio.run(observer.on_system_prompt(None, "你是执行者。"))
    print(observer.records[0].as_dict())  # noqa: T201 - 模块自测入口
