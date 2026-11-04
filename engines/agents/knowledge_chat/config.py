"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/agents/knowledge_chat/config.py 🏁
模块功能：➡️ 文字问答会话的模型名、文本长度上限与就绪状态 🏁
Python 调试：➡️ python -m engines.agents.knowledge_chat.config 🏁
时间：➡️ 2026-11-04 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-04 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. ChatConfig: 一次文字问答会话的模型名、文本长度上限与开关。
2. load_chat_config(): 读环境变量并校验，非法取值给出可读原因。
3. build_status(): 生成 text_model / text_ready / text_reason，不含任何密钥。
🏁
关联模块：➡️
1. engines.agents.models: 导入 get_text，取目录里的文字模型名与密钥变量名
🏁
测试：➡️
1. tests/graybox/unit/test_knowledge_chat_session.py: 文字问答配置与会话单测：不联网
🏁
"""

from __future__ import annotations

import os

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from engines.agents.models import get_text

CHAT_MODEL_KEY: Final[str] = "deepseek_flash"
DEFAULT_AGENT_NAME: Final[str] = "知识库助手"
DEFAULT_MAX_TEXT_CHARS: Final[int] = 2000
_ENABLED_ENV: Final[str] = "KNOWLEDGE_CHAT_ENABLED"
_MAX_CHARS_ENV: Final[str] = "KNOWLEDGE_CHAT_MAX_CHARS"


@dataclass(frozen=True)
class ChatConfig:
    """
    一次文字问答会话的配置。

    Attributes:
        model: 正式模型名，如 deepseek-flash。
        api_key_env: 读取密钥的环境变量名。
        max_text_chars: 单条用户文本的长度上限。
        enabled: 文字入口是否启用。

    Raises:
        FrozenInstanceError: 配置不可变。
    """

    model: str
    api_key_env: str
    max_text_chars: int
    enabled: bool


def _read(environ: Mapping[str, str] | None, name: str, default: str = "") -> str:
    """读取一个配置项：显式传入的映射优先，否则读进程环境变量。"""
    value = environ.get(name) if environ is not None else os.environ.get(name)
    return (value or default).strip()


def _parse_bool(environ: Mapping[str, str] | None, name: str, default: bool) -> bool:
    """解析布尔配置，接受 1/true/yes/on 与 0/false/no/off。"""
    raw = _read(environ, name)
    if not raw:
        return default
    normalized = raw.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} 必须是 true/false 之一，当前为 {raw!r}")


def _parse_max_chars(environ: Mapping[str, str] | None) -> int:
    """解析单条文本长度上限，限制在 1..10000。"""
    raw = _read(environ, _MAX_CHARS_ENV)
    if not raw:
        return DEFAULT_MAX_TEXT_CHARS
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{_MAX_CHARS_ENV} 必须是整数，当前为 {raw!r}") from exc
    if not 1 <= value <= 10000:
        raise RuntimeError(f"{_MAX_CHARS_ENV} 必须在 1 到 10000 之间，当前为 {value}")
    return value


def load_chat_config(environ: Mapping[str, str] | None = None) -> ChatConfig:
    """
    读取文字问答会话的配置。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        校验完成的配置。

    Raises:
        RuntimeError: 文字入口被关闭，或配置值非法。
    """
    ready = get_text(CHAT_MODEL_KEY)
    enabled = _parse_bool(environ, _ENABLED_ENV, True)
    if not enabled:
        raise RuntimeError(f"文字问答已关闭（{_ENABLED_ENV}=false）")
    return ChatConfig(
        model=ready.model_name,
        api_key_env=ready.api_key_env,
        max_text_chars=_parse_max_chars(environ),
        enabled=True,
    )


def build_status(environ: Mapping[str, str] | None = None) -> dict:
    """
    生成文字入口的状态字段，不包含密钥。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        含 `text_model` / `text_ready` / `text_reason` 的字典。
    """
    ready = get_text(CHAT_MODEL_KEY)
    try:
        config = load_chat_config(environ)
    except RuntimeError as exc:
        return {"text_model": ready.model_name, "text_ready": False, "text_reason": str(exc)}
    api_key = _read(environ, config.api_key_env)
    if not api_key:
        return {
            "text_model": config.model,
            "text_ready": False,
            "text_reason": f"缺少 {config.api_key_env}，无法连接文字问答模型",
        }
    return {"text_model": config.model, "text_ready": True, "text_reason": ""}


__all__ = [
    "CHAT_MODEL_KEY",
    "DEFAULT_AGENT_NAME",
    "DEFAULT_MAX_TEXT_CHARS",
    "ChatConfig",
    "build_status",
    "load_chat_config",
]
