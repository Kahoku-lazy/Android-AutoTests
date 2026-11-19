"""
文件名: ➡️ models.py 🏁
路径: ➡️ engines/ae_harness/agents/models.py 🏁
模块功能：➡️ 校验一条模型配置并创建聊天模型 🏁
Python 调试：➡️ python -m engines.ae_harness.agents.models 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.3.0 🏁
修改时间: ➡️ 2026-11-19 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ChatModel: 一条聊天模型配置的形状；字段声明即校验。
2. CreatedModel: 造模型的结果——模型实例 + 本次使用的密钥环境变量名（不含明文）。
3. create_model: 按调用方传入的厂商、密钥名、地址、模型名创建聊天模型。
4. 密钥由本模块自己解析：先查仓库根 .env，再查进程环境；不经 config。
5. 密钥环境变量只有三个：DEEPSEEK_API_KEY、DASHSCOPE_API_KEY、OPENAI_API_KEY。
6. OpenAIGatewayFormatter: openai 通道去掉 system 与 assistant 消息的 name 键。
7. OpenAIGatewayChatModel: 思考模式拒绝强制选工具时，按请求类型只重发一次。
8. create_model 支持显式配置模型层内置重试次数（默认 1），与可靠性中间件分层，避免叠加放大。
9. OpenAIGatewayChatModel 经官方扩展点 _get_disable_thinking_kwargs 向结构化输出策略阶梯声明关思考参数。
🏁
关联模块：➡️
1. 无本地依赖：只用标准库、dotenv 与 agentscope。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_openai_message_name.py: openai 消息名过滤
2. tests/engines/ae_harness/unit/test_openai_tool_choice.py: 思考模式拒绝强制选工具时的重发
3. tests/engines/ae_harness/unit/test_model_max_retries.py: 模型层重试默认 1 与显式配置透传
4. tests/engines/ae_harness/unit/test_openai_disable_thinking.py: 关思考扩展点形状与普通 400 不重发
🏁
"""

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

# 仓库根：engines/ae_harness/agents/models.py 往上四级。只读这一份 .env。
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_ENV = dotenv_values(_ENV_PATH) if _ENV_PATH.exists() else {}

# 调用方没传地址时用厂商默认。openai 不再钉死，传入值优先。
_DEFAULT_BASE_URL = {
    "deepseek": "https://api.deepseek.com",
    "openai": "https://test-llm.lanjingerp.com/v1",
}

