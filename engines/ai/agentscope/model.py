"""模型层：通用 create_model / build_agent + 装配类。设备执行 / 平台任务通过类区分。"""

from __future__ import annotations

from agentscope.agent import Agent, ContextConfig, ReActConfig
from agentscope.credential import DeepSeekCredential, OpenAICredential
from agentscope.model import DeepSeekChatModel, OpenAIChatModel

from engines.ai.base import ToolSpec

from .config import (
    PLANNER_PROMPT,
    PLATFORM_EXECUTOR_PROMPT,
    PLATFORM_PLANNER_PROMPT,
    PLATFORM_VERIFIER_PROMPT,
    PLATFORM_VERIFIER_TOOLS,
    REASONING_TOOLS,
    VERIFIER_PROMPT,
    VERIFIER_TOOLS,
    VISION_PROMPT,
    VISION_TOOLS,
    DeviceExecutionConfig,
    ModelConfig,
    PlatformTaskConfig,
)
from .tool_wrapper import build_toolkit


def create_model(config: ModelConfig, stream: bool = True, vision: bool = False):
    """通用模型创建：按 provider 用专用模型类。

    vision=True 走 OpenAI 兼容类（formatter 支持 image_url 图片），关 thinking
    （结构化输出的 tool_choice 与 DeepSeek thinking 冲突）。
    文本模型默认也关 thinking，便于 structured_schema 输出。
    """
    api_key = config.api_key or ""
    # base_url 已由 Django 层（engine_adapter）解析默认值后传入 ModelSpec
    base_url = config.base_url
    if config.provider == "deepseek":
        if vision:
            params = OpenAIChatModel.Parameters(thinking_enable=False)
            return OpenAIChatModel(
                credential=OpenAICredential(api_key=api_key, base_url=base_url),
                model=config.model_name,
                parameters=params,
                stream=stream,
                extra_body={"thinking": {"type": "disabled"}},
            )
        return DeepSeekChatModel(
            credential=DeepSeekCredential(api_key=api_key, base_url=base_url),
            model=config.model_name,
            parameters=DeepSeekChatModel.Parameters(thinking_enable=False),
            stream=stream,
        )
    if config.provider == "dashscope":
        from agentscope.credential import DashScopeCredential
        from agentscope.model import DashScopeChatModel

        return DashScopeChatModel(
            credential=DashScopeCredential(api_key=api_key),
            model=config.model_name,
            stream=stream,
        )
    return OpenAIChatModel(
        credential=OpenAICredential(api_key=api_key, base_url=base_url),
        model=config.model_name,
        stream=stream,
    )


def build_agent(
    model,
    system_prompt: str,
    tool_specs: list[ToolSpec],
    user_id: str = "",
    name: str = "agent",
    context_config: dict | None = None,
    react_config: dict | None = None,
) -> Agent:
    """通用 Agent 装配：model + system_prompt + 工具 → Agent。"""
    return Agent(
        name=name,
        system_prompt=system_prompt,
        model=model,
        toolkit=build_toolkit(tool_specs, user_id=user_id),
        context_config=ContextConfig(**context_config) if context_config else None,
        react_config=ReActConfig(**react_config) if react_config else None,
    )


def _select_specs(tools: list[ToolSpec], names: list[str]) -> list[ToolSpec]:
    """按工具名子集从 TaskRequest.tools 选取 ToolSpec（保持 names 顺序）。"""
    by_name = {t.name: t for t in tools}
    return [by_name[n] for n in names if n in by_name]


class DeviceExecution:
    """设备执行：读三模型配置 → 通用创建 + 包装 → 持有三个 Agent。"""

    def __init__(self, config: DeviceExecutionConfig, tools: list[ToolSpec], user_id: str = ""):
        self.config = config
        self.user_id = user_id
        # 配置与模型创建分离：通用 create_model，再 build_agent 包装成 Agent
        self.planner_agent = build_agent(
            create_model(config.planner, stream=False, vision=False),
            PLANNER_PROMPT,
            [],
            user_id,
            name="planner",
        )
        self.executor_agent = build_agent(
            create_model(config.executor, stream=True, vision=True),
            VISION_PROMPT,
            _select_specs(tools, VISION_TOOLS),
            user_id,
            name="executor",
            context_config={"max_image_num": 5},
            react_config={"max_iters": 8},
        )
        self.verifier_agent = build_agent(
            create_model(config.verifier, stream=False, vision=True),
            VERIFIER_PROMPT,
            _select_specs(tools, VERIFIER_TOOLS),
            user_id,
            name="verifier",
            context_config={"max_image_num": 5},
        )


class PlatformTask:
    """平台任务：读三模型配置 → 通用创建 + 包装 → 持有三个文本 Agent。"""

    def __init__(self, config: PlatformTaskConfig, tools: list[ToolSpec], user_id: str = ""):
        self.config = config
        self.user_id = user_id
        # 三模型全文本（平台工具返回 JSON/文本，无图），不走 vision
        self.planner_agent = build_agent(
            create_model(config.planner, stream=False, vision=False),
            PLATFORM_PLANNER_PROMPT,
            [],
            user_id,
            name="planner",
        )
        self.executor_agent = build_agent(
            create_model(config.executor, stream=False, vision=False),
            PLATFORM_EXECUTOR_PROMPT,
            _select_specs(tools, REASONING_TOOLS),
            user_id,
            name="executor",
            react_config={"max_iters": 12},
        )
        self.verifier_agent = build_agent(
            create_model(config.verifier, stream=False, vision=False),
            PLATFORM_VERIFIER_PROMPT,
            _select_specs(tools, PLATFORM_VERIFIER_TOOLS),
            user_id,
            name="verifier",
        )
