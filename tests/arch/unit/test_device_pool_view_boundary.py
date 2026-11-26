from __future__ import annotations

import ast

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
VIEW = ROOT / "backend" / "apps" / "device_pool" / "views.py"

ALLOWED_RELATIVE = frozenset({"api", "contracts", "models", "pool"})

FORBIDDEN_RELATIVE = frozenset({"manager", "registry", "state_machine", "detector", "serializer"})

pytestmark = [pytest.mark.unit, pytest.mark.arch]


def relative_modules(source: str) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ImportFrom) or not node.level:
            continue
        if node.module:
            modules.add(node.module.split(".")[0])
        else:
            modules.update(alias.name.split(".")[0] for alias in node.names)
    return modules


def test_device_pool_views_discovered():
    assert VIEW.is_file(), "device_pool/views.py 不存在 —— 守卫范围失效"


def test_device_pool_views_only_reach_api_models_pool_contracts():
    imported = relative_modules(VIEW.read_text(encoding="utf-8"))

    leaked = sorted(imported & FORBIDDEN_RELATIVE)
    assert not leaked, f"device_pool/views.py 直连内部实现，应经 api.py：{leaked}"

    beyond = sorted(imported - ALLOWED_RELATIVE)
    assert not beyond, (
        f"device_pool/views.py 越界 import（只允许 api/models/pool/contracts）：{beyond}"
    )


def test_detector_flags_internal_import_snippet():
    snippet = "from .manager import registry\nfrom . import state_machine\nfrom .api import list_devices\n"

    modules = relative_modules(snippet)

    assert "manager" in modules
    assert "state_machine" in modules
    assert modules & FORBIDDEN_RELATIVE == {"manager", "state_machine"}
    assert "api" not in modules & FORBIDDEN_RELATIVE
