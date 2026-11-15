"""
文件名: ➡️ agent_builders.py 🏁
路径: ➡️ engines/agents/agent_builders.py 🏁
模块功能：➡️ 本文件集中 LLM agents（chat / ReAct）：UI 执行/验收与用例编写相关角色 🏁
Python 调试：➡️ python -m engines.agents.agent_builders 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.2.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. RoleConfig / ToolsConfig / ContextConfig / ReActConfig: 过渡期再导出四分段类型
2. AgentRoleFactory: 用已建好的模型 + 四分段配置装配 agentscope.Agent
3. build_ui_executor / build_ui_verifier / build_case_*: 角色键 → 模型 + 四分段 + 工具包
4. build_knowledge_chat: 知识库文字问答角色（纯文字，不装语音合成）
5. executor_agent / verifier_agent / build_executor / build_verifier: 兼容旧名的快捷入口
6. _build: 兼容入口，读两张表后转调 assistant.create_chat_agent
🏁
关联模块：➡️
1. engines.agents.config.role_types: 四分段类型仍由本文件再导出，供旧调用方使用
2. engines.agents.config.role_types: 导入四分段类型
3. engines.agents.assistant: 导入 create_chat_agent，只转调聊天出口
4. engines.agents.config.config: 导入 load_agent_config / load_model_config，读两张表
5. engines.agents.middleware: 延迟导入 build_agent_middlewares，仅 Factory 直接构造时使用
6. engines.agents.tools_config: 延迟导入各角色工具包
7. engines.agents.role_sys_prompts: 导入 resolve_system_prompt / with_app_info，转调前把 token 解成正文
🏁
测试：➡️
1. tests/engines/agents/test_agents.py: 连通性：按 YAML 创建 Agent 并能拿到一轮回复
2. tests/graybox/unit/test_case_authoring_roles.py: 用例编写/验收角色的装配与成对运行入口
3. tests/graybox/unit/test_case_run_continuity.py: 一批用例的执行连续性
4. tests/graybox/unit/test_forced_handover_thinking.py: 强制交卷时关闭思考
5. tests/graybox/unit/test_model_retry_middleware.py: 模型重试与回退中间件
🏁
"""

from __future__ import annotations

from agentscope.agent import Agent
from agentscope.agent import (
    ContextConfig as AsContextConfig,
)
from agentscope.agent import (
    ReActConfig as AsReActConfig,
)
from agentscope.model import ChatModelBase
from agentscope.tool import Toolkit

from engines.agents.assistant import create_chat_agent
from engines.agents.config.config import load_agent_config, load_model_config
from engines.agents.config.role_types import (
    ContextConfig,
    ReActConfig,
    RoleConfig,
    ToolsConfig,
)
from engines.agents.role_sys_prompts import resolve_system_prompt, with_app_info

# 过渡期再导出：历史调用方仍可 from agent_builders import RoleConfig 等；
# 类型定义归属 config.role_types（Harness 装载层内部面，非长期公共 API）。
__all__ = [
    "RoleConfig",
    "ToolsConfig",
    "ContextConfig",
    "ReActConfig",
    "AgentRoleFactory",
    "build_ui_executor",
    "build_ui_verifier",
    "build_case_writer",
    "build_case_verifier",
    "build_knowledge_chat",
    "build_executor",
    "build_verifier",
    "executor_agent",
    "verifier_agent",
]


def _as_react_config(react: ReActConfig) -> AsReActConfig:
    """role 侧 ReActConfig → agentscope.ReActConfig。"""
    return AsReActConfig(
        max_iters=react.max_iters,
        structured_output_grace_iters=react.structured_output_grace_iters,
        stop_on_reject=react.stop_on_reject,
        interruption_raise_cancelled_error=react.interruption_raise_cancelled_error,
    )


def _as_context_config(context: ContextConfig) -> AsContextConfig:
    """role 侧 ContextConfig → agentscope.ContextConfig。"""
    return AsContextConfig(
        trigger_ratio=context.trigger_ratio,
        reserve_ratio=context.reserve_ratio,
        tool_result_limit=context.tool_result_limit,
        max_image_num=context.max_image_num,
    )


def _default_middlewares(fallback_model: ChatModelBase | None, *, with_events: bool = True) -> list:
    """默认中间件装配：事件流在外，模型重试在内。

    Args:
        fallback_model: 已建好的备用模型；None 表示不启用回退。
        with_events: 是否挂回复事件流。SOP 传 False。

    Returns:
        交给 `Agent(middlewares=...)` 的列表。
    """
    from engines.agents.middleware import build_agent_middlewares

    return build_agent_middlewares(fallback_model=fallback_model, with_events=with_events)


