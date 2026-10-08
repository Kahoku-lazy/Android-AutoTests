"""智能体基类：模型创建 + 角色基类。

- `create_model`：按 provider 创建底层大模型连接（deepseek / dashscope / OpenAI 兼容）。
- `RoleSpec`：角色配方（角色名 / 系统提示词 / 工具子集 / 视觉 / 上下文 / ReAct 参数）。
- `AgentRole`：角色实体基类，封装一个 AgentScope Agent，固化「装配 → 接受任务 → 执行 → 报告」
  不变主干；子类只填 RoleSpec，赋什么配置就编排成什么角色。

本文件是**智能体包内**的基类，与 `engines/ai/base.py`（引擎协议：AiEngine / TaskRequest /
TaskResult）不是一回事：那个是引擎对外契约，这个是包内实现基类。

边界：本文件不认识任何具体角色——具体角色在同包的 `planner.py` / `executor.py` / `verifier.py`，
各自从 `config.py` 取自己的提示词与工具子集。回复怎么读在 `engines.ai.messaging`，
用量与计价在 `engines.ai.billing`，角色间协作在 `engines.ai.workflow`。
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import ClassVar

from agentscope.agent import Agent, ContextConfig, ReActConfig
from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential
from agentscope.message import (
    DataBlock,
    TextBlock,
    ThinkingBlock,
    ToolCallBlock,
    ToolResultBlock,
    UserMsg,
)
from agentscope.model import DashScopeChatModel, DeepSeekChatModel, OpenAIChatModel

from engines.ai.base import ToolSpec
from engines.ai.billing import model_cost
from engines.ai.messaging import (
    RoleResult,
    collect_from_blocks,
    collect_trace,
    context_summary,
    count_tool_results,
    extract_screenshot,
    extract_screenshot_path,
    prompt_to_input_text,
)
from engines.ai.registry import ConfigurationError
from engines.ai.tools import build_toolkit

from .config import ModelConfig, model_supports_image

# logger 名沿用拆分前的 ai_assistant.model，保持既有日志口径不变（改名会改变日志分类）
logger = logging.getLogger("ai_assistant.model")


# ── 数据模型 ──


@dataclass(frozen=True)
class RoleSpec:
    """创建 Agent 角色的配置（纯数据，无行为）。

    Attributes:
        role: 角色名（planner / executor / verifier），用于 Agent 名、日志与用量按角色聚合。
        prompt: 本角色系统提示词正文（取自 config.py 的对应常量，引擎内唯一真相源）。
        tool_names: 该角色可见的工具名子集（config.py 的 *_TOOLS）。
        vision: 是否多模态（executor / verifier 需截图输入）。
        context_config: 上下文配置（如 {"max_image_num": 5}）。
        react_config: ReAct 循环配置（如 {"max_iters": 8}）。
    """

    role: str
    prompt: str
    tool_names: tuple[str, ...]
    vision: bool = False
    context_config: dict | None = None
    react_config: dict | None = None


# ── provider 兼容分支 ──

# OpenAI 兼容类可承接的 provider（其余走各自专用 SDK 类）
OPENAI_COMPATIBLE_PROVIDERS = frozenset({"openai", "anthropic", "gemini", "custom"})

# 引擎可处理的全部 provider：必须与 Django 侧 VALID_PROVIDERS 相等（一致性测试守护）
SUPPORTED_PROVIDERS = frozenset({"deepseek", "dashscope"}) | OPENAI_COMPATIBLE_PROVIDERS


# ── 模型连接创建（通用工厂，与角色无关）──


def create_model(config: ModelConfig, stream: bool = True, vision: bool = False):
    """按 provider 创建底层 ChatModel 连接（deepseek / dashscope / openai 兼容）。

    Args:
        config: 模型连接配置（provider/model_name/api_key/base_url）。
        stream: 是否流式；角色执行用非流式（stream=False），因需一次拿全 JSON。
        vision: 是否多模态；True 走 OpenAI 兼容类（formatter 支持 image_url 图片）。

    Returns:
        对应 provider 的 ChatModel 实例。

    Raises:
        ConfigurationError: provider 不在 SUPPORTED_PROVIDERS 内（不再静默降级）。
    """
    api_key = config.api_key or ""
    base_url = config.base_url
    if config.provider == "deepseek":
        if vision:
            params = OpenAIChatModel.Parameters(thinking_enable=True)
            return OpenAIChatModel(
                credential=OpenAICredential(api_key=api_key, base_url=base_url),
                model=config.model_name,
                parameters=params,
                stream=stream,
                extra_body={"thinking": {"type": "enabled"}},
            )
        return DeepSeekChatModel(
            credential=DeepSeekCredential(api_key=api_key, base_url=base_url),
            model=config.model_name,
            parameters=DeepSeekChatModel.Parameters(thinking_enable=True),
            stream=stream,
        )
    if config.provider == "dashscope":
        # base_url 为空时交给框架默认值，避免用空串覆盖默认端点
        credential = (
            DashScopeCredential(api_key=api_key, base_url=base_url)
            if base_url
            else DashScopeCredential(api_key=api_key)
        )
        return DashScopeChatModel(
            credential=credential,
            model=config.model_name,
            stream=stream,
        )
    if config.provider in OPENAI_COMPATIBLE_PROVIDERS:
        return OpenAIChatModel(
            credential=OpenAICredential(api_key=api_key, base_url=base_url),
            model=config.model_name,
            stream=stream,
        )
    raise ConfigurationError(
        f"Unsupported provider {config.provider!r}; supported: {sorted(SUPPORTED_PROVIDERS)}"
    )


# ── 角色实体 ──


class AgentRole:
    """Agent 角色实体基类：封装一个 AgentScope Agent，可接受任务并产出任务报告。

    固化「装配 Agent → 接受任务 → 执行(reply) → 生成报告」不变主干；子类只填
    spec（角色配置）与 run()（拼任务输入）。赋什么 RoleSpec 就编排成什么角色。

    设计要点：
    - 类属性 spec 是角色的静态配方（每角色恒定，故用类属性而非构造参数）。
    - _execute 是执行骨架（子类不覆盖）；子类 run() 只拼 content 再调 _execute。
    - 本类是复用基类而非多态接口：三个子类 run() 入参不同（goal / action+idx /
      assertion+截图），共享的是内部机制，不是统一签名。
    - 角色间协作不在此类，在 workflow 包。
    """

    spec: ClassVar[RoleSpec]

    def __init__(
        self,
        config: ModelConfig,
        tools: list[ToolSpec],
        user_id: str = "",
        skill_dirs: list[str] | None = None,
        system_prompt: str | None = None,
    ):
        """装配本角色：1 份角色配置 + 1 份模型连接 + 全量工具 → 1 个 Agent。

        Args:
            config: 本角色的模型连接（provider/model_name/api_key/base_url）。
            tools: 平台全量工具（内部按 self.spec.tool_names 子集装配）。
            user_id: 注入工具包装层（写工具鉴权/归属）。
            skill_dirs: 启用的 skill 文件夹绝对路径（空则不挂 Skill）。
            system_prompt: 覆盖用的系统提示词；缺省取本角色 spec.prompt（config.py 常量）。
        """
        resolved_prompt = self.spec.prompt if system_prompt is None else system_prompt
        self.config = config
        self.system_prompt = resolved_prompt
        self.agent = self._assemble(config, tools, user_id, skill_dirs or [], resolved_prompt)

    @property
    def model_name(self) -> str:
        """本角色底层模型名（用量按此聚合）。"""
        return self.config.model_name

    def _assemble(
        self,
        config: ModelConfig,
        tools: list[ToolSpec],
        user_id: str,
        skill_dirs: list[str],
        system_prompt: str,
    ) -> Agent:
        """装配：模型连接 + 系统提示词 + 工具子集 → AgentScope Agent。"""
        if self.spec.vision and model_supports_image(config.provider, config.model_name) is False:
            # 提醒而非拦截：需要读截图的角色绑了已知纯文本模型时，截图很可能被模型拒绝
            logger.warning(
                "【装配提醒】角色 %s 绑定了不支持图片输入的模型 %s（provider=%s）："
                "该角色需要读截图，请改用多模态模型（如 deepseek-flash）。",
                self.spec.role,
                config.model_name,
                config.provider,
            )
        model = create_model(config, stream=False, vision=self.spec.vision)
        return Agent(
            name=self.spec.role,
            system_prompt=system_prompt,
            model=model,
            toolkit=build_toolkit(
                self._select_tools(tools), user_id=user_id, skill_dirs=skill_dirs
            ),
            context_config=(
                ContextConfig(**self.spec.context_config) if self.spec.context_config else None
            ),
            react_config=ReActConfig(**self.spec.react_config) if self.spec.react_config else None,
        )

    def _select_tools(self, tools: list[ToolSpec]) -> list[ToolSpec]:
        """按 spec.tool_names 子集从全量 tools 选取（保持顺序，跳过不存在的名）。"""
        by_name = {t.name: t for t in tools}
        return [by_name[n] for n in self.spec.tool_names if n in by_name]

    async def ask(self, content: str) -> RoleResult:
        """单轮问答：供调试台 / 工具对本角色说一句话（复用执行骨架，不改动它）。

        Args:
            content: 要发给本角色的纯文本。

        Returns:
            RoleResult（本轮的输出 / 思考 / 用量）。
        """
        return await self._execute(content)

    async def _execute(self, content: str | list) -> RoleResult:
        """执行任务骨架：调本角色 Agent → 打日志 → 解析成任务报告。

        Args:
            content: 拼好的消息内容（str 或块列表），由子类 run() 负责拼装。

        Returns:
            RoleResult：本轮的输出/思考/工具/上下文/用量/费用。
        """
        input_text = prompt_to_input_text(content)
        msg = await self.agent.reply(UserMsg(name="user", content=content))
        self._dump_reply(msg)
        return self._to_result(msg, input_text=input_text)

    def _to_result(self, msg, *, input_text: str = "") -> RoleResult:
        """把一次 reply + 完整 context 解析成任务报告。

        最终 reply 的 TextBlock → output（供 JSON 契约解析）；
        思考 / 工具调用与返回扫整段 agent.state.context（ReAct 中间轮在 context 里）。
        """
        output_parts: list[str] = []
        for block in getattr(msg, "content", None) or []:
            if isinstance(block, TextBlock):
                output_parts.append(block.text)
        context = getattr(self.agent.state, "context", None) or []
        thinking, tool_usage = collect_trace(context)
        # context 若为空（极端实现差异），回退扫最终 reply 块
        if not thinking and not tool_usage:
            thinking, tool_usage = collect_from_blocks(getattr(msg, "content", None) or [])
        usage = self._usage_dict(msg)
        return RoleResult(
            role=self.spec.role,
            model_name=self.model_name,
            output="".join(output_parts),
            input_text=input_text,
            thinking=thinking,
            tool_usage=tool_usage,
            context=context_summary(context),
            screenshot=extract_screenshot(getattr(msg, "content", None)),
            screenshot_path=extract_screenshot_path(context),
            usage=usage,
            cost=model_cost(self.config.provider, self.model_name, usage),
        )

    def tool_results_seen(self) -> int:
        """当前上下文里已有的工具返回条数。

        上下文是**整个任务累积**的，工作流用这个数字切出「本步新增」的工具返回，
        否则本步的动作发出时刻会取到上一步的值（真机验证时踩到过）。
        """
        return count_tool_results(getattr(self.agent.state, "context", None) or [])

    def _usage_dict(self, msg) -> dict:
        """从一次 reply 提取本轮用量 dict（屏蔽 ChatUsage 对象差异）。"""
        u = getattr(msg, "usage", None)
        return {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "cache_input_tokens": int(getattr(u, "cache_input_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0),
        }

    def _last_message(self, fallback=None):
        """取 agent 最近一条消息（打日志用）；无上下文回退 fallback。"""
        context = getattr(self.agent.state, "context", None)
        return context[-1] if context else fallback

    def _dump_reply(self, msg) -> None:
        """打印一次 reply 的完整内容块（截图只打 media_type 脱敏，供开发者调试）。

        工具结果的详细返回已由 tool_wrapper 的【工具返回】日志负责，此处只打 name/state。
        """
        target = self._last_message(msg)
        logger.info(
            "===== %s | role=%s name=%s =====",
            self.spec.role,
            getattr(target, "role", ""),
            getattr(target, "name", ""),
        )
        for block in getattr(target, "content", None) or []:
            if isinstance(block, ThinkingBlock):
                logger.info("  [思考] %s", block.thinking)
            elif isinstance(block, ToolCallBlock):
                logger.info("  [工具调用] %s 入参=%s", block.name, block.input)
            elif isinstance(block, ToolResultBlock):
                logger.info("  [工具结果] %s state=%s", block.name, block.state)
            elif isinstance(block, DataBlock):
                logger.info("  [数据/截图] media_type=%s", getattr(block.source, "media_type", ""))
            elif isinstance(block, TextBlock):
                logger.info("  [文本] %s", block.text)
            else:
                logger.info("  [块] %s", type(block).__name__)

    def reset_context(self) -> None:
        """清空自己的上下文（每步开始前调用，避免上一步污染）。"""
        self.agent.state.context.clear()
