"""智能体基类：模型连接创建（`create_model`）+ 角色配方（`RoleSpec`）+ 角色基类（`AgentRole`）。

`AgentRole` 封装一个 AgentScope Agent，固化「装配 → 接受任务 → 执行(reply) → 生成报告」主干，
子类只填 `RoleSpec` 与 `run()`。本模块不认识任何具体角色，具体角色在同包的
`planner.py` / `executor.py` / `verifier.py`。
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import ClassVar

from agentscope.agent import Agent, ContextConfig, ReActConfig
from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential
from agentscope.message import (
    DataBlock,
    Msg,
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
    EventStreamRecorder,
    RoleResult,
    collect_from_blocks,
    collect_trace,
    context_summary,
    extract_screenshot,
    extract_screenshot_path,
    prompt_to_input_text,
)
from engines.ai.process_log import SCOPE_STANDALONE, AgentProcessLog
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

# 平台支持的 provider（与 Django 侧 VALID_PROVIDERS 相等，由一致性测试守护）：
# deepseek / dashscope 两项，无 OpenAI 兼容兜底分支。
SUPPORTED_PROVIDERS = frozenset({"deepseek", "dashscope"})


# ── 模型连接创建（通用工厂，与角色无关）──


def create_model(config: ModelConfig, stream: bool = True, vision: bool = False):
    """按 provider 创建底层 ChatModel 连接。

    Args:
        config: 模型连接配置（provider/model_name/api_key/base_url）。
        stream: 是否流式。角色执行传 False（需一次拿全 JSON）。
        vision: 是否多模态；True 时按 DeepSeek 多模态档走 OpenAI 兼容客户端以支持图片输入。

    Returns:
        对应 provider 的 ChatModel 实例。

    Raises:
        ConfigurationError: provider 不在 SUPPORTED_PROVIDERS 内。
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
    raise ConfigurationError(
        f"Unsupported provider {config.provider!r}; supported: {sorted(SUPPORTED_PROVIDERS)}"
    )


# ── 角色实体 ──


