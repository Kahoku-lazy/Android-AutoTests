"""
文件名: ➡️ schema.py 🏁
路径: ➡️ engines/agents/assistant/schema.py 🏁
模块功能：➡️ 角色节的形状与校验：只收短名和四分段，拒绝连接参数 🏁
Python 调试：➡️ python -m engines.agents.assistant.schema 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. AgentConfigError: 角色节不合法，消息带角色键。
2. RoleSpec: 一个角色节的不可变形状（模型短名、名字、提示词、上下文、ReAct）。
3. parse_role: 把 YAML 一节校验成 RoleSpec；连接参数直接拒绝。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 pydantic，不 import 引擎内其它模块。
🏁
测试：➡️
1. tests/engines/agents/unit/test_assistant_create.py: 缺字段、未知字段、连接参数被拒
🏁
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

__all__ = ["AgentConfigError", "RoleSpec", "parse_role"]

# 连接参数只属于模型表。角色节写了这些键，说明有人把模型配置抄进了角色。
_FORBIDDEN = ("provider", "model_name", "api_key", "api_key_env", "base_url")


class AgentConfigError(ValueError):
    """
    角色节不合法。

    消息面向改配置的人：带角色键，能照着改。

    Attributes:
        无。
    """


class _ContextSpec(BaseModel):
    """
    角色侧上下文参数，缺省与现有 ContextConfig 一致。

    Attributes:
        trigger_ratio: 压缩触发比例。
        reserve_ratio: 压缩后保留比例。
        tool_result_limit: 单条工具结果长度上限。
        max_image_num: 上下文保留的图片数量上限。
    """

    model_config = ConfigDict(extra="forbid")

    trigger_ratio: float = 0.7
    reserve_ratio: float = 0.2
    tool_result_limit: int = Field(default=400000, ge=0)
    max_image_num: int = Field(default=5, ge=0)


class _ReActSpec(BaseModel):
    """
    角色侧 ReAct 参数，缺省与现有 ReActConfig 一致。

    Attributes:
        max_iters: 推理-行动循环最大轮次。
        structured_output_grace_iters: 结构化输出的宽限轮次。
        stop_on_reject: 工具被拒绝时是否停止。
        interruption_raise_cancelled_error: 被取消后是否继续抛出取消异常。
    """

    model_config = ConfigDict(extra="forbid")

    max_iters: int = Field(default=30, ge=1)
    structured_output_grace_iters: int = Field(default=5, ge=0)
    stop_on_reject: bool = True
    interruption_raise_cancelled_error: bool = True


class _ModelRef(BaseModel):
    """
    角色对模型的引用：只留短名和聊天族的流式开关。

    Attributes:
        model: 模型表里的短名。
        stream: 聊天族流式开关；None 表示用模型层默认。
    """

    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1)
    stream: bool | None = None


class RoleSpec(BaseModel):
    """
    一个角色节校验后的形状。

    Attributes:
        model: 模型短名与可选流式开关。
        name: 智能体名字。
        system_prompt: 已解析的提示词正文；本类不读文件。
        context: 上下文参数。
        react: ReAct 参数。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: _ModelRef
    name: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    context: _ContextSpec = Field(default_factory=_ContextSpec)
    react: _ReActSpec = Field(default_factory=_ReActSpec)


def _flatten(section: dict[str, Any]) -> dict[str, Any]:
    """
    把 YAML 四分段收成 RoleSpec 能直接校验的一层。

    Args:
        section: 一个角色节（含 ModelConfig / RoleConfig 等）。

    Returns:
        扁平字典：model、name、system_prompt、context、react。

    Raises:
        AgentConfigError: 节里出现连接参数，或分段不是映射表。
    """
    leaked = [key for key in _FORBIDDEN if key in section]
    if leaked:
        raise AgentConfigError(f"角色节不得包含连接参数：{', '.join(leaked)}")
    model = section.get("ModelConfig") or {}
    role = section.get("RoleConfig") or {}
    if not isinstance(model, dict) or not isinstance(role, dict):
        raise AgentConfigError("ModelConfig 与 RoleConfig 必须是映射表")
    leaked = [key for key in _FORBIDDEN if key in model or key in role]
    if leaked:
        raise AgentConfigError(f"角色节不得包含连接参数：{', '.join(leaked)}")
    flat: dict[str, Any] = {
        "model": model,
        "name": role.get("name"),
        "system_prompt": role.get("system_prompt"),
    }
    if section.get("ContextConfig"):
        flat["context"] = section["ContextConfig"]
    if section.get("ReActConfig"):
        flat["react"] = section["ReActConfig"]
    return flat


def parse_role(section: object, *, role_key: str) -> RoleSpec:
    """
    校验一个角色节。

    Args:
        section: 角色表里的一节。
        role_key: 角色键，只用于报错定位。

    Returns:
        已校验的角色规格。

    Raises:
        AgentConfigError: 节不是映射表、缺字段、未知字段，或含连接参数。
    """
    if not isinstance(section, dict):
        raise AgentConfigError(f"{role_key}: 必须是映射表，收到 {type(section).__name__}")
    try:
        return RoleSpec.model_validate(_flatten(section))
    except ValidationError as exc:
        problems: list[str] = []
        for err in exc.errors():
            where = ".".join(str(part) for part in err["loc"]) or role_key
            problems.append(f"{role_key}.{where}: {err['msg']}")
        raise AgentConfigError("；".join(problems)) from exc
