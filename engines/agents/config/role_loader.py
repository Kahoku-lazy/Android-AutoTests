"""
文件名: ➡️ role_loader.py 🏁
路径: ➡️ engines/agents/config/role_loader.py 🏁
模块功能：➡️ 角色四分段装载：从 agent_config.yaml 装 Role / Tools / Context / ReAct 🏁
Python 调试：➡️ python -m engines.agents.config.role_loader 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. RoleModelRef: 角色侧模型引用（短名 + 调用姿势），不含连接参数
2. RoleBundle: 一个角色的四分段打包（role_key + 模型引用 + Role / Tools / Context / ReAct）
3. load_role_spec: 读 agent_config.yaml 的一个角色节，产出 RoleBundle；短名存在性经只读视图确认
4. _merge_dataclass / _build_role_config / _build_tools_config: 分段的默认值与校验
🏁
关联模块：➡️
1. engines.agents.config.config: 导入 load_agent_config / load_model_config，读两张表
2. engines.agents.config.model_view: 导入 model_view，只确认短名存在，不造模型
3. engines.agents.config.role_types: 导入四分段类型
4. engines.agents.role_sys_prompts: 导入 resolve_system_prompt / with_app_info，解析提示词 token 与应用短卡
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_roles.py: 经 RoleBundle 装配用例编写/验收角色
2. tests/graybox/unit/test_case_run_continuity.py: 一批用例的执行连续性
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import MISSING, dataclass, fields

from agentscope.tool import Toolkit

from engines.agents.config.config import load_agent_config, load_model_config
from engines.agents.config.model_view import model_view
from engines.agents.config.role_types import (
    ContextConfig,
    ReActConfig,
    RoleConfig,
    ToolsConfig,
)
from engines.agents.role_sys_prompts import resolve_system_prompt, with_app_info

__all__ = ["RoleBundle", "RoleModelRef", "load_role_spec"]

_CONNECTION_KEYS = frozenset(
    {"provider", "model_name", "base_url", "api_key", "api_key_env", "vision"}
)
_REF_KEYS = frozenset(
    {"model", "stream", "temperature", "max_retries", "context_size", "parameters"}
)


@dataclass(frozen=True)
class RoleModelRef:
    """
    角色侧的模型引用：只含短名与调用姿势。

    Attributes:
        model: 模型资产短名。
        stream: 是否流式；None 表示用默认。
        temperature: 采样温度覆盖。
        max_retries: 重试次数覆盖。
        context_size: 上下文窗口覆盖。
        parameters: 参数覆盖。
    """

    model: str
    stream: bool | None = None
    temperature: float | None = None
    max_retries: int | None = None
    context_size: int | None = None
    parameters: Mapping[str, object] | None = None


@dataclass(frozen=True)
class RoleBundle:
    """
    一个角色的四分段配置打包。

    Attributes:
        role_key: agent_config.yaml 的顶层键。
        model: 模型引用（短名 + 调用姿势），连接参数不在这里。
        role: 角色名与系统提示词。
        tools: 工具配置（空节为 `Toolkit()`）。
        context: 上下文配置。
        react: ReAct 配置。
    """

    role_key: str
    model: RoleModelRef
    role: RoleConfig
    tools: ToolsConfig
    context: ContextConfig
    react: ReActConfig


def _is_empty_section(value: object) -> bool:
    """YAML 节缺失 / null / 空映射 / 空白字符串视为空。"""
    if value is None:
        return True
    if isinstance(value, dict) and not value:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _merge_dataclass(cls, raw: object, *, where: str):
    """用 YAML 部分字段覆盖 dataclass 默认值；空节则全默认。

    未知键直接报错：配置写了不生效比配置报错更难查（例如 `max_iter` 少了 `s`）。

    Args:
        cls: 目标 dataclass 类型。
        raw: YAML 节点。
        where: 报错定位用的路径。

    Returns:
        dataclass 实例。

    Raises:
        ValueError: 节点不是映射表，出现 dataclass 不认识的键，或字段缺失且无默认值。
    """
    if _is_empty_section(raw):
        return cls()
    if not isinstance(raw, dict):
        raise ValueError(f"{where} 必须是映射表或空")
    known = [f.name for f in fields(cls)]
    unknown = sorted(set(raw) - set(known))
    if unknown:
        raise ValueError(f"{where} 含未知键 {', '.join(unknown)}；可选：{', '.join(sorted(known))}")
    kwargs: dict = {}
    for f in fields(cls):
        if f.name in raw and raw[f.name] is not None:
            kwargs[f.name] = raw[f.name]
        elif f.default is not MISSING:
            kwargs[f.name] = f.default
        elif f.default_factory is not MISSING:  # type: ignore[truthy-function]
            kwargs[f.name] = f.default_factory()
        else:
            raise ValueError(f"{where}.{f.name} 缺失且无默认值")
    return cls(**kwargs)


def _build_role_config(raw: object, *, where: str) -> RoleConfig:
    """构造 RoleConfig；可选 RoleConfig.app_info 追加「被测应用短卡」。

    Args:
        raw: YAML 的 RoleConfig 节点。
        where: 报错定位用的路径。

    Returns:
        角色名与解析后的系统提示词。

    Raises:
        ValueError: 节为空、不是映射表，或 name 缺失。
    """
    if _is_empty_section(raw):
        raise ValueError(f"{where}.RoleConfig 为空，无法构造角色（需要 name 与 system_prompt）")
    if not isinstance(raw, dict):
        raise ValueError(f"{where}.RoleConfig 必须是映射表")
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{where}.RoleConfig.name 缺失或为空")
    system_prompt = resolve_system_prompt(raw.get("system_prompt"), where=f"{where}.RoleConfig")
    system_prompt = with_app_info(system_prompt, raw.get("app_info"))
    return RoleConfig(name=name.strip(), system_prompt=system_prompt)


def _build_tools_config(raw: object, *, where: str) -> ToolsConfig:
    """ToolsConfig 为空时默认 Toolkit()（空工具包）；不在此硬编码设备工具。

    需要执行/验收工具的调用方应在装好 ToolsConfig 后自行注入 toolkit，
    或后续扩展 YAML 以外的装配路径。

    Args:
        raw: YAML 的 ToolsConfig 节点。
        where: 报错定位用的路径。

    Returns:
        工具配置；空节返回 `Toolkit()`。

    Raises:
        ValueError: 节点不是映射表，或 toolkit 不是 Toolkit 实例。
    """
    if _is_empty_section(raw):
        return ToolsConfig(toolkit=Toolkit())
    if not isinstance(raw, dict):
        raise ValueError(f"{where}.ToolsConfig 必须是映射表或空")
    toolkit = raw.get("toolkit")
    if toolkit is None:
        return ToolsConfig(toolkit=Toolkit())
    if isinstance(toolkit, Toolkit):
        return ToolsConfig(toolkit=toolkit)
    raise ValueError(
        f"{where}.ToolsConfig.toolkit 无法从 YAML 反序列化；"
        "请留空以使用 Toolkit()，或在代码中注入工具包"
    )


def _parse_int(raw: object, *, where: str) -> int:
    """把覆盖项收成整数。

    Args:
        raw: YAML 里的原始值。
        where: 报错定位用的路径。

    Returns:
        整数值。

    Raises:
        ValueError: 不是整数。
    """
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ValueError(f"{where}: 期望整数")
    return raw


def _load_role_model_ref(config_key: str, section: Mapping[str, object]) -> RoleModelRef:
    """读取角色节的模型引用，并拒绝连接参数。

    Args:
        config_key: agent_config.yaml 顶层键。
        section: 已加载的角色节。

    Returns:
        角色模型引用。

    Raises:
        ValueError: ModelConfig 缺失、出现连接参数或字段类型非法。
    """
    raw = section.get("ModelConfig")
    where = f"{config_key}.ModelConfig"
    if not isinstance(raw, Mapping):
        raise ValueError(f"{where} 缺失或不是映射表")
    illegal = sorted(set(raw) & _CONNECTION_KEYS)
    if illegal:
        raise ValueError(
            f"{where}: 不允许出现连接参数 {', '.join(illegal)}；连接参数只在 models.yaml"
        )
    unknown = sorted(set(raw) - _REF_KEYS)
    if unknown:
        raise ValueError(f"{where}: 未知字段 {', '.join(unknown)}")
    model = raw.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError(f"{where}.model: 缺失或为空（应填 models.yaml 里的模型短名）")
    stream = raw.get("stream")
    if stream is not None and not isinstance(stream, bool):
        raise ValueError(f"{where}.stream: 期望布尔值")
    temperature = raw.get("temperature")
    if temperature is not None and not isinstance(temperature, (int, float)):
        raise ValueError(f"{where}.temperature: 期望数字")
    parameters = raw.get("parameters") or {}
    if not isinstance(parameters, Mapping):
        raise ValueError(f"{where}.parameters: 期望映射表")
    return RoleModelRef(
        model=model.strip(),
        stream=stream,
        temperature=None if temperature is None else float(temperature),
        max_retries=_parse_int(raw.get("max_retries"), where=f"{where}.max_retries")
        if raw.get("max_retries") is not None
        else None,
        context_size=_parse_int(raw.get("context_size"), where=f"{where}.context_size")
        if raw.get("context_size") is not None
        else None,
        parameters=dict(parameters),
    )


def load_role_spec(config_key: str) -> RoleBundle:
    """从 agent_config.yaml 装一个角色的四分段配置。

    RoleConfig / ToolsConfig / ContextConfig / ReActConfig：
    - 节缺失、null、空映射时用 dataclass 默认（ToolsConfig → Toolkit()）。
    - RoleConfig 完全为空会报错（无法臆造 name）。
    - RoleConfig.system_prompt 为 prompts 目录下的 token 时读 md 原文。
    - RoleConfig.app_info 可选：app_info 目录下的 token，追加「被测应用短卡」。

    Args:
        config_key: agent_config.yaml 的顶层键，如 UI_EXECUTOR_ROLE_CONFIG。

    Returns:
        四分段打包；模型连接参数不在其中。

    Raises:
        ValueError: 节缺失、RoleConfig 为空，或分段字段非法。
    """
    roles = load_agent_config()
    section = roles.get(config_key) if isinstance(roles, dict) else None
    section = section or {}
    if not isinstance(section, dict) or not section:
        raise ValueError(f"agent_config 缺少节 {config_key!r}")

    model_ref = _load_role_model_ref(config_key, section)
    model_view(load_model_config(), model_ref.model)

    return RoleBundle(
        role_key=config_key,
        model=model_ref,
        role=_build_role_config(section.get("RoleConfig"), where=config_key),
        tools=_build_tools_config(section.get("ToolsConfig"), where=config_key),
        context=_merge_dataclass(
            ContextConfig, section.get("ContextConfig"), where=f"{config_key}.ContextConfig"
        ),
        react=_merge_dataclass(
            ReActConfig, section.get("ReActConfig"), where=f"{config_key}.ReActConfig"
        ),
    )
