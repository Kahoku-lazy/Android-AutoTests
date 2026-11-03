"""
文件名: ➡️ role_loader.py 🏁
路径: ➡️ engines/agents/config/role_loader.py 🏁
模块功能：➡️ 角色四分段装载：从 agent_config.yaml 装 Role / Tools / Context / ReAct 🏁
Python 调试：➡️ python -m engines.agents.config.role_loader 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. RoleBundle: 一个角色的四分段打包（role_key + Role / Tools / Context / ReAct）
2. load_role_spec: 读 agent_config.yaml 的一个角色节，产出 RoleBundle；不含模型连接参数
3. _merge_dataclass / _build_role_config / _build_tools_config: 分段的默认值与校验
4. 模型连接参数不在这里：由 engines.agents.models 的 loader 负责
🏁
关联模块：➡️
1. engines.agents.config.config: 导入 load_agent_config，读 agent_config.yaml
2. engines.agents.config.role_types: 导入四分段类型
3. engines.agents.role_sys_prompts: 导入 resolve_system_prompt / with_app_info，解析提示词 token 与应用短卡
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_roles.py: 经 RoleBundle 装配用例编写/验收角色
2. tests/graybox/unit/test_case_run_continuity.py: 一批用例的执行连续性
🏁
"""

from __future__ import annotations

from dataclasses import MISSING, dataclass, fields

from agentscope.tool import Toolkit

from engines.agents.config.config import load_agent_config
from engines.agents.config.role_types import (
    ContextConfig,
    ReActConfig,
    RoleConfig,
    ToolsConfig,
)
from engines.agents.role_sys_prompts import resolve_system_prompt, with_app_info

__all__ = ["RoleBundle", "load_role_spec"]


@dataclass(frozen=True)
class RoleBundle:
    """
    一个角色的四分段配置打包。

    Attributes:
        role_key: agent_config.yaml 的顶层键，模型装配按它取模型。
        role: 角色名与系统提示词。
        tools: 工具配置（空节为 `Toolkit()`）。
        context: 上下文配置。
        react: ReAct 配置。
    """

    role_key: str
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

    Args:
        cls: 目标 dataclass 类型。
        raw: YAML 节点。
        where: 报错定位用的路径。

    Returns:
        dataclass 实例。

    Raises:
        ValueError: 节点不是映射表，或字段缺失且无默认值。
    """
    if _is_empty_section(raw):
        return cls()
    if not isinstance(raw, dict):
        raise ValueError(f"{where} 必须是映射表或空")
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
    section = load_agent_config(config_key) or {}
    if not isinstance(section, dict) or not section:
        raise ValueError(f"agent_config 缺少节 {config_key!r}")

    return RoleBundle(
        role_key=config_key,
        role=_build_role_config(section.get("RoleConfig"), where=config_key),
        tools=_build_tools_config(section.get("ToolsConfig"), where=config_key),
        context=_merge_dataclass(
            ContextConfig, section.get("ContextConfig"), where=f"{config_key}.ContextConfig"
        ),
        react=_merge_dataclass(
            ReActConfig, section.get("ReActConfig"), where=f"{config_key}.ReActConfig"
        ),
    )