class AgentRoleFactory:
    """用已建好的模型 + Role/Tools/Context/ReAct 四分段配置创建 agentscope.Agent。"""

    def __init__(
        self,
        model: ChatModelBase,
        role: RoleConfig,
        *,
        tools: ToolsConfig | None = None,
        context: ContextConfig | None = None,
        react: ReActConfig | None = None,
        toolkit: Toolkit | None = None,
        middlewares: list | None = None,
        fallback_model: ChatModelBase | None = None,
        with_events: bool = True,
    ) -> None:
        """
        Args:
            model: 已建好的聊天模型实例（由 `engines.agents.models` 创建）。
            role: 角色名与系统提示词。
            tools: 工具配置；None 时用空 Toolkit()。
            context: 上下文配置；None 用 dataclass 默认。
            react: ReAct 配置；None 用 dataclass 默认。
            toolkit: 显式工具包，优先于 tools.toolkit。
            middlewares: 显式中间件；None 时自动装配。
            fallback_model: 备用模型；仅自动装配中间件时使用。
            with_events: 是否挂回复事件流。SOP 传 False。

        Raises:
            TypeError: `role` 不是 RoleConfig。
        """
        if not isinstance(role, RoleConfig):
            raise TypeError(f"role 须为 RoleConfig，收到: {type(role).__name__}")

        self.model = model
        self.role = role
        if toolkit is not None:
            self.tools = ToolsConfig(toolkit=toolkit)
        elif tools is not None:
            self.tools = tools
        else:
            self.tools = ToolsConfig(toolkit=Toolkit())
        self.context = context if context is not None else ContextConfig()
        self.react = react if react is not None else ReActConfig()
        self._middlewares = middlewares
        self.fallback_model = fallback_model
        self.with_events = with_events

    def create(self) -> Agent:
        """组装 agentscope.Agent。

        供已持有模型实例的调用方使用。`build_*` 不走这里，它们转调 assistant。

        Returns:
            新的 Agent 实例（每次调用都是独立实例）。
        """
        middlewares = (
            self._middlewares
            if self._middlewares is not None
            else _default_middlewares(self.fallback_model, with_events=self.with_events)
        )
        from engines.agents.assistant.create import create_from_model

        return create_from_model(
            self.model,
            name=self.role.name,
            system_prompt=self.role.system_prompt,
            toolkit=self.tools.toolkit,
            middlewares=middlewares,
            context=_as_context_config(self.context),
            react=_as_react_config(self.react),
            with_events=self.with_events,
        )


def _prepared_roles(role_key: str) -> dict:
    """读整张角色表，并把该键的提示词 token 解成正文。

    Args:
        role_key: agent_config.yaml 的顶层键。

    Returns:
        整张角色表的副本；目标节的 system_prompt 已是正文。

    Raises:
        ValueError: 角色键不存在，或提示词 token 无法解析。
    """
    roles = load_agent_config()
    section = roles.get(role_key)
    if not isinstance(section, dict):
        raise ValueError(f"agent_config 缺少节 {role_key!r}")
    role = dict(section.get("RoleConfig") or {})
    where = f"{role_key}.RoleConfig"
    prompt = resolve_system_prompt(role.get("system_prompt"), where=where)
    role["system_prompt"] = with_app_info(prompt, role.get("app_info"))
    prepared = dict(roles)
    prepared[role_key] = {**section, "RoleConfig": role}
    return prepared


# ── 四大主角色（配置全在 agent_config.yaml）──────────────────────────


def _build(
    role_key: str,
    toolkit: Toolkit | None = None,
    *,
    middlewares: list | None = None,
    with_events: bool = True,
    modules: tuple[str, ...] | None = None,
    extra: list | None = None,
) -> Agent:
    """读两张表并转调 assistant。

    Args:
        role_key: agent_config.yaml 的顶层键。
        toolkit: 已装好的工具包；None 时按角色节的模块名装。
        middlewares: 显式中间件；None 走 assistant 默认装配。
        with_events: SOP 自己记录事件时传 False。
        modules: 要激活的模块；None 时从角色节读取。
        extra: 追加到默认中间件之前的实例。None 不追加。

    Returns:
        新的 Agent。已授予的工具组处于激活状态。
    """
    from engines.agents.tools_config import (
        activate_modules,
        build_toolkit_for_modules,
        role_modules,
    )

    roles = _prepared_roles(role_key)
    granted = role_modules(roles, role_key) if modules is None else modules
    agent = create_chat_agent(
        roles,
        load_model_config(),
        role_key,
        toolkit=toolkit if toolkit is not None else build_toolkit_for_modules(granted),
        middlewares=middlewares,
        extra=extra,
        with_events=with_events,
    )
    if toolkit is None:
        activate_modules(agent, granted)
    return agent


def build_ui_executor(*, extra_middlewares: list | None = None, with_events: bool = False) -> Agent:
    """UI 控制执行角色：按角色节授予 device / observe，创建时激活。

    Args:
        extra_middlewares: 只给本次实例追加的中间件。SOP 不传。
        with_events: SOP 自己记录事件，默认 False。单智能体对话传 True。
    """
    return _build(
        "UI_EXECUTOR_ROLE_CONFIG",
        extra=extra_middlewares,
        with_events=with_events,
    )


def build_ui_verifier() -> Agent:
    """UI 控制验收角色：按角色节只授予 observe。"""
    return _build("UI_VERIFIER_ROLE_CONFIG", with_events=False)


def build_case_writer() -> Agent:
    """用例编写执行角色：不授静态工具，产物工具运行时注入。"""
    return _build("CASE_WRITER_ROLE_CONFIG", middlewares=[])


def build_case_verifier() -> Agent:
    """用例编写验收角色：不授静态工具。"""
    return _build("CASE_VERIFIER_ROLE_CONFIG", middlewares=[])


# 兼容旧名
build_executor = build_ui_executor
build_verifier = build_ui_verifier


def executor_agent() -> Agent:
    """兼容旧名：等同 build_ui_executor（无额外工具包注入时请直接用工厂）。"""
    return build_ui_executor()


def verifier_agent() -> Agent:
    """兼容旧名：等同 build_ui_verifier。"""
    return build_ui_verifier()


def build_knowledge_chat(toolkit: Toolkit | None = None) -> Agent:
    """知识库文字问答角色：KNOWLEDGE_CHAT_ROLE_CONFIG + 知识检索工具包。

    纯文字角色不装语音合成中间件，避免把回答再合成一遍音频。

    Args:
        toolkit: 调用方注入的工具包（如 RAG 的 search_knowledge）；None 用空包。

    Returns:
        装配好的 Agent（每次调用都是独立实例，多轮历史留在实例内）。
    """
    return _build("KNOWLEDGE_CHAT_ROLE_CONFIG", toolkit or Toolkit(), with_events=False)
