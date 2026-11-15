"""
文件名: ➡️ loader.py 🏁
路径: ➡️ engines/agents/assistant/loader.py 🏁
模块功能：➡️ 从整张角色表里取一节并校验 🏁
Python 调试：➡️ python -m engines.agents.assistant.loader 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_role: 按角色键取节并校验；不读文件、不读环境变量。
🏁
关联模块：➡️
1. engines.agents.assistant.schema: 导入 AgentConfigError / RoleSpec / parse_role
🏁
测试：➡️
1. tests/engines/agents/unit/test_assistant_create.py: 未知键报错并列出可选键
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .schema import AgentConfigError, RoleSpec, parse_role

__all__ = ["load_role"]


def load_role(roles: Mapping[str, Any], role_key: str) -> RoleSpec:
    """
    从整张角色表里取一节并校验。

    Args:
        roles: config 读好的整张角色表。提示词若是 token，须由调用方先解析成正文。
        role_key: 角色键，如 UI_EXECUTOR_ROLE_CONFIG。

    Returns:
        已校验的角色规格。

    Raises:
        AgentConfigError: 表不是映射表、角色键不存在，或该节校验不通过。
    """
    if not isinstance(roles, Mapping):
        raise AgentConfigError(f"角色表: 顶层必须是映射表，收到 {type(roles).__name__}")
    section = roles.get(role_key)
    if section is None:
        choices = ", ".join(sorted(str(key) for key in roles)) or "无"
        raise AgentConfigError(f"未知角色 {role_key!r}；可选：{choices}")
    return parse_role(section, role_key=role_key)
