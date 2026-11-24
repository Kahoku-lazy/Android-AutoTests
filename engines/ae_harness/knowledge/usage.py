from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from agentscope.embedding import EmbeddingModelBase, EmbeddingResponse
from agentscope.message import DataBlock, TextBlock

__all__ = ["UsageEvent", "UsageRecordingEmbedding", "tag_events"]


@dataclass(frozen=True)
class UsageEvent:
    model: str
    api_key_env: str
    tokens: int
    time: float
    phase: str = ""
    base: str = ""
    occurred_at: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "api_key_env": self.api_key_env,
            "tokens": self.tokens,
            "time": self.time,
            "phase": self.phase,
            "base": self.base,
            "occurred_at": self.occurred_at,
        }


class UsageRecordingEmbedding:
    def __init__(self, model: EmbeddingModelBase, api_key_env: str) -> None:
        self._model = model
        self.api_key_env = api_key_env
        self._events: list[UsageEvent] = []

    @property
    def model(self) -> str:
        return self._model.model

    @property
    def dimensions(self) -> int:
        return self._model.dimensions

    @property
    def supports_multimodal(self) -> bool:
        return self._model.supports_multimodal

    async def __call__(
        self,
        inputs: list[str | TextBlock | DataBlock],
        **kwargs: Any,
    ) -> EmbeddingResponse:
        response = await self._model(inputs, **kwargs)
        usage = response.usage
        tokens = int(usage.tokens or 0) if usage is not None else 0
        if tokens > 0:
            self._events.append(
                UsageEvent(
                    model=self._model.model,
                    api_key_env=self.api_key_env,
                    tokens=tokens,
                    time=float(usage.time) if usage is not None else 0.0,
                    occurred_at=datetime.now().isoformat(timespec="milliseconds"),
                )
            )
        return response

    def drain_events(self) -> list[UsageEvent]:
        events = self._events
        self._events = []
        return events


def tag_events(events: list[UsageEvent], *, phase: str, base: str) -> list[UsageEvent]:
    return [replace(event, phase=phase, base=base) for event in events]


if __name__ == "__main__":
    print(  # noqa: T201 - 模块自测：确认事件可序列化
        UsageEvent(
            model="text-embedding-v4", api_key_env="DASHSCOPE_API_KEY", tokens=1, time=0.1
        ).as_dict()
    )