# provider → 唯一允许的密钥环境变量名。
_API_KEY_ENV = {
    "deepseek": "DEEPSEEK_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class ChatModel(BaseModel):
    """
    一条聊天模型配置。

    Attributes:
        provider: 厂商名；决定用哪个客户端类。
        api_key: 密钥所在的环境变量名；只能是预定的三个之一。
        model_name: 厂商正式模型名。
        base_url: 基础地址；空串表示用厂商默认。openai 固定。

    Raises:
        ValidationError: 字段缺失、类型不对、出现未知字段，或密钥名与 provider 不匹配。
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    provider: Literal["deepseek", "dashscope", "openai"]
    api_key: Literal["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY"]
    model_name: str = Field(min_length=1)
    base_url: str = ""

    @model_validator(mode="after")
    def _check_api_key(self) -> "ChatModel":
        """
        确认密钥环境变量与 provider 对应。

        Returns:
            校验通过的自身。

        Raises:
            ValueError: 两者不匹配，如 provider=deepseek 却写 OPENAI_API_KEY。
        """
        expected = _API_KEY_ENV[self.provider]
        if self.api_key != expected:
            raise ValueError(f"provider={self.provider} 的 api_key 必须是 {expected}")
        return self


@dataclass(frozen=True)
class CreatedModel:
    """
    造模型的结果：模型实例 + 用的是哪把密钥。

    密钥只给环境变量名，不给值；记账按这个名字归组。

    Attributes:
        model: 已创建的聊天模型实例。
        api_key_env: 本次使用的密钥所在的环境变量名。
    """

    model: ChatModelBase
    api_key_env: str


class OpenAIGatewayFormatter(OpenAIChatFormatter):
    """
    openai 网关用的 OpenAI 兼容格式化器。

    先按 OpenAI 形状写出消息，再删除 system 与 assistant 上的 name 键。
    user 与 tool 的 name 保留。不按模型名分支。
    """

    async def format(self, msgs: list[Msg]) -> list[dict]:
        """
        格式化消息，并去掉非 user、非 tool 消息的 name。

        Args:
            msgs: 待格式化的 AgentScope 消息。

        Returns:
            已删除受限 name 键的消息列表。
        """
        formatted = await super().format(msgs)
        for item in formatted:
            if item.get("role") not in {"user", "tool"}:
                item.pop("name", None)
        return formatted


_THINKING_TOOL_CHOICE = "Thinking mode does not support this tool_choice"
_STRUCTURED_TOOL = "GenerateStructuredOutput"


def _thinking_rejected(exc: Exception) -> bool:
    """只认网关这句拒绝。其它 400 不重发。"""
    return _THINKING_TOOL_CHOICE in str(exc)


def _can_retry(tool_choice: ToolChoice | None) -> bool:
    """没强制、也不是禁止调用时，不重发。"""
    if tool_choice is None or tool_choice.mode == "auto":
        return False
    return True


def _forced_name(tool_choice: ToolChoice | None) -> str | None:
    """强制工具名。auto / none / 未指定时返回 None。"""
    if tool_choice is None:
        return None
    mode = tool_choice.mode
    if mode in {"auto", "none", "required"}:
        return None
    return str(mode)


def _disable_thinking(kwargs: dict) -> dict:
    """只在这次重发里关思考，不改模型默认。"""
    extra = dict(kwargs.get("extra_body") or {})
    thinking = dict(extra.get("thinking") or {})
    thinking["type"] = "disabled"
    extra["thinking"] = thinking
    return {**kwargs, "extra_body": extra}


def _only_structured(tools: list[dict] | None) -> list[dict]:
    """交结论的最后一次只留结构化工具，避免改去点设备。"""
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
    """
    openai 通道的聊天模型。

    思考模式拒绝强制选工具时，按请求类型重发。普通请求、已开始的流、其它错误都不重发。
    另经官方扩展点声明关思考参数，供框架结构化输出策略阶梯的 no_think 档使用。
    """

    def _get_disable_thinking_kwargs(self) -> dict:
        """
        向框架结构化输出策略阶梯声明关思考参数（与官方 DeepSeek 实现同款）。

        Returns:
            no_think 档叠加的请求参数：extra_body.thinking.type=disabled。
        """
        return {"extra_body": {"thinking": {"type": "disabled"}}}

    async def _call_api(
        self,
        model_name: str,
        messages: list[Msg],
        tools: list[dict] | None = None,
        tool_choice: ToolChoice | None = None,
        **generate_kwargs,
    ):
        """
        调用网关。仅在请求还没开始返回时，按四段规则重发。

        Args:
            model_name: 厂商模型名。
            messages: 已格式化前的消息。
            tools: 本次可用工具。
            tool_choice: 本次工具选择。
            generate_kwargs: 其余请求参数。

        Returns:
            父类的响应或流。

        Raises:
            Exception: 不是这句拒绝，或重发后仍被拒绝。
        """
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
    """
    按环境变量名取密钥值。先查仓库根 .env，再查进程环境。

    Args:
        name: 环境变量名，如 DEEPSEEK_API_KEY。

    Returns:
        密钥值；两处都没配时返回空串。
    """
    return str(_ENV.get(name) or os.environ.get(name, ""))


def create_model(
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    *,
    stream: bool = True,
    max_retries: int = 1,
) -> CreatedModel:
    """
    按调用方传入的连接参数创建聊天模型，并交出用的是哪把密钥。

    Args:
        provider: 厂商名，只能是 deepseek、dashscope、openai。
        api_key_env: 密钥所在的环境变量名，必须与厂商成对。
        model_name: 厂商正式模型名。
        base_url: 基础地址；空串时用该厂商默认地址。
        stream: 是否流式输出。
        max_retries: 模型层内置重试次数，默认 1（最多尝试 2 次）。
            与可靠性中间件分层：中间件负责错误分类、退避抖动与流式首块前兜底，
            模型层只留一次快速重试，避免两层叠加放大调用次数。

    Returns:
        模型实例与本次使用的密钥环境变量名（不含明文）。

    Raises:
        ValueError: 厂商与密钥名不匹配、密钥没配，或地址为空且没有默认值。
        ValidationError: 连接参数校验不通过。
    """
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
                formatter=DeepSeekMultiAgentFormatter(),
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
                formatter=DashScopeMultiAgentFormatter(),
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
                formatter=OpenAIGatewayFormatter(),
            ),
            api_key_env=entry.api_key,
        )
    raise ValueError(f"不支持的 provider {entry.provider!r}")
