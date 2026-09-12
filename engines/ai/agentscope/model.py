"""模型层：Agent 角色 —— 配置角色、创建角色、接受任务、执行并产出任务报告。

- RoleSpec：创建 Agent 角色的配置（角色名/系统提示词/工具子集/视觉/上下文/ReAct 参数）。
- AgentRole：角色实体基类，封装一个 AgentScope Agent，固化「装配 → 接受任务 → 执行 → 报告」
  不变主干；子类只填 RoleSpec，赋什么配置就编排成什么角色。
- RoleResult：一次任务执行的任务报告（输出/思考/工具/截图/用量/成本），供用户了解与开发者调试。
- 边界：本模块只创建单角色，不编排角色间协作（planner → executor ↔ verifier 的流转在 workflow.py）。
"""

from __future__ import annotations

import json
import logging

from dataclasses import dataclass
from typing import Any, ClassVar

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
from pydantic import BaseModel, Field

from engines.ai.base import ToolSpec

from .billing import model_cost
from .config import (
    DEVICE_PLANNER_TOOLS,
    PLANNER_PROMPT,
    VERIFIER_PROMPT,
    VERIFIER_TOOLS,
    VISION_PROMPT,
    VISION_TOOLS,
    DeviceExecutionConfig,
    ModelConfig,
)
from .tool_wrapper import build_toolkit

logger = logging.getLogger("ai_assistant.model")


def _screenshot_path_from_tool_output(output) -> str:
    """从 screenshot_page 工具结果里解析 summary.screenshot_path（工具真相，非模型编造）。"""
    for text in _tool_output_text_parts(output):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        path = str(obj.get("screenshot_path") or "").replace("\\", "/").strip()
        if path:
            return path
    return ""


def _tool_output_text_parts(output) -> list[str]:
    """工具 output → 纯文本片段（忽略 DataBlock 二进制）。"""
    texts: list[str] = []
    if isinstance(output, str):
        if output.strip():
            texts.append(output)
        return texts
    if isinstance(output, list):
        for block in output:
            if isinstance(block, TextBlock) and block.text:
                texts.append(block.text)
            elif isinstance(block, str) and block.strip():
                texts.append(block)
    return texts


def _sanitize_tool_output_text(output, *, limit: int = 800) -> str:
    """工具返回 → 可落库短文本：保留 summary/路径，剔除 base64。"""
    parts: list[str] = []
    for text in _tool_output_text_parts(output):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            parts.append(text)
            continue
        if not isinstance(obj, dict):
            parts.append(text)
            continue
        # 去掉可能夹带的超大字段
        cleaned = {
            k: v
            for k, v in obj.items()
            if k not in ("base64", "image", "data") and not (
                isinstance(v, str) and len(v) > 500 and k.endswith("_b64")
            )
        }
        # screenshot_page：优先只留可读摘要 + 路径
        if "screenshot_path" in cleaned or "screenshot_name" in cleaned:
            slim = {
                k: cleaned[k]
                for k in (
                    "serial",
                    "package",
                    "activity",
                    "screen_w",
                    "screen_h",
                    "screenshot_path",
                    "screenshot_name",
                )
                if k in cleaned
            }
            parts.append(json.dumps(slim or cleaned, ensure_ascii=False, default=str))
        else:
            parts.append(json.dumps(cleaned, ensure_ascii=False, default=str))
    # DataBlock 仅记占位（图已由 screenshot_path / 验收证据落盘）
    if isinstance(output, list) and any(isinstance(b, DataBlock) for b in output):
        if not parts:
            parts.append("[image]")
    text = "\n".join(parts).strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def _prompt_to_input_text(content: str | list) -> str:
    """发给 Agent 的 content → 可展示的输入文本（忽略图片块）。"""
    if isinstance(content, str):
        return content.strip()
    parts: list[str] = []
    for block in content or []:
        if isinstance(block, TextBlock) and block.text:
            parts.append(block.text)
        elif isinstance(block, str) and block.strip():
            parts.append(block)
    return "\n".join(parts).strip()


# ── 数据模型 ──


