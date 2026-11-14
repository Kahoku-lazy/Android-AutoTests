"""
文件名: ➡️ models.py 🏁
路径: ➡️ engines/ae_harness/agents/models.py 🏁
模块功能：➡️ 校验一条模型配置并创建聊天模型 🏁
Python 调试：➡️ python -m engines.ae_harness.agents.models 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. ChatModel: 一条聊天模型配置的形状；字段声明即校验。
2. CreatedModel: 造模型的结果——模型实例 + 本次使用的密钥环境变量名（不含明文）。
3. create_model: 按短名取一条配置，校验后创建聊天模型，并交出用的是哪把密钥；不传表则自己读。
4. 密钥环境变量只有三个：DEEPSEEK_API_KEY、DASHSCOPE_API_KEY、GOVEE_API_KEY。
5. govee 走 OpenAI Chat Completions 协议，base_url 固定。
🏁
关联模块：➡️
1. engines.ae_harness.agents.config: 提供模型表与密钥取值。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor。
🏁
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agentscope.credential import (
    DashScopeCredential,
    DeepSeekCredential,
    OpenAICredential,
)
from agentscope.formatter import (
    DashScopeMultiAgentFormatter,
    DeepSeekMultiAgentFormatter,
)
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
    OpenAIChatModel,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import load_models, load_secret

__all__ = ["ChatModel", "CreatedModel", "create_model"]

# DeepSeek 条目没写 base_url 时用厂商默认地址。
_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# govee 走 OpenAI 兼容协议，地址固定。
_GOVEE_BASE_URL = "https://test-llm.lanjingerp.com/v1"

# provider → 唯一允许的密钥环境变量名。
_API_KEY_ENV = {
    "deepseek": "DEEPSEEK_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "govee": "GOVEE_API_KEY",
}


class ChatModel(BaseModel):
    """
    一条聊天模型配置。

    Attributes:
        provider: 厂商名；决定用哪个客户端类。
        api_key: 密钥所在的环境变量名；只能是预定的三个之一。
        model_name: 厂商正式模型名。
        base_url: 基础地址；空串表示用厂商默认。govee 固定。

    Raises:
        ValidationError: 字段缺失、类型不对、出现未知字段，或密钥名与 provider 不匹配。
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    provider: Literal["deepseek", "dashscope", "govee"]
    api_key: Literal["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "GOVEE_API_KEY"]
    model_name: str = Field(min_length=1)
    base_url: str = ""

    @model_validator(mode="after")
    def _check_api_key(self) -> "ChatModel":
        """
        确认密钥环境变量与 provider 对应。

        Returns:
            校验通过的自身。

        Raises:
            ValueError: 两者不匹配，如 provider=deepseek 却写 GOVEE_API_KEY。
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


def create_model(
    short_name: str,
    *,
    catalog: dict | None = None,
    stream: bool = True,
) -> CreatedModel:
    """
    按短名取一条配置，校验后创建聊天模型，并交出用的是哪把密钥。

    Args:
        short_name: 模型短名，如 deepseek_chat_flash。
        catalog: 模型表；不传则现读一次 models.yaml。
        stream: 是否流式输出。

    Returns:
        模型实例与本次使用的密钥环境变量名（不含明文）。

    Raises:
        ValueError: 短名不存在、密钥没配、base_url 不合法，或 provider 不受支持。
        ValidationError: 条目校验不通过。
    """
    table = catalog if catalog is not None else load_models()
    raw = table.get(short_name)
    if not isinstance(raw, dict):
        choices = ", ".join(sorted(str(key) for key in table)) or "无"
        raise ValueError(f"未知模型 {short_name!r}；可选：{choices}")

    entry = ChatModel.model_validate(raw)
    api_key = load_secret(entry.api_key)
    if not api_key:
        raise ValueError(f"{short_name}: 没有配置密钥 {entry.api_key}")
    if entry.provider == "deepseek":
        return CreatedModel(
            model=DeepSeekChatModel(
                credential=DeepSeekCredential(
                    api_key=api_key,
                    base_url=entry.base_url or _DEEPSEEK_BASE_URL,
                ),
                model=entry.model_name,
                stream=stream,
                formatter=DeepSeekMultiAgentFormatter(),
            ),
            api_key_env=entry.api_key,
        )
    if entry.provider == "dashscope":
        return CreatedModel(
            model=DashScopeChatModel(
                credential=DashScopeCredential(api_key=api_key),
                model=entry.model_name,
                stream=stream,
                formatter=DashScopeMultiAgentFormatter(),
            ),
            api_key_env=entry.api_key,
        )
    if entry.provider == "govee":
        base_url = entry.base_url or _GOVEE_BASE_URL
        if base_url != _GOVEE_BASE_URL:
            raise ValueError(
                f"{short_name}: govee 的 base_url 固定为 {_GOVEE_BASE_URL}，收到 {base_url!r}"
            )
        return CreatedModel(
            model=OpenAIChatModel(
                credential=OpenAICredential(api_key=api_key, base_url=base_url),
                model=entry.model_name,
                stream=stream,
            ),
            api_key_env=entry.api_key,
        )
    raise ValueError(f"{short_name}: 不支持的 provider {entry.provider!r}")
