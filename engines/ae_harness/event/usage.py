from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["EMPTY_LABEL", "TokenUsage", "UsageSummary", "summarize"]

EMPTY_LABEL = "-"


@dataclass(frozen=True)
class TokenUsage:
    api_key_env: str
    round_index: int
    started_at: str
    ended_at: str
    input_tokens: int
    output_tokens: int
    cache_input_tokens: int
    cache_creation_input_tokens: int
    model: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "api_key_env": self.api_key_env,
            "model": self.model,
            "round": self.round_index,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_input_tokens": self.cache_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
        }


@dataclass
class UsageSummary:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    by_api_key_env: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "calls": self.calls,
            "input": self.input_tokens,
            "output": self.output_tokens,
            "cache_hit": self.cache_input_tokens,
            "cache_creation": self.cache_creation_input_tokens,
            "by_api_key_env": dict(self.by_api_key_env),
        }


def summarize(usages: list[TokenUsage] | tuple[TokenUsage, ...]) -> UsageSummary:
    result = UsageSummary()
    for item in usages:
        result.calls += 1
        result.input_tokens += item.input_tokens
        result.output_tokens += item.output_tokens
        result.cache_input_tokens += item.cache_input_tokens
        result.cache_creation_input_tokens += item.cache_creation_input_tokens
        key = item.api_key_env or EMPTY_LABEL
        result.by_api_key_env[key] = result.by_api_key_env.get(key, 0) + 1
    return result


if __name__ == "__main__":
    demo = TokenUsage(
        api_key_env="OPENAI_API_KEY",
        round_index=1,
        started_at="2026-11-13_18-00-00.000",
        ended_at="2026-11-13_18-00-03.721",
        input_tokens=5384,
        output_tokens=32,
        cache_input_tokens=4992,
        cache_creation_input_tokens=0,
    )
    print(demo.as_dict())  # noqa: T201 - 模块自测入口
    print(summarize([demo]).as_dict())  # noqa: T201 - 模块自测入口
