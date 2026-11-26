from __future__ import annotations

from enum import Enum

import pytest

from backend.models import constants as models_constants

pytestmark = [pytest.mark.unit]

SSOT_MODULES = (models_constants,)

MIN_DISCOVERED_ENUMS = 11


def _discover_enums() -> list[tuple[str, type[Enum]]]:
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
    names = [name for name, _ in ENUMS]
    assert len(ENUMS) >= MIN_DISCOVERED_ENUMS, names


def test_member_stringifies_to_value():
    offenders = [
        f"{name}.{m.name}: str={str(m)!r} f={f'{m}'!r} value={m.value!r}"
        for name, enum_cls in ENUMS
        for m in enum_cls
        if str(m) != m.value or f"{m}" != m.value
    ]
    assert offenders == [], offenders


def test_member_is_str_subclass():
    offenders = [
        f"{name}.{m.name}" for name, enum_cls in ENUMS for m in enum_cls if not isinstance(m, str)
    ]
    assert offenders == [], offenders


def test_member_compares_and_hashes_as_value():
    offenders = [
        f"{name}.{m.name}"
        for name, enum_cls in ENUMS
        for m in enum_cls
        if not (m == m.value and hash(m) == hash(m.value))
    ]
    assert offenders == [], offenders
