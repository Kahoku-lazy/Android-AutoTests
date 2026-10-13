"""
python -m 调试路径: engines.agents.role.config

本模块的业务功能如下：
1. ModelConfig: 模型配置, 包括提供商、模型名称、API 密钥、基础 URL。
2. RoleSpecConfig: 角色配置, 包括名称、系统提示词、工具包、是否多模态、是否流式, 以及 ReAct 与上下文参数。
3. ChatModelFactory: 模型工厂, 根据模型配置创建模型。
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential
from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    DeepSeekChatModel,
    OpenAIChatModel,
)
from agentscope.tool import Toolkit
from pydantic import SecretStr


@dataclass(frozen=True)
class ModelConfig:
    """
    模型配置：提供商、模型名称、API 密钥、基础 URL。

    Attributes:
        provider: 模型提供商，可选 deepseek、openai、dashscope。
        model_name: 模型名称，如 deepseek-chat、gpt-4o、qwen-plus。
        api_key: API 密钥，字符串或 SecretStr 类型。
        base_url: 基础 URL，可选。

    Raises:
        FrozenInstanceError: 模型配置不可变。
    """

    provider: str = ""
    model_name: str = ""
    api_key: str | SecretStr = ""
    base_url: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.api_key, SecretStr):
            object.__setattr__(self, "api_key", SecretStr(self.api_key))


@dataclass(frozen=True)
class RoleSpecConfig:
    """
    角色配置：名称、系统提示词、工具包、是否多模态、是否流式，以及 ReAct 与上下文参数。

    Attributes:
        name: 角色名，用于 Agent 名与日志，如 executor_role、verifier_role。
        system_prompt: 本角色系统提示词正文。
        toolkit: 本角色已装配的工具包（每个角色一份，不共享）。
        vision: 是否多模态（executor / verifier 需截图输入）。
        stream: 是否流式输出。
        max_iters: ReAct 循环最大轮次。
        structured_output_grace_iters: 结构化输出的宽限轮次。
        stop_on_reject: 被驳回时是否停止。
        trigger_ratio: 上下文压缩触发比例。
        reserve_ratio: 上下文压缩保留比例。
        tool_result_limit: 单条工具结果的长度上限。
        max_image_num: 上下文保留的图片数量上限。

    Raises:
        FrozenInstanceError: 角色配置不可变。
    """

    name: str
    system_prompt: str
    toolkit: Toolkit
    vision: bool = True
    stream: bool = True
    max_iters: int = 30
    structured_output_grace_iters: int = 3
    stop_on_reject: bool = True
    trigger_ratio: float = 0.7
    reserve_ratio: float = 0.2
    tool_result_limit: int = 400000
    max_image_num: int = 5


class ChatModelFactory:
    """按 provider 创建 DeepSeek、DashScope 或 OpenAI 模型。"""

    def __init__(self, config: ModelConfig, stream: bool = True, vision: bool = False):
        """
        创建模型工厂：根据模型配置创建模型。

        Args:
            config: 模型配置。
            stream: 是否流式输出。
            vision: 是否多模态。
        """

        self.config = config
        self.stream = stream
        self.vision = vision

    def _credential(self, credential_cls):
        """凭证：base_url 原样传入（DeepSeek 与 OpenAI 兼容档的现有口径）。"""
        return credential_cls(api_key=self.config.api_key, base_url=self.config.base_url)

    def _credential_default_endpoint(self, credential_cls):
        """凭证：base_url 为空时不传，交给框架默认地址（DashScope 的现有口径）。"""
        if self.config.base_url:
            return credential_cls(api_key=self.config.api_key, base_url=self.config.base_url)
        return credential_cls(api_key=self.config.api_key)

    def deepseek_model(self) -> ChatModelBase:
        """创建 DeepSeek。vision 时走 OpenAI 兼容客户端，才能把截图当图片传入。"""
        config = self.config
        if self.vision:
            return OpenAIChatModel(
                credential=self._credential(OpenAICredential),
                model=config.model_name,
                parameters=OpenAIChatModel.Parameters(thinking_enable=True),
                stream=self.stream,
                extra_body={"thinking": {"type": "enabled"}},
            )
        return DeepSeekChatModel(
            credential=self._credential(DeepSeekCredential),
            model=config.model_name,
            parameters=DeepSeekChatModel.Parameters(thinking_enable=True),
            stream=self.stream,
        )

    def openai_model(self) -> OpenAIChatModel:
        """创建 OpenAI 模型。"""
        config = self.config
        return OpenAIChatModel(
            credential=self._credential(OpenAICredential),
            model=config.model_name,
            stream=self.stream,
        )

    def dashscope_model(self) -> DashScopeChatModel:
        """创建 DashScope 模型。base_url 为空时使用框架默认地址。"""
        config = self.config
        return DashScopeChatModel(
            credential=self._credential_default_endpoint(DashScopeCredential),
            model=config.model_name,
            stream=self.stream,
        )

    def create(self) -> ChatModelBase:
        """按 provider 创建模型。

        Returns:
            该 provider 对应的聊天模型实例。

        Raises:
            ValueError: provider 不在支持集合内（deepseek / openai / dashscope），
                报错会列出可选厂商。
        """
        config = self.config
        builders = {
            "deepseek": self.deepseek_model,
            "openai": self.openai_model,
            "dashscope": self.dashscope_model,
        }
        builder = builders.get(config.provider)
        if builder is None:
            raise ValueError(f"不支持的模型提供商: {config.provider}；可选：{', '.join(builders)}")
        return builder()
