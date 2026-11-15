"""
文件名: ➡️ loader.py 🏁
路径: ➡️ engines/agents/models/loader.py 🏁
模块功能：➡️ 从整张模型表里取一条，按 family 校验并解析成参数对象 🏁
Python 调试：➡️ python -m engines.agents.models.loader 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 3.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. parse: 按短名取条目 → 看 family 选校验类 → 返回参数对象；只对 create 内部可见。
2. 表由 config 读好传入；本模块不碰文件、不碰环境变量、不碰密钥解密。
🏁
关联模块：➡️
1. engines.agents.models.schema: 导入 FAMILIES / ModelConfigError / validate_model。
🏁
测试：➡️
1. 待功能定型后补：按族校验与错误定位
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .schema import FAMILIES, ModelConfigError, validate_model

__all__ = ["parse"]


def parse(catalog: Mapping[str, Any], short_name: str) -> Any:
    """
    从整张表里取一条并校验解析。

    族由条目自己的 `family` 字段决定，调用方不需要先说"这是哪类模型"。

    Args:
        catalog: config 读好的整张模型表。
        short_name: 模型短名，同时用作报错定位。

    Returns:
        已校验的参数对象（三个类之一）。

    Raises:
        ModelConfigError: 表不是映射表、短名不存在、条目不是映射表、family 未知，
            或校验不通过。
    """
    if not isinstance(catalog, Mapping):
        raise ModelConfigError(
            f"模型表: 顶层必须是映射表，收到 {type(catalog).__name__}",
        )
    raw = catalog.get(short_name)
    if raw is None:
        raise ModelConfigError(
            f"未知模型 {short_name!r}；可选：{', '.join(sorted(str(k) for k in catalog)) or '无'}",
        )
    if not isinstance(raw, dict):
        raise ModelConfigError(f"{short_name}: 必须是映射表，收到 {type(raw).__name__}")
    family = str(raw.get("family") or "").strip()
    if family not in FAMILIES:
        raise ModelConfigError(
            f"{short_name}.family: 必须是 {' / '.join(FAMILIES)}，收到 {family!r}"
        )
    return validate_model(family, raw, source=short_name)
