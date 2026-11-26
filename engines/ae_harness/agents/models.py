from __future__ import annotations

import os

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentscope.credential import (
    DashScopeCredential,
    DeepSeekCredential,
    OpenAICredential,
)
from agentscope.formatter import (
    DashScopeMultiAgentFormatter,
    DeepSeekMultiAgentFormatter,
    OpenAIChatFormatter,
)
from agentscope.message import Msg
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
    OpenAIChatModel,
)
from agentscope.tool import ToolChoice
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = [
    "ChatModel",
    "CreatedModel",
    "OpenAIGatewayFormatter",
    "create_model",
    "load_secret",
]

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_ENV = dotenv_values(_ENV_PATH) if _ENV_PATH.exists() else {}

_DEFAULT_BASE_URL = {
    "deepseek": "https://api.deepseek.com",
    "openai": "https://test-llm.lanjingerp.com/v1",
}

_API_KEY_ENV = {
    "deepseek": "DEEPSEEK_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class ChatModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    provider: Literal["deepseek", "dashscope", "openai"]
    api_key: Literal["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY"]
    model_name: str = Field(min_length=1)
    base_url: str = ""

    @model_validator(mode="after")
    def _check_api_key(self) -> "ChatModel":
        expected = _API_KEY_ENV[self.provider]
        if self.api_key != expected:
            raise ValueError(f"provider={self.provider} 的 api_key 必须是 {expected}")
        return self


@dataclass(frozen=True)
class CreatedModel:
    model: ChatModelBase
    api_key_env: str


class OpenAIGatewayFormatter(OpenAIChatFormatter):
    async def format(self, msgs: list[Msg]) -> list[dict]:
        formatted = await super().format(msgs)
        for item in formatted:
            if item.get("role") not in {"user", "tool"}:
                item.pop("name", None)
        return formatted


_THINKING_TOOL_CHOICE = "Thinking mode does not support this tool_choice"
_STRUCTURED_TOOL = "GenerateStructuredOutput"


def _thinking_rejected(exc: Exception) -> bool:
    return _THINKING_TOOL_CHOICE in str(exc)


def _can_retry(tool_choice: ToolChoice | None) -> bool:
    if tool_choice is None or tool_choice.mode == "auto":
        return False
    return True


def _forced_name(tool_choice: ToolChoice | None) -> str | None:
    if tool_choice is None:
        return None
    mode = tool_choice.mode
    if mode in {"auto", "none", "required"}:
        return None
    return str(mode)


def _disable_thinking(kwargs: dict) -> dict:
    extra = dict(kwargs.get("extra_body") or {})
    thinking = dict(extra.get("thinking") or {})
    thinking["type"] = "disabled"
    extra["thinking"] = thinking
    return {**kwargs, "extra_body": extra}


def _only_structured(tools: list[dict] | None) -> list[dict]:
    for tool in tools or []:
        function = tool.get("function") or {}
        if function.get("name") == _STRUCTURED_TOOL or tool.get("name") == _STRUCTURED_TOOL:
            return [tool]
    return [
        {
            "type": "function",
            "function": {"name": _STRUCTURED_TOOL, "parameters": {"type": "object"}},
        }
    ]


class OpenAIGatewayChatModel(OpenAIChatModel):
    def _get_disable_thinking_kwargs(self) -> dict:
        return {"extra_body": {"thinking": {"type": "disabled"}}}

    async def _call_api(
        self,
        model_name: str,
        messages: list[Msg],
        tools: list[dict] | None = None,
        tool_choice: ToolChoice | None = None,
        **generate_kwargs,
    ):
        try:
            return await super()._call_api(
                model_name, messages, tools, tool_choice, **generate_kwargs
            )
        except Exception as exc:
            if not _thinking_rejected(exc) or not _can_retry(tool_choice):
                raise
            quiet = _disable_thinking(generate_kwargs)
            try:
                return await super()._call_api(model_name, messages, tools, tool_choice, **quiet)
            except Exception as second:
                if not _thinking_rejected(second) or _forced_name(tool_choice) != _STRUCTURED_TOOL:
                    raise
                return await super()._call_api(
                    model_name,
                    messages,
                    _only_structured(tools),
                    ToolChoice(mode="auto"),
                    **quiet,
                )


def load_secret(name: str) -> str:
    return str(_ENV.get(name) or os.environ.get(name, ""))


def _input_types(model_cls: type, model_name: str) -> list[str]:
    try:
        cards = model_cls.list_models()
    except Exception:  # silent-except
        return []
    for card in cards or []:
        if str(getattr(card, "name", "")) == model_name:
            return [str(item) for item in getattr(card, "input_types", []) or []]
    return []


def create_model(
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    *,
    stream: bool = True,
    max_retries: int = 1,
) -> CreatedModel:
    entry = ChatModel.model_validate(
        {
            "provider": provider,
            "api_key": api_key_env,
            "model_name": model_name,
            "base_url": base_url,
        }
    )
    api_key = load_secret(entry.api_key)
    if not api_key:
        raise ValueError(f"没有配置密钥 {entry.api_key}")
    resolved = entry.base_url or _DEFAULT_BASE_URL.get(entry.provider, "")
    if entry.provider == "deepseek":
        return CreatedModel(
            model=DeepSeekChatModel(
                credential=DeepSeekCredential(api_key=api_key, base_url=resolved),
                model=entry.model_name,
                stream=stream,
                max_retries=max_retries,
                formatter=DeepSeekMultiAgentFormatter(
                    input_types=_input_types(DeepSeekChatModel, entry.model_name) or ["text/plain"]
                ),
            ),
            api_key_env=entry.api_key,
        )
    if entry.provider == "dashscope":
        credential = (
            DashScopeCredential(api_key=api_key, base_url=resolved)
            if resolved
            else DashScopeCredential(api_key=api_key)
        )
        return CreatedModel(
            model=DashScopeChatModel(
                credential=credential,
                model=entry.model_name,
                stream=stream,
                max_retries=max_retries,
                formatter=DashScopeMultiAgentFormatter(
                    input_types=_input_types(DashScopeChatModel, entry.model_name) or ["text/plain"]
                ),
            ),
            api_key_env=entry.api_key,
        )
    if entry.provider == "openai":
        if not resolved:
            raise ValueError("openai 的 base_url 不能为空")
        return CreatedModel(
            model=OpenAIGatewayChatModel(
                credential=OpenAICredential(api_key=api_key, base_url=resolved),
                model=entry.model_name,
                stream=stream,
                max_retries=max_retries,
                formatter=OpenAIGatewayFormatter(
                    input_types=_input_types(OpenAIChatModel, entry.model_name) or ["text/plain"]
                ),
            ),
            api_key_env=entry.api_key,
        )
    raise ValueError(f"不支持的 provider {entry.provider!r}")
