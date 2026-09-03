"""AI 引擎层 — 注册表与工厂（可替换插槽，对齐 engines/device/registry.py）。

失败策略：引擎未知名 / 不可导入 / 构建失败即 fail-fast（抛 ConfigurationError），
不做静默回退。层纯度：不 import django settings——引擎名由调用方从 settings 解析后传入。
"""

from __future__ import annotations

import importlib
import threading

from typing import Optional

from .base import AiEngine

__all__ = ["AI_ENGINE_REGISTRY", "DEFAULT_ENGINE", "ConfigurationError", "get_ai_engine"]


class ConfigurationError(RuntimeError):
    """引擎配置错误：未知名 / 未实现 / 构建失败。"""


# 引擎名 → 实现类 import 路径（懒加载，实例化延迟到首次取用）
AI_ENGINE_REGISTRY = {
    "agentscope": "engines.ai.agentscope.engine.AgentScopeEngine",
    # 未来插槽示例： "langchain": "engines.ai.langchain.engine.LangChainEngine",
}

DEFAULT_ENGINE = "agentscope"

_instances: dict = {}
_instances_lock = threading.Lock()


def _resolve_path(name: str) -> str:
    if name not in AI_ENGINE_REGISTRY:
        raise ConfigurationError(
            f"Unknown engine '{name}'. Registered engines: {sorted(AI_ENGINE_REGISTRY)}"
        )
    return AI_ENGINE_REGISTRY[name]


def _import_engine(name: str):
    path = _resolve_path(name)
    module_path, _, attr = path.rpartition(".")
    try:
        module = importlib.import_module(module_path)
        return getattr(module, attr)
    except (ImportError, AttributeError) as e:
        raise ConfigurationError(
            f"Engine '{name}' is registered but not importable: {path} ({e})"
        ) from e


def get_ai_engine(name: str = DEFAULT_ENGINE) -> AiEngine:
    """按名取 AI 引擎实例（惰性 import + 进程内缓存，线程安全）。

    Args:
        name: 引擎名（调用方从 settings.AI_ENGINE 解析后传入）。

    Raises:
        ConfigurationError: 未知名 / 未实现 / 构建失败。
    """
    if name in _instances:
        return _instances[name]

    with _instances_lock:
        if name in _instances:
            return _instances[name]
        engine_cls = _import_engine(name)
        instance: Optional[AiEngine] = None
        try:
            instance = engine_cls()
        except Exception as e:
            raise ConfigurationError(f"Engine '{name}' failed to build: {e}") from e
        _instances[name] = instance
        return instance
