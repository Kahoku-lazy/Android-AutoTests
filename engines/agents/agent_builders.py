"""
文件名: ➡️ agent_builders.py 🏁
路径: ➡️ engines/agents/agent_builders.py 🏁
模块功能：➡️ 本文件集中 LLM agents（chat / ReAct）：UI 执行/验收与用例编写相关角色 🏁
Python 调试：➡️ python -m engines.agents.agent_builders 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. RoleConfig / ToolsConfig / ContextConfig / ReActConfig: 过渡期再导出四分段类型
2. AgentRoleFactory: 用已建好的模型 + 四分段配置装配 agentscope.Agent
3. build_ui_executor / build_ui_verifier / build_case_*: 角色键 → 模型 + 四分段 + 工具包
4. build_knowledge_chat: 知识库文字问答角色（纯文字，不装语音合成）
4. executor_agent / verifier_agent / build_executor / build_verifier: 兼容旧名的快捷入口
5. _agent_from_role_bundle: 全部角色共用的装配路径，模型只经 engines.agents.models 门面取
🏁
关联模块：➡️
1. engines.agents.config.role_loader: 导入 load_role_spec / RoleBundle，装角色四分段
2. engines.agents.config.role_types: 导入四分段类型
3. engines.agents.models: 导入 get_chat_model / get_fallback_chat_model，取模型实例
4. engines.agents.middleware: 延迟导入 build_agent_middlewares，装配默认中间件
5. engines.agents.tools_config: 延迟导入各角色工具包
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

from agentscope.agent import (
    Agent,
)
from agentscope.agent import (
    ContextConfig as AsContextConfig,
)
from agentscope.agent import (
    ReActConfig as AsReActConfig,
)
from agentscope.model import ChatModelBase
from agentscope.tool import Toolkit

from engines.agents.config.role_loader import RoleBundle, load_role_spec
from engines.agents.config.role_types import (
    ContextConfig,
    ReActConfig,
    RoleConfig,
    ToolsConfig,
)
from engines.agents.models import get_chat_model, get_fallback_chat_model

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
    "build_case_planner",
    "build_case_writer_goal",
    "build_case_verifier_goal",
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
    )


def _as_context_config(context: ContextConfig) -> AsContextConfig:
    """role 侧 ContextConfig → agentscope.ContextConfig。"""
    return AsContextConfig(
        trigger_ratio=context.trigger_ratio,
        reserve_ratio=context.reserve_ratio,
        tool_result_limit=context.tool_result_limit,
        max_image_num=context.max_image_num,
    )


def _default_middlewares(fallback_model: ChatModelBase | None, *, with_tts: bool = True) -> list:
    """默认中间件装配：调用统一装配入口，只把备用模型实例传进去。

    Args:
        fallback_model: 已建好的备用模型；None 表示不启用回退。
        with_tts: 是否允许装配语音合成中间件；纯文字角色传 False。

    Returns:
        交给 `Agent(middlewares=...)` 的列表。
    """
    from engines.agents.middleware import build_agent_middlewares

    return build_agent_middlewares(fallback_model=fallback_model, with_tts=with_tts)


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
        with_tts: bool = True,
    ) -> None:
        """
        Args:
            model: 已建好的聊天模型实例（由 `engines.agents.models` 门面提供）。
            role: 角色名与系统提示词。
            tools: 工具配置；None 时用空 Toolkit()。
            context: 上下文配置；None 用 dataclass 默认。
            react: ReAct 配置；None 用 dataclass 默认。
            toolkit: 显式工具包，优先于 tools.toolkit。
            middlewares: 显式中间件；None 时自动装配。
            fallback_model: 备用模型；仅自动装配中间件时使用。
            with_tts: 是否允许自动装配语音合成中间件；纯文字角色传 False。

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
        self.with_tts = with_tts

    def create(self) -> Agent:
        """组装 agentscope.Agent。

        N1：Agent 只接收 `ChatModelBase`；模型连接参数止于门面内部。

        Returns:
            新的 Agent 实例（每次调用都是独立实例）。
        """
        middlewares = (
            self._middlewares
            if self._middlewares is not None
            else _default_middlewares(self.fallback_model, with_tts=self.with_tts)
        )
        return Agent(
            name=self.role.name,
            system_prompt=self.role.system_prompt,
            model=self.model,
            react_config=_as_react_config(self.react),
            context_config=_as_context_config(self.context),
            toolkit=self.tools.toolkit,
            middlewares=middlewares,
        )


def _agent_from_role_bundle(
    bundle: RoleBundle,
    *,
    toolkit: Toolkit | None = None,
    react: ReActConfig | None = None,
    middlewares: list | None = None,
    with_tts: bool = True,
) -> Agent:
    """把 RoleBundle 变成 Agent：模型经门面取，四分段来自 bundle。

    Args:
        bundle: `load_role_spec` 的产物。
        toolkit: 角色工具包。
        react: 覆盖 YAML 的 ReAct 配置；None 用 bundle 里的。
        middlewares: 显式中间件；None 时按默认装配并附带备用模型。
        with_tts: 是否允许默认装配语音合成中间件；纯文字角色传 False。

    Returns:
        装配好的 Agent。
    """
    model = get_chat_model(bundle.role_key)
    fallback_model = get_fallback_chat_model(bundle.role_key) if middlewares is None else None
    return AgentRoleFactory(
        model,
        bundle.role,
        tools=bundle.tools,
        context=bundle.context,
        react=react if react is not None else bundle.react,
        toolkit=toolkit,
        middlewares=middlewares,
        fallback_model=fallback_model,
        with_tts=with_tts,
    ).create()


# ── 四大主角色（配置全在 agent_config.yaml）──────────────────────────


def build_ui_executor() -> Agent:
    """UI 控制执行角色：UI_EXECUTOR_ROLE_CONFIG + 设备执行工具包。"""
    from engines.agents.tools_config import build_executor_toolkit

    return _agent_from_role_bundle(
        load_role_spec("UI_EXECUTOR_ROLE_CONFIG"),
        toolkit=build_executor_toolkit(),
    )


def build_ui_verifier() -> Agent:
    """UI 控制验收角色：UI_VERIFIER_ROLE_CONFIG + 设备验收工具包。"""
    from engines.agents.tools_config import build_verifier_toolkit

    return _agent_from_role_bundle(
        load_role_spec("UI_VERIFIER_ROLE_CONFIG"),
        toolkit=build_verifier_toolkit(),
    )


def build_case_writer() -> Agent:
    """用例编写执行角色：CASE_WRITER_ROLE_CONFIG + 空工具包（产物工具运行时注入）。"""
    from engines.agents.tools_config import build_case_authoring_toolkit

    return _agent_from_role_bundle(
        load_role_spec("CASE_WRITER_ROLE_CONFIG"),
        toolkit=build_case_authoring_toolkit(),
        middlewares=[],
    )


def build_case_verifier() -> Agent:
    """用例编写验收角色：CASE_VERIFIER_ROLE_CONFIG + 空工具包。"""
    from engines.agents.tools_config import build_case_authoring_toolkit

    return _agent_from_role_bundle(
        load_role_spec("CASE_VERIFIER_ROLE_CONFIG"),
        toolkit=build_case_authoring_toolkit(),
        middlewares=[],
    )


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
    return _agent_from_role_bundle(
        load_role_spec("KNOWLEDGE_CHAT_ROLE_CONFIG"),
        toolkit=toolkit,
        with_tts=False,
    )
