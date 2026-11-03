"""
文件名: ➡️ loader.py 🏁
路径: ➡️ engines/agents/models/loader.py 🏁
模块功能：➡️ 从 agent_config.yaml 的 ModelConfig 段装聊天与实时语音连接参数 🏁
Python 调试：➡️ python -m engines.agents.models.loader 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. load_model_config: 读 `<KEY>.ModelConfig` 段，产出聊天模型 ModelConfig
2. load_realtime_model_config: 读 `<KEY>.ModelConfig` 段，产出实时语音 RealtimeModelConfig
3. _get_api_key: 把 YAML 里写的环境变量名解析成密钥；缺变量直接报错
🏁
关联模块：➡️
1. engines.agents.config.config: 导入 load_agent_config，读 config/data/agent_config.yaml
2. engines.agents.models.types: 导入 ModelConfig / RealtimeModelConfig，本模块的装载产物
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_roles.py: 经角色装配间接装模型
2. tests/engines/agents/test_models.py: 经门面建执行/验收模型（e2e）
🏁
"""

from __future__ import annotations

import os

from dataclasses import fields

from pydantic import SecretStr

from engines.agents.config.config import load_agent_config

from .types import ModelConfig, RealtimeModelConfig

__all__ = ["load_model_config", "load_realtime_model_config"]


def _get_api_key(env_name: str) -> SecretStr:
    """从环境变量读取 API 密钥；config 里存的是变量名。

    Args:
        env_name: 环境变量名。

    Returns:
        包好的密钥。

    Raises:
        ValueError: 环境变量未设置或为空。
    """
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"环境变量未设置: {env_name}")
    return SecretStr(value)


def _load_section(config_key: str) -> dict:
    """取出 agent_config.yaml 的一个角色节。

    Args:
        config_key: 顶层键，如 UI_EXECUTOR_ROLE_CONFIG。

    Returns:
        该节的映射表。

    Raises:
        ValueError: 节缺失或不是映射表。
    """
    section = load_agent_config(config_key) or {}
    if not isinstance(section, dict) or not section:
        raise ValueError(f"agent_config 缺少节 {config_key!r}")
    return section


def _raw_model_config(section: dict, *, config_key: str) -> dict:
    """取出并校验 `<KEY>.ModelConfig` 段，把 api_key 换成真实密钥。

    Args:
        section: 角色节。
        config_key: 顶层键，用于报错定位。

    Returns:
        可直接构造配置的字段表。

    Raises:
        ValueError: ModelConfig 缺失 / 不是映射表 / api_key 不是环境变量名。
    """
    raw_model_config = section.get("ModelConfig")
    if not isinstance(raw_model_config, dict):
        raise ValueError(f"{config_key}.ModelConfig 缺失或不是映射表")
    model_fields = dict(raw_model_config)
    env_name = model_fields.get("api_key")
    if not isinstance(env_name, str) or not env_name.strip():
        raise ValueError(f"{config_key}.ModelConfig.api_key 必须是环境变量名字符串")
    model_fields["api_key"] = _get_api_key(env_name.strip())
    return model_fields


def load_model_config(config_key: str) -> ModelConfig:
    """从 agent_config.yaml 装一个聊天模型的连接参数。

    Args:
        config_key: 顶层键，如 UI_EXECUTOR_ROLE_CONFIG。

    Returns:
        该角色的 ModelConfig；vision / stream 归一到布尔。

    Raises:
        ValueError: 节缺失、ModelConfig 缺失或 api_key 不是环境变量名。
    """
    model_fields = _raw_model_config(_load_section(config_key), config_key=config_key)
    if "vision" in model_fields:
        model_fields["vision"] = bool(model_fields["vision"])
    if "stream" in model_fields:
        model_fields["stream"] = bool(model_fields["stream"])
    return ModelConfig(**model_fields)


def load_realtime_model_config(config_key: str) -> RealtimeModelConfig:
    """从 agent_config.yaml 装一个实时语音模型的连接参数。

    Args:
        config_key: 顶层键，通常为 OMNI_ROLE_CONFIG。

    Returns:
        该角色的 RealtimeModelConfig。

    Raises:
        ValueError: 节缺失、ModelConfig 缺失、api_key 不是环境变量名、
            base_url 不是字符串，或含实时侧不认识的字段。
    """
    model_fields = _raw_model_config(_load_section(config_key), config_key=config_key)
    base_url = model_fields.get("base_url", "")
    if base_url is None:
        model_fields["base_url"] = ""
    elif not isinstance(base_url, str):
        raise ValueError(f"{config_key}.ModelConfig.base_url 必须是字符串")
    for chat_only in ("vision", "stream"):
        model_fields.pop(chat_only, None)
    allowed = {f.name for f in fields(RealtimeModelConfig)}
    unknown = set(model_fields) - allowed
    if unknown:
        raise ValueError(f"{config_key}.ModelConfig 含未知字段: {sorted(unknown)}")
    return RealtimeModelConfig(**model_fields)