@dataclass(frozen=True)
class RoleSpec:
    """创建 Agent 角色的配置（纯数据，无行为）。

    Attributes:
        role: 角色名（planner / executor / verifier），用于 Agent 名、日志与用量按角色聚合。
        prompt: 系统提示词（config.py 的 *_PROMPT）。
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


class RoleResult(BaseModel):
    """一次任务执行的任务报告（角色执行任务的完整产出）。

    把 AgentScope 的原始 reply（消息块 + usage）解析成语义化字段，屏蔽框架差异。
    供用户了解结果（output/screenshot/cost），供开发者调试（thinking/tool_usage/usage）。
    """

    role: str = Field(default="", description="本角色：planner / executor / verifier")
    model_name: str = Field(default="", description="底层模型名（用量按此聚合）")
    output: str = Field(default="", description="输出结果文本（TextBlock 拼接，供 JSON 解析）")
    input_text: str = Field(default="", description="本轮发给 Agent 的用户输入文本（详情页「输入」）")
    thinking: list[str] = Field(default_factory=list, description="思考过程（ThinkingBlock 逐个）")
    tool_usage: list[dict] = Field(
        default_factory=list,
        description="工具使用记录（type=call/result/image + name/入参/返回/状态）",
    )
    context: list[dict] = Field(
        default_factory=list,
        description="自己上下文摘要（每条仅 role + 截断文本，脱敏图片）",
    )
    screenshot: Any = Field(
        default=None,
        description="最后一张截图 DataBlock（executor 产出 → 传给 verifier）",
    )
    screenshot_path: str = Field(
        default="",
        description="本轮最后一次 screenshot_page 落盘相对 MEDIA 路径（验收证据用）",
    )
    usage: dict = Field(
        default_factory=dict,
        description="本轮用量（input_tokens/output_tokens/cache_input_tokens/cache_creation_input_tokens）",
    )
    cost: float = Field(default=0.0, description="本轮费用（元，仅 DeepSeek 计费，其余 0）")


# ── 模型连接创建（通用工厂，与角色无关）──


def create_model(config: ModelConfig, stream: bool = True, vision: bool = False):
    """按 provider 创建底层 ChatModel 连接（deepseek / dashscope / openai 兼容）。

    Args:
        config: 模型连接配置（provider/model_name/api_key/base_url）。
        stream: 是否流式；角色执行用非流式（stream=False），因需一次拿全 JSON。
        vision: 是否多模态；True 走 OpenAI 兼容类（formatter 支持 image_url 图片）。

    Returns:
        对应 provider 的 ChatModel 实例。
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
    - 角色间协作不在此类，在 workflow.py。
    """

    spec: ClassVar[RoleSpec]

    def __init__(
        self,
        config: ModelConfig,
        tools: list[ToolSpec],
        user_id: str = "",
        skill_dirs: list[str] | None = None,
    ):
        """装配本角色：1 份角色配置 + 1 份模型连接 + 全量工具 → 1 个 Agent。

        Args:
            config: 本角色的模型连接（provider/model_name/api_key/base_url）。
            tools: 平台全量工具（内部按 self.spec.tool_names 子集装配）。
            user_id: 注入工具包装层（写工具鉴权/归属）。
            skill_dirs: 启用的 skill 文件夹绝对路径（空则不挂 Skill）。
        """
        self.config = config
        self.agent = self._assemble(config, tools, user_id, skill_dirs or [])

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
    ) -> Agent:
        """装配：模型连接 + 系统提示词 + 工具子集 → AgentScope Agent。"""
        model = create_model(config, stream=False, vision=self.spec.vision)
        return Agent(
            name=self.spec.role,
            system_prompt=self.spec.prompt,
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

    async def _execute(self, content: str | list) -> RoleResult:
        """执行任务骨架：调本角色 Agent → 打日志 → 解析成任务报告。

        Args:
            content: 拼好的消息内容（str 或块列表），由子类 run() 负责拼装。

        Returns:
            RoleResult：本轮的输出/思考/工具/上下文/用量/费用。
        """
        input_text = _prompt_to_input_text(content)
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
        thinking, tool_usage = self._collect_trace_from_context()
        # context 若为空（极端实现差异），回退扫最终 reply 块
        if not thinking and not tool_usage:
            thinking, tool_usage = self._collect_trace_from_blocks(
                getattr(msg, "content", None) or []
            )
        usage = self._usage_dict(msg)
        return RoleResult(
            role=self.spec.role,
            model_name=self.model_name,
            output="".join(output_parts),
            input_text=input_text,
            thinking=thinking,
            tool_usage=tool_usage,
            context=self._context_summary(),
            screenshot=self._extract_screenshot(getattr(msg, "content", None)),
            screenshot_path=self._extract_screenshot_path(),
            usage=usage,
            cost=model_cost(self.config.provider, self.model_name, usage),
        )

    def _collect_trace_from_context(self) -> tuple[list[str], list[dict]]:
        """从 agent 完整上下文收集思考 + 工具调用/返回（脱敏，无 base64）。"""
        thinking: list[str] = []
        tool_usage: list[dict] = []
        context = getattr(self.agent.state, "context", None) or []
        for msg in context:
            t, u = self._collect_trace_from_blocks(getattr(msg, "content", None) or [])
            thinking.extend(t)
            tool_usage.extend(u)
        return thinking, tool_usage

    def _collect_trace_from_blocks(self, blocks) -> tuple[list[str], list[dict]]:
        """从一组消息内容块收集思考 + 工具（脱敏）。"""
        thinking: list[str] = []
        tool_usage: list[dict] = []
        for block in blocks:
            if isinstance(block, ThinkingBlock) and block.thinking:
                thinking.append(block.thinking)
            elif isinstance(block, ToolCallBlock):
                tool_usage.append(
                    {"type": "call", "name": block.name, "input": block.input}
                )
            elif isinstance(block, ToolResultBlock):
                row: dict = {
                    "type": "result",
                    "name": block.name,
                    "state": getattr(block, "state", ""),
                }
                out_text = _sanitize_tool_output_text(block.output)
                if out_text:
                    row["output"] = out_text
                path = _screenshot_path_from_tool_output(block.output)
                if path:
                    row["screenshot_path"] = path
                tool_usage.append(row)
            elif isinstance(block, DataBlock):
                tool_usage.append(
                    {
                        "type": "image",
                        "media_type": getattr(block.source, "media_type", ""),
                    }
                )
        return thinking, tool_usage

    def _usage_dict(self, msg) -> dict:
        """从一次 reply 提取本轮用量 dict（屏蔽 ChatUsage 对象差异）。"""
        u = getattr(msg, "usage", None)
        return {
            "input_tokens": int(getattr(u, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(u, "output_tokens", 0) or 0),
            "cache_input_tokens": int(getattr(u, "cache_input_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0),
        }

    def _context_summary(self) -> list[dict]:
        """上下文摘要：每条消息只留 role + 截断 500 字文本（脱敏图片）。"""
        summary = []
        context = getattr(self.agent.state, "context", None)
        for m in context or []:
            content = getattr(m, "content", "")
            text = (
                content
                if isinstance(content, str)
                else "".join(getattr(b, "text", "") for b in (content or []) if hasattr(b, "text"))
            )
            summary.append({"role": getattr(m, "role", ""), "text": text[:500]})
        return summary

    def _extract_screenshot(self, content) -> Any:
        """从 reply 内容块里取最后一张截图 DataBlock（倒序找，返回最后一个）。"""
        for block in reversed(content or []):
            if isinstance(block, DataBlock):
                return block
            if isinstance(block, ToolResultBlock):
                out = block.output
                if isinstance(out, DataBlock):
                    return out
                if isinstance(out, list):
                    for b in reversed(out):
                        if isinstance(b, DataBlock):
                            return b
        return None

    def _extract_screenshot_path(self) -> str:
        """从本轮 agent 上下文里取最后一次 screenshot_page 的落盘相对路径。

        扫完整 context（工具结果在中间消息，不在最终 reply），路径来自工具 summary。
        """
        context = getattr(self.agent.state, "context", None) or []
        last = ""
        for msg in context:
            for block in getattr(msg, "content", None) or []:
                if not isinstance(block, ToolResultBlock):
                    continue
                if getattr(block, "name", "") != "screenshot_page":
                    continue
                path = _screenshot_path_from_tool_output(block.output)
                if path:
                    last = path
        return last

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


# ── 具体角色 ──


class PlannerRole(AgentRole):
    """规划角色：接受用户需求，输出步骤计划（goal + steps）。"""

    spec = RoleSpec(
        role="planner",
        prompt=PLANNER_PROMPT,
        tool_names=tuple(DEVICE_PLANNER_TOOLS),
    )

    async def run(self, goal: str) -> RoleResult:
        """接受任务：用户一句话 UI 操作需求。

        Args:
            goal: 用户一句话 UI 操作需求。

        Returns:
            RoleResult（output 为 {"plan": {...}} 的 JSON 文本）。
        """
        return await self._execute(goal)


class ExecutorRole(AgentRole):
    """执行角色：接受单个操作步骤，在设备上执行并输出结果与截图。

    多模态（vision=True）：靠截图看图定位元素；ReAct 最多 8 轮（max_iters=8）；
    上下文最多保留 5 张图（max_image_num=5）控制 token。
    """

    spec = RoleSpec(
        role="executor",
        prompt=VISION_PROMPT,
        tool_names=tuple(VISION_TOOLS),
        vision=True,
        context_config={"max_image_num": 5},
        react_config={"max_iters": 8},
    )

    async def run(
        self,
        serial: str,
        action: str,
        idx: int,
        total: int,
        retry_hint: str = "",
    ) -> RoleResult:
        """接受任务：在指定设备上执行一个操作步骤。

        Args:
            serial: 目标设备 serial。
            action: 本步骤要执行的一个操作。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            retry_hint: 上次验收失败回灌的修正提示（空串 = 首次执行）。

        Returns:
            RoleResult（output 为 {"action","result","message"} JSON；screenshot 为操作结果截图）。
        """
        prompt = f"当前设备 serial：{serial}\n请执行以下操作（第 {idx}/{total} 步）：\n{action}"
        if retry_hint:
            prompt += f"\n<feedback>上次执行未通过验收，请修正后重做：\n{retry_hint}</feedback>"
        return await self._execute(prompt)


def _force_keep_local_screenshot(handler):
    """验收工具包装：无论模型是否传 keep_local，一律保留路径回传。"""

    def wrapped(serial: str, keep_local: bool = True, user_id: str = "", **kwargs):
        return handler(serial, keep_local=True, user_id=user_id, **kwargs)

    wrapped.__name__ = getattr(handler, "__name__", "screenshot_page")
    wrapped.__doc__ = getattr(handler, "__doc__", "") or ""
    return wrapped


class VerifierRole(AgentRole):
    """验收角色：对比断言与执行截图，输出是否通过（验收是否真实达成）。"""

    spec = RoleSpec(
        role="verifier",
        prompt=VERIFIER_PROMPT,
        tool_names=tuple(VERIFIER_TOOLS),
        vision=True,
        context_config={"max_image_num": 5},
    )

    def _select_tools(self, tools: list[ToolSpec]) -> list[ToolSpec]:
        """验收子集：screenshot_page 强制 keep_local=True，保证证据路径回传。"""
        selected = super()._select_tools(tools)
        out: list[ToolSpec] = []
        for spec in selected:
            if spec.name == "screenshot_page":
                out.append(
                    ToolSpec(
                        name=spec.name,
                        handler=_force_keep_local_screenshot(spec.handler),
                        read_only=spec.read_only,
                        auto_allow=spec.auto_allow,
                    )
                )
            else:
                out.append(spec)
        return out

    async def run(
        self,
        serial: str,
        assertion: str,
        idx: int,
        total: int,
        exec_result: str,
        exec_message: str,
        screenshot=None,
    ) -> RoleResult:
        """接受任务：对比断言与执行截图，判断操作是否成功。

        Args:
            serial: 目标设备 serial。
            assertion: 本步骤的断言（期望的可观察结果）。
            idx: 当前步骤序号（1 起）。
            total: 总步骤数。
            exec_result: 执行模型的 result（PASS/FAIL）。
            exec_message: 执行模型的 message。
            screenshot: 执行模型产出的操作结果截图（DataBlock，可空）。

        Returns:
            RoleResult（output 为 {"action","assert","actual","result"} JSON）。
        """
        text = (
            f"当前设备 serial：{serial}\n"
            f"断言 assert：{assertion}\n"
            f"执行结果：result={exec_result}，message={exec_message}\n"
            f"请截图确认，对比断言与实际结果，判断操作是否成功（第 {idx}/{total} 步）。"
        )
        content: list = [TextBlock(text=text)]
        if screenshot is not None:
            content.append(screenshot)
        return await self._execute(content)


# ── 装配工厂 ──


def build_device_models(
    config: DeviceExecutionConfig,
    tools: list[ToolSpec],
    user_id: str = "",
    skill_dirs: list[str] | None = None,
) -> tuple[PlannerRole, ExecutorRole, VerifierRole]:
    """按三角色配置创建三个角色对象（planner / executor / verifier）。

    Args:
        config: 三角色模型连接配置 + max_loops。
        tools: 平台全量工具（各角色按自己的 RoleSpec.tool_names 子集取用）。
        user_id: 注入工具包装层（写工具鉴权/归属）。
        skill_dirs: 启用的 skill 文件夹绝对路径。

    Returns:
        (planner, executor, verifier) 三个角色对象。
    """
    dirs = skill_dirs or []
    return (
        PlannerRole(config.planner, tools, user_id, dirs),
        ExecutorRole(config.executor, tools, user_id, dirs),
        VerifierRole(config.verifier, tools, user_id, dirs),
    )
