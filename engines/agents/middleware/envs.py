"""
python -m 调试路径: engines.agents.middleware.envs

本模块的业务功能如下：
1. env_flag / env_int / env_float: 读环境变量的三个小工具，非法值回落默认。
"""

from __future__ import annotations

import os

_TRUTHY = {"1", "true", "yes", "on"}


def env_flag(name: str, default: bool = False) -> bool:
    """读一个布尔开关。

    Args:
        name: 环境变量名。
        default: 未设置时使用的值。

    Returns:
        设置且属于真值集合返回 True；设置但为假值返回 False。
    """
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in _TRUTHY


def env_int(name: str, default: int) -> int:
    """读一个整数环境变量，缺省或非法时回落默认值。

    Args:
        name: 环境变量名。
        default: 读不到或非法时使用的值。

    Returns:
        解析出的整数。
    """
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    """读一个浮点环境变量，缺省或非法时回落默认值。

    Args:
        name: 环境变量名。
        default: 读不到或非法时使用的值。

    Returns:
        解析出的浮点数。
    """
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default
