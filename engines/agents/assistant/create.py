"""
文件名: ➡️ create.py 🏁
路径: ➡️ engines/agents/assistant/create.py 🏁
模块功能：➡️ 聊天与语音两个创建出口：只创建不使用 🏁
Python 调试：➡️ python -m engines.agents.assistant.create 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. create_chat_agent: 只接受 chat 族，返回新的 Agent。
2. create_voice_agent: 只接受 realtime 族，返回新的 RealtimeAgent。
3. create_from_model: 兼容入口，调用方已持有聊天模型时仍经本包构造。
4. 模型只经 models.create_model 取得；本模块不读文件、不读环境变量。
5. 不调用 reply / reply_stream，不启动 SOP 或语音会话。
6. 聊天模型按（短名, stream）复用；语音模型不缓存；智能体每次新建。
🏁
关联模块：➡️
1. engines.agents.assistant.loader: 导入 load_role，取已校验的角色节
2. engines.agents.assistant.schema: 导入 AgentConfigError
3. engines.agents.models: 导入 create_model，按短名造模型
4. engines.agents.middleware.assembly: 导入 build_agent_middlewares，仅在未传入中间件时使用
🏁
测试：➡️
1. tests/engines/agents/unit/test_assistant_create.py: 两出口分派、错族拒绝、多余参数拒绝、空工具包
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agentscope.agent import Agent, ContextConfig, ReActConfig
from agentscope.model import ChatModelBase
from agentscope.model import ChatModelBase as _ChatModelBase
from agentscope.realtime import RealtimeModelBase
from agentscope.tool import Toolkit

from engines.agents.models import ModelConfigError, create_model

from .loader import load_role
from .schema import AgentConfigError, RoleSpec

__all__ = ["clear_chat_model_cache", "create_chat_agent", "create_voice_agent"]

# 同一进程、同一短名、同一调用姿势复用聊天模型。Agent 仍每次新建。
# 键只含短名与 stream：密钥在 config 注入时已固定，换密钥需要重新读表。
_CHAT_CACHE: dict[tuple, _ChatModelBase] = {}


def clear_chat_model_cache() -> None:
    """清空聊天模型复用记录，供测试隔离。

    Returns:
        None。
    """
    _CHAT_CACHE.clear()


def _context(spec: RoleSpec) -> ContextConfig:
    """
    把角色侧上下文参数映射成框架配置。

    Args:
        spec: 已校验的角色规格。

    Returns:
        框架 ContextConfig。
    """
    return ContextConfig(
        trigger_ratio=spec.context.trigger_ratio,
        reserve_ratio=spec.context.reserve_ratio,
        tool_result_limit=spec.context.tool_result_limit,
        max_image_num=spec.context.max_image_num,
    )


def _react(spec: RoleSpec) -> ReActConfig:
    """
    把角色侧 ReAct 参数映射成框架配置。

    Args:
        spec: 已校验的角色规格。

    Returns:
        框架 ReActConfig。
    """
    return ReActConfig(
        max_iters=spec.react.max_iters,
        structured_output_grace_iters=spec.react.structured_output_grace_iters,
        stop_on_reject=spec.react.stop_on_reject,
        interruption_raise_cancelled_error=spec.react.interruption_raise_cancelled_error,
    )


def _middlewares(given: list | None, *, with_events: bool, extra: list | None = None) -> list:
    """
    取中间件列表：调用方传入则原样使用，否则按默认装配。

    Args:
        given: 调用方传入的中间件；None 表示走默认装配。
        with_events: 默认装配时是否挂回复事件流。
        extra: 追加到默认事件流之后、重试之前的中间件。

    Returns:
        交给 Agent 的中间件列表。
    """
    if given is not None:
        return given
    from engines.agents.middleware.assembly import build_agent_middlewares

    return build_agent_middlewares(with_events=with_events, extra=extra or ())


def _chat_agent(
    spec: RoleSpec,
    model: ChatModelBase,
    *,
    toolkit: Toolkit | None,
    middlewares: list | None,
    system_prompt: str | None,
    name: str | None,
    with_events: bool,
    extra: list | None = None,
) -> Agent:
    """
    用已建好的聊天模型造一个 Agent。

    Args:
        spec: 已校验的角色规格。
        model: 聊天模型实例。
        toolkit: 调用方传入的工具包；None 用空包。
        middlewares: 调用方传入的中间件；None 走默认装配。
        system_prompt: 覆盖提示词；None 用角色节正文。
        name: 覆盖名字；None 用角色节名字。
        with_events: 默认装配时是否挂回复事件流。

    Returns:
        新的 Agent 实例。
    """
    return Agent(
        name=name or spec.name,
        system_prompt=system_prompt or spec.system_prompt,
        model=model,
        toolkit=toolkit if toolkit is not None else Toolkit(),
        middlewares=_middlewares(middlewares, with_events=with_events, extra=extra),
        context_config=_context(spec),
        react_config=_react(spec),
    )


def _realtime_agent(
    spec: RoleSpec,
    model: RealtimeModelBase,
    *,
    toolkit: Toolkit | None,
    system_prompt: str | None,
    name: str | None,
) -> Any:
    """
    用已建好的实时模型造一个 RealtimeAgent。

    Args:
        spec: 已校验的角色规格。
        model: 实时语音模型实例。
        toolkit: 调用方传入的工具包；None 表示不挂工具。
        system_prompt: 覆盖提示词；None 用角色节正文。
        name: 覆盖名字；None 用角色节名字。

    Returns:
        新的 RealtimeAgent 实例。
    """
    from agentscope.agent import RealtimeAgent

    return RealtimeAgent(
        name=name or spec.name,
        system_prompt=system_prompt or spec.system_prompt,
        model=model,
        toolkit=toolkit,
    )


def create_from_model(
    model: ChatModelBase,
    *,
    name: str,
    system_prompt: str,
    toolkit: Toolkit | None = None,
    middlewares: list | None = None,
    context: ContextConfig | None = None,
    react: ReActConfig | None = None,
    with_events: bool = True,
) -> Agent:
    """
    用调用方已经建好的聊天模型造 Agent。

    只给仍持有模型实例的兼容入口使用（如 AgentRoleFactory）。新角色不要走这里。

    Args:
        model: 已建好的聊天模型。
        name: 智能体名字。
        system_prompt: 提示词正文。
        toolkit: 工具包；None 用空包。
        middlewares: 显式中间件；None 走默认装配。
        context: 框架上下文配置；None 用框架默认。
        react: 框架 ReAct 配置；None 用框架默认。
        with_events: 默认装配时是否挂回复事件流。

    Returns:
        新的 Agent。
    """
    kwargs: dict[str, Any] = {
        "name": name,
        "system_prompt": system_prompt,
        "model": model,
        "toolkit": toolkit if toolkit is not None else Toolkit(),
        "middlewares": _middlewares(middlewares, with_events=with_events),
    }
    if context is not None:
        kwargs["context_config"] = context
    if react is not None:
        kwargs["react_config"] = react
    return Agent(**kwargs)


def _family(models: Mapping[str, Any], short_name: str, role_key: str) -> str:
    """
    在创建实例之前读出模型族。

    Args:
        models: config 读好的整张模型表。
        short_name: 角色节引用的模型短名。
        role_key: 角色键，写进错误消息。

    Returns:
        条目上的 family。

    Raises:
        AgentConfigError: 短名不存在，或条目不是映射表。
    """
    raw = models.get(short_name)
    if not isinstance(raw, Mapping):
        raise AgentConfigError(f"{role_key}: 未知模型 {short_name!r}")
    return str(raw.get("family") or "").strip()


def _reject_family(role_key: str, short_name: str, family: str, expected: str) -> None:
    """
    模型族与出口不符时抛错。

    Args:
        role_key: 角色键。
        short_name: 模型短名。
        family: 条目上的实际族。
        expected: 本出口接受的族。

    Raises:
        AgentConfigError: 实际族不是本出口接受的族。
    """
    if family != expected:
        raise AgentConfigError(
            f"{role_key}: 模型 {short_name!r} 的族是 {family or '空'}，本出口只接受 {expected}"
        )


def _require_absent(role_key: str, given: Mapping[str, object]) -> None:
    """
    语音出口拒绝聊天专用参数，不静默丢弃。

    Args:
        role_key: 角色键。
        given: 调用方显式传入的参数名到值。空值也算传入。

    Raises:
        AgentConfigError: 传入了任一聊天专用参数。
    """
    names = ", ".join(sorted(given))
    if names:
        raise AgentConfigError(f"{role_key}: 语音出口不接受 {names}")


def create_chat_agent(
    roles: Mapping[str, Any],
    models: Mapping[str, Any],
    role_key: str,
    *,
    toolkit: Toolkit | None = None,
    middlewares: list | None = None,
    system_prompt: str | None = None,
    name: str | None = None,
    with_events: bool = True,
    extra: list | None = None,
) -> Agent:
    """
    按角色键创建一个聊天智能体。

    用哪个角色由调用方决定。这里只负责「这一节能不能建成 Agent」，不调用回复接口。

    Args:
        roles: config 读好的整张角色表。system_prompt 须已是正文。
        models: config 读好的整张模型表（条目里已注入密钥）。
        role_key: 角色键，如 UI_EXECUTOR_ROLE_CONFIG。
        toolkit: 运行时工具包；不传则用空包。
        middlewares: 显式中间件；None 时走默认装配。
        system_prompt: 覆盖角色节里的提示词。
        name: 覆盖角色节里的名字。
        with_events: 默认装配时是否挂回复事件流。SOP 传 False。
        extra: 追加到默认事件流之后、重试之前的中间件。

    Returns:
        新的 Agent。同一短名、同一 stream 的聊天模型可复用。

    Raises:
        AgentConfigError: 角色键不存在、角色节非法，或模型族不是 chat。
        ModelConfigError: 模型短名不存在或模型条目非法（由模型层抛出）。
    """
    spec = load_role(roles, role_key)
    short_name = spec.model.model
    _reject_family(role_key, short_name, _family(models, short_name, role_key), "chat")
    cache_key = (short_name, spec.model.stream)
    cached = _CHAT_CACHE.get(cache_key)
    if isinstance(cached, ChatModelBase):
        model = cached
    else:
        try:
            model = create_model(models, short_name, stream=spec.model.stream)
        except ModelConfigError as exc:
            raise AgentConfigError(f"{role_key}: {exc}") from exc
        if not isinstance(model, ChatModelBase):
            raise AgentConfigError(
                f"{role_key}: 模型 {short_name!r} 的族是 chat，但没有造出聊天模型"
            )
        _CHAT_CACHE[cache_key] = model
    return _chat_agent(
        spec,
        model,
        toolkit=toolkit,
        middlewares=middlewares,
        system_prompt=system_prompt,
        name=name,
        with_events=with_events,
        extra=extra,
    )


def create_voice_agent(
    roles: Mapping[str, Any],
    models: Mapping[str, Any],
    role_key: str,
    *,
    toolkit: Toolkit | None = None,
    system_prompt: str | None = None,
    name: str | None = None,
    context: object | None = None,
    react: object | None = None,
    middlewares: list | None = None,
    stream: bool | None = None,
) -> Any:
    """
    按角色键创建一个实时语音智能体。

    只创建，不持有音频传输，不调用回复接口。聊天专用参数传入即拒绝。

    Args:
        roles: config 读好的整张角色表。system_prompt 须已是正文。
        models: config 读好的整张模型表（条目里已注入密钥）。
        role_key: 角色键，如 OMNI_ROLE_CONFIG。
        toolkit: 运行时工具包；不传则不挂工具。
        system_prompt: 覆盖角色节里的提示词；会话侧追加提示词时使用。
        name: 覆盖角色节里的名字。
        context: 聊天专用，传入即拒绝。
        react: 聊天专用，传入即拒绝。
        middlewares: 聊天专用，传入即拒绝。
        stream: 聊天专用，传入即拒绝。

    Returns:
        新的 RealtimeAgent。语音模型不复用。

    Raises:
        AgentConfigError: 角色键不存在、角色节非法、模型族不是 realtime，或传入了聊天专用参数。
        ModelConfigError: 模型短名不存在或模型条目非法（由模型层抛出）。
    """
    given = {
        key: value
        for key, value in {
            "context": context,
            "react": react,
            "middlewares": middlewares,
            "stream": stream,
        }.items()
        if value is not None
    }
    _require_absent(role_key, given)
    spec = load_role(roles, role_key)
    short_name = spec.model.model
    _reject_family(role_key, short_name, _family(models, short_name, role_key), "realtime")
    try:
        model = create_model(models, short_name)
    except ModelConfigError as exc:
        raise AgentConfigError(f"{role_key}: {exc}") from exc
    if not isinstance(model, RealtimeModelBase):
        raise AgentConfigError(
            f"{role_key}: 模型 {short_name!r} 的族是 realtime，但没有造出实时语音模型"
        )
    return _realtime_agent(
        spec,
        model,
        toolkit=toolkit,
        system_prompt=system_prompt,
        name=name,
    )
