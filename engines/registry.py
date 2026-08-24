"""L1c 引擎层 — 注册表与工厂（可替换插槽，借鉴 provider_registry 先例）。

失败策略与 provider_registry 不同：引擎**未知名/未实现即 fail-fast**
（抛 ConfigurationError），不做静默回退。

层纯度：不 import django settings——引擎名由调用方（未来 DeviceSession）
从 settings 解析后传入。
"""

import importlib
import threading

from typing import Optional

from .base import UiEngine

__all__ = ["ConfigurationError", "ENGINE_REGISTRY", "DEFAULT_ENGINE", "get_device_engine"]


class ConfigurationError(RuntimeError):
    """引擎配置错误：未知名 / 未实现 / 构建失败。"""


# 引擎名 → 实现类 import 路径（懒加载，实例化延迟到首次取用）
ENGINE_REGISTRY = {
    "airtest_u2": "engines.android.airtest_u2.AirtestU2Engine",
    # 未来插槽示例： "cloud": "engines.android.cloud.CloudDeviceEngine",
}

DEFAULT_ENGINE = "airtest_u2"

_instances: dict = {}
_instances_lock = threading.Lock()


def _resolve_path(name: str) -> str:
    if name not in ENGINE_REGISTRY:
        raise ConfigurationError(
            f"Unknown engine '{name}'. Registered engines: {sorted(ENGINE_REGISTRY)}"
        )
    return ENGINE_REGISTRY[name]


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


def get_device_engine(name: str = DEFAULT_ENGINE) -> UiEngine:
    """按名取引擎实例（惰性 import + 进程内缓存，线程安全）。

    Args:
        name: 引擎名（调用方从 settings.DEVICE_ENGINE 解析后传入）。

    Raises:
        ConfigurationError: 未知名 / 未实现 / 构建失败。
    """
    if name in _instances:
        return _instances[name]

    with _instances_lock:
        if name in _instances:
            return _instances[name]
        engine_cls = _import_engine(name)
        instance: Optional[UiEngine] = None
        try:
            instance = engine_cls()
        except Exception as e:
            raise ConfigurationError(f"Engine '{name}' failed to build: {e}") from e
        _instances[name] = instance
        return instance