class AgentRole:
    """Agent 角色实体基类：封装一个 AgentScope Agent，接受任务并产出任务报告。

    子类填 `spec`（角色配方）并实现 `run()`（拼任务输入）；执行骨架 `_execute` 不覆盖。
    """

    spec: ClassVar[RoleSpec]

    def __init__(
        self,
        config: ModelConfig,
        tools: list[ToolSpec],
        user_id: str = "",
        skill_dirs: list[str] | None = None,
        system_prompt: str | None = None,
        media_root: str = "",
        log_path: str = "",
        task_id: int = 0,
    ):
        """装配本角色：1 份角色配置 + 1 份模型连接 + 全量工具 → 1 个 Agent。

        Args:
            config: 本角色的模型连接（provider/model_name/api_key/base_url）。
            tools: 平台全量工具（内部按 `self.spec.tool_names` 取子集；同名设备动作工具由引擎自带）。
            user_id: 注入工具包装层，用于写工具的鉴权与归属。
            skill_dirs: 启用的 skill 文件夹绝对路径；空则不挂 Skill。
            system_prompt: 覆盖用的系统提示词；None 时取 `self.spec.prompt`。
            media_root: 截图等证据的落盘根目录；空则用引擎默认目录。
            log_path: 过程日志基路径；空则用 `<当前目录>/logs/agents.log`。
            task_id: 任务 id（只用于过程日志的任务与步骤标识；0 表示无任务上下文）。
        """
        resolved_prompt = self.spec.prompt if system_prompt is None else system_prompt
        self.config = config
        self.system_prompt = resolved_prompt
        self.media_root = str(media_root or "")
        self.task_id = int(task_id or 0)
        self.process_log = AgentProcessLog(log_path)
        self._scope = self.scope_label("")
        self.agent = self._assemble(config, tools, user_id, skill_dirs or [], resolved_prompt)

    def scope_label(self, stage: str) -> str:
        """过程日志的「任务与步骤」列：有任务时带任务号，无任务时如实写独立运行。"""
        detail = str(stage or "").strip()
        if not self.task_id:
            return f"{SCOPE_STANDALONE} · {detail}" if detail else SCOPE_STANDALONE
        return f"任务 {self.task_id} · {detail}" if detail else f"任务 {self.task_id}"

    def mark_scope(self, stage: str) -> None:
        """标记本角色当前所处的阶段（写进过程日志的任务与步骤列）。"""
        self._scope = self.scope_label(stage)

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
        """按 `spec.tool_names` 从全量 tools 选取（保持顺序，跳过不存在的名）。

        设备动作工具由引擎自带（`tool_device`）：同名注入条目被跳过，注入实现不再可见。
        """
        from engines.ai.tools.tool_device import device_tool_specs

        # 属性缺省按空处理：本方法也允许按 spec 直接调用（不带装配实例）
        media_root = str(getattr(self, "media_root", "") or "")
        owned = {spec.name: spec for spec in device_tool_specs(media_root)}
        injected = {tool.name: tool for tool in tools}
        selected: list[ToolSpec] = []
        for name in self.spec.tool_names:
            if name in owned:
                if name in injected:
                    logger.debug("设备动作工具 %s 由引擎自带，跳过注入的同名实现", name)
                selected.append(owned[name])
            elif name in injected:
                selected.append(injected[name])
        return selected

    async def ask(self, content: str) -> RoleResult:
        """单轮问答：把一句话发给本角色并取回任务报告。

        Args:
            content: 要发给本角色的纯文本。

        Returns:
            RoleResult（本轮的输出 / 思考 / 用量）。
        """
        return await self._execute(content)

    async def _execute(self, content: str | list) -> RoleResult:
        """执行任务骨架：消费事件流（实时写过程日志）→ 解析成任务报告。

        Args:
            content: 拼好的消息内容（str 或块列表），由子类 run() 负责拼装。

        Returns:
            RoleResult：本轮的输出/思考/工具/上下文/用量/费用。
        """
        input_text = prompt_to_input_text(content)
        recorder = EventStreamRecorder(
            self.process_log,
            role=self.spec.role,
            model=self.model_name,
            scope=self._scope,
        )
        msg = await self._stream_reply(content, recorder)
        self._dump_reply(msg)
        return self._to_result(msg, input_text=input_text, recorder=recorder)

    async def _stream_reply(self, content: str | list, recorder: EventStreamRecorder):
        """消费 `reply_stream`：事件到达即写过程日志，末尾取回最终消息。

        非流式模型同样逐块给出事件，两种档位走同一路径。
        """
        final = None
        async for item in self.agent.reply_stream(
            UserMsg(name="user", content=content), yield_final_msg=True
        ):
            if isinstance(item, Msg):
                final = item
                continue
            recorder.consume(item)
        recorder.finish()
        return final if final is not None else self._last_message()

    def _to_result(
        self,
        msg,
        *,
        input_text: str = "",
        recorder: EventStreamRecorder | None = None,
    ) -> RoleResult:
        """把一次回复 + 完整 context 解析成任务报告。

        思考与工具记录优先取事件流汇总（`recorder`）；事件流缺失时回退扫整段 context。
        """
        output_parts: list[str] = []
        for block in getattr(msg, "content", None) or []:
            if isinstance(block, TextBlock):
                output_parts.append(block.text)
        context = getattr(self.agent.state, "context", None) or []
        thinking = list(getattr(recorder, "thinking", []) or [])
        tool_usage = list(getattr(recorder, "tool_usage", []) or [])
        if not thinking and not tool_usage:
            thinking, tool_usage = collect_trace(context)
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
            screenshot_path=str(getattr(recorder, "screenshot_path", "") or "")
            or extract_screenshot_path(context),
            usage=usage,
            cost=model_cost(self.config.provider, self.model_name, usage),
        )

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
        """取 agent 最近一条消息；无上下文时返回 fallback。"""
        context = getattr(self.agent.state, "context", None)
        return context[-1] if context else fallback

    def _dump_reply(self, msg) -> None:
        """把一次 reply 的内容块写进日志（截图只记 media_type，工具结果只记 name/state）。"""
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
