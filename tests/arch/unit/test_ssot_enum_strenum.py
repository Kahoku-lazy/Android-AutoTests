"""
模块功能：➡️ D4 SSOT 枚举基类门禁：`models/` 的枚举必须用 `StrEnum` 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/arch/unit/test_ssot_enum_strenum.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/models
🏁
"""

from __future__ import annotations

from enum import Enum

import pytest

from backend.models import constants as models_constants

pytestmark = [pytest.mark.unit]

SSOT_MODULES = (models_constants,)

# `models/` 内 SSOT 枚举总数（constants 11）；仅作「发现没漏」的下限
MIN_DISCOVERED_ENUMS = 11


def _discover_enums() -> list[tuple[str, type[Enum]]]:
    """取出 SSOT 模块内**自行定义**的枚举子类（不硬编码清单，也不含 enum 基类）。"""
    found: list[tuple[str, type[Enum]]] = []
    for module in SSOT_MODULES:
        for name, obj in vars(module).items():
            if (
                isinstance(obj, type)
                and issubclass(obj, Enum)
                and obj.__module__ == module.__name__
            ):
                found.append((f"{module.__name__}.{name}", obj))
    return found


ENUMS = _discover_enums()


def test_discovery_covers_ssot_enums():
    """门禁自身有效性：动态发现必须覆盖两模块的全部 SSOT 枚举。"""
    names = [name for name, _ in ENUMS]
    assert len(ENUMS) >= MIN_DISCOVERED_ENUMS, names


def test_member_stringifies_to_value():
    """核心不变量：`str(member)` 与 f-string 必须等于 `member.value`（而非限定名）。"""
    offenders = [
        f"{name}.{m.name}: str={str(m)!r} f={f'{m}'!r} value={m.value!r}"
        for name, enum_cls in ENUMS
        for m in enum_cls
        if str(m) != m.value or f"{m}" != m.value
    ]
    assert offenders == [], offenders


def test_member_is_str_subclass():
    """成员必须仍是 `str` 子类：Django CharField 与 json 才能直用。"""
    offenders = [
        f"{name}.{m.name}" for name, enum_cls in ENUMS for m in enum_cls if not isinstance(m, str)
    ]
    assert offenders == [], offenders


def test_member_compares_and_hashes_as_value():
    """与字面量比较 / 哈希必须等价 —— D4-1 收敛字面量依赖这两条性质。"""
    offenders = [
        f"{name}.{m.name}"
        for name, enum_cls in ENUMS
        for m in enum_cls
        if not (m == m.value and hash(m) == hash(m.value))
    ]
    assert offenders == [], offenders
