"""L1c 引擎层 — 注册表与工厂（可替换插槽，借鉴 provider_registry 先例）。

失败策略与 provider_registry 不同：引擎**未知名/未实现即 fail-fast**
（抛 ConfigurationError），不做静默回退。

层纯度：不 import django settings——引擎名由调用方（未来 DeviceSession）
从 settings 解析后传入。
"""

import importlib

from .base import UiEngine

__all__ = [
    "ConfigurationError",
    "ENGINE_REGISTRY",
    "DEFAULT_ENGINE",
    "close_engine",
    "get_device_engine",
    "open_engine",
]


class ConfigurationError(RuntimeError):
    """引擎配置错误：未知名 / 未实现 / 构建失败。"""


# 引擎名 → 实现类 import 路径（懒加载，实例化延迟到首次取用）
ENGINE_REGISTRY = {
    "u2": "engines.device.android.u2.U2Engine",
    # 未来插槽示例： "cloud": "engines.device.android.cloud.CloudDeviceEngine",
}

DEFAULT_ENGINE = "u2"


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
    """按名创建引擎实例（惰性 import，每次返回新实例）。

    设备引擎持有连接状态（_u2），不可跨设备共享，故不做进程内缓存。

    Args:
        name: 引擎名（调用方从 settings.DEVICE_ENGINE 解析后传入）。

    Raises:
        ConfigurationError: 未知名 / 未实现 / 构建失败。
    """
    engine_cls = _import_engine(name)
    try:
        return engine_cls()
    except Exception as e:
        raise ConfigurationError(f"Engine '{name}' failed to build: {e}") from e


def open_engine(serial: str, addr: str = "", name: str = DEFAULT_ENGINE, on_log=None) -> UiEngine:
    """打开引擎并建立连接（短连接：调用方用完需 close_engine 断开）。

    不做缓存/锁/租用——连接生命周期由调用方自管。
    """
    engine = get_device_engine(name)
    engine.connect(serial, addr, on_log=on_log)
    return engine


def close_engine(engine: UiEngine) -> None:
    """断开引擎连接。"""
    engine.disconnect()
