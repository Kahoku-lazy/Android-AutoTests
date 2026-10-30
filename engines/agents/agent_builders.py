"""
文件名: ➡️ agent_builders.py 🏁
路径: ➡️ engines/agents/agent_builders.py 🏁
模块功能：➡️ 本文件集中 LLM agents（chat / ReAct）：UI 执行/验收与用例编写相关角色 🏁
Python 调试：➡️ python -m engines.agents.agent_builders 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. RoleConfig: 角色配置（名称、系统提示词）。
2. ToolsConfig: 工具配置（本角色已装配的工具包）。
3. ContextConfig: 上下文配置（role 侧参数，由 AgentRoleFactory 映射到 agentscope.ContextConfig）。
4. ReActConfig: ReAct 配置（role 侧参数，由 AgentRoleFactory 映射到 agentscope.ReActConfig）。
5. AgentRoleFactory: 按 ModelConfig + 四分段配置创建 agentscope.Agent（对称于 ChatModelFactory）。
6. executor_agent / verifier_agent: 从 agent_config.yaml 快捷创建执行/验收智能体。
7. build_executor / build_verifier: YAML + 设备工具包，返回 Agent。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/engines/agents/test_agents.py: 连通性：engines.agents.agent_builders 按 YAML 创建 Agent 并能拿到一轮回复
2. tests/graybox/unit/test_case_authoring_roles.py: 家电测试用例编写/验收角色的装配与成对运行入口
3. tests/graybox/unit/test_case_run_continuity.py: 一批用例的执行连续性：单条失败继续跑、结果区分清单、取消不追加失败
4. tests/graybox/unit/test_forced_handover_thinking.py: 强制交卷时关闭思考，未满轮次的请求保持原样
5. tests/graybox/unit/test_model_retry_middleware.py: 模型重试与回退中间件：分类判定、退避序列、回退、流式首块、环境变量解析
🏁
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agentscope.agent import (
    Agent,
)
from agentscope.agent import (
    ContextConfig as AsContextConfig,
)
from agentscope.agent import (
    ReActConfig as AsReActConfig,
)
from agentscope.tool import Toolkit

from engines.agents.config.role_types import (
    ContextConfig,
    ReActConfig,
    RoleConfig,
    ToolsConfig,
)

if TYPE_CHECKING:
    from engines.agents.config.models import ModelConfig

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


def _fallback_chat_model(model_config: ModelConfig, settings):
    """按重试设置构造备用聊天模型；未配置回退模型名时返回 None。"""
    from engines.agents.config.models import ChatModelFactory
    from engines.agents.config.models import ModelConfig as MC

    if not settings.fallback_model_name:
        return None
    api_key = model_config.api_key
    if hasattr(api_key, "get_secret_value"):
        api_key = api_key.get_secret_value()
    fallback = MC(
        provider=settings.fallback_provider or model_config.provider,
        model_name=settings.fallback_model_name,
        api_key=settings.fallback_api_key or api_key,
        base_url=settings.fallback_base_url or model_config.base_url,
        vision=model_config.vision,
        stream=model_config.stream,
    )
    return ChatModelFactory(fallback).create()


def _default_middlewares(model_config: ModelConfig) -> list:
    """默认中间件装配（追踪 / 预算 / RAG / 语音 / 记忆 / 模型重试）。"""
    from engines.agents.middleware import build_agent_middlewares, load_retry_settings

    settings = load_retry_settings()
    fallback = _fallback_chat_model(model_config, settings) if settings.enabled else None
    return build_agent_middlewares(fallback_model=fallback)


class AgentRoleFactory:
    """按 ModelConfig + Role/Tools/Context/ReAct 四分段配置创建 agentscope.Agent。"""

    def __init__(
        self,
        model_config: ModelConfig,
        role: RoleConfig,
        *,
        tools: ToolsConfig | None = None,
        context: ContextConfig | None = None,
        react: ReActConfig | None = None,
        toolkit: Toolkit | None = None,
        middlewares: list | None = None,
    ) -> None:
        """
        Args:
            model_config: 聊天模型配置（含 vision / stream）。
            role: 角色名与系统提示词。
            tools: 工具配置；None 时用空 Toolkit()。
            context: 上下文配置；None 用 dataclass 默认。
            react: ReAct 配置；None 用 dataclass 默认。
            toolkit: 显式工具包，优先于 tools.toolkit。
            middlewares: 显式中间件；None 时自动装配。
        """
        if not isinstance(role, RoleConfig):
            raise TypeError(f"role 须为 RoleConfig，收到: {type(role).__name__}")

        self.model_config = model_config
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

    def create(self) -> Agent:
        """用 ChatModelFactory(model_config).create() 建模型，再组装 Agent。

        N1：仅把 ChatModelBase 交给 Agent；ModelConfig 止于本方法内建模型，不传入 Agent(...)。
        """
        from engines.agents.config.models import ChatModelFactory

        model = ChatModelFactory(self.model_config).create()
        middlewares = (
            self._middlewares
            if self._middlewares is not None
            else _default_middlewares(self.model_config)
        )
        return Agent(
            name=self.role.name,
            system_prompt=self.role.system_prompt,
            model=model,
            react_config=_as_react_config(self.react),
            context_config=_as_context_config(self.context),
            toolkit=self.tools.toolkit,
            middlewares=middlewares,
        )


def _agent_from_role_bundle(
    bundle: tuple,
    *,
    toolkit: Toolkit | None = None,
    react: ReActConfig | None = None,
    middlewares: list | None = None,
) -> Agent:
    """把 load_role_config 五元组交给 AgentRoleFactory.create()。"""
    model_config, role, tools, context, loaded_react = bundle
    return AgentRoleFactory(
        model_config,
        role,
        tools=tools,
        context=context,
        react=react if react is not None else loaded_react,
        toolkit=toolkit,
        middlewares=middlewares,
    ).create()


# ── 四大主角色（配置全在 agent_config.yaml）──────────────────────────


def build_ui_executor() -> Agent:
    """UI 控制执行角色：UI_EXECUTOR_ROLE_CONFIG + 设备执行工具包。"""
    from engines.agents.config.models import ui_executor_role_config
    from engines.agents.tools_config import build_executor_toolkit

    return _agent_from_role_bundle(
        ui_executor_role_config(),
        toolkit=build_executor_toolkit(),
    )


def build_ui_verifier() -> Agent:
    """UI 控制验收角色：UI_VERIFIER_ROLE_CONFIG + 设备验收工具包。"""
    from engines.agents.config.models import ui_verifier_role_config
    from engines.agents.tools_config import build_verifier_toolkit

    return _agent_from_role_bundle(
        ui_verifier_role_config(),
        toolkit=build_verifier_toolkit(),
    )


def build_case_writer() -> Agent:
    """用例编写执行角色：CASE_WRITER_ROLE_CONFIG + 计划模式工具。"""
    from engines.agents.config.models import case_writer_role_config
    from engines.agents.tools_config import build_case_writer_toolkit

    return _agent_from_role_bundle(
        case_writer_role_config(),
        toolkit=build_case_writer_toolkit(),
        middlewares=[],
    )


def build_case_verifier() -> Agent:
    """用例编写验收角色：CASE_VERIFIER_ROLE_CONFIG + 空工具包。"""
    from engines.agents.config.models import case_verifier_role_config
    from engines.agents.tools_config import build_case_authoring_toolkit

    return _agent_from_role_bundle(
        case_verifier_role_config(),
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


def build_case_planner() -> Agent:
    """用例模块规划角色：CASE_PLANNER_ROLE_CONFIG。"""
    from engines.agents.config.models import load_role_config
    from engines.agents.tools_config import build_case_authoring_toolkit

    return _agent_from_role_bundle(
        load_role_config("CASE_PLANNER_ROLE_CONFIG"),
        toolkit=build_case_authoring_toolkit(),
        middlewares=[],
    )


def build_case_writer_goal() -> Agent:
    """用例编写 Goal 变体：CASE_WRITER_GOAL_ROLE_CONFIG。"""
    from engines.agents.config.models import load_role_config
    from engines.agents.tools_config import build_case_writer_toolkit

    return _agent_from_role_bundle(
        load_role_config("CASE_WRITER_GOAL_ROLE_CONFIG"),
        toolkit=build_case_writer_toolkit(),
        middlewares=[],
    )


def build_case_verifier_goal() -> Agent:
    """用例验收 Goal 变体：CASE_VERIFIER_GOAL_ROLE_CONFIG。"""
    from engines.agents.config.models import load_role_config
    from engines.agents.tools_config import build_case_authoring_toolkit

    return _agent_from_role_bundle(
        load_role_config("CASE_VERIFIER_GOAL_ROLE_CONFIG"),
        toolkit=build_case_authoring_toolkit(),
        middlewares=[],
    )
