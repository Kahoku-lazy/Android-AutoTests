"""
模块功能：➡️ D3 写库收敛守卫 — View 层不得直写 ORM，写库只经 api.py 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/arch/unit/test_view_write_convergence.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 前端与后端源码的一致性面（只读源码断言）
🏁
"""

from __future__ import annotations

import ast

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
VIEW_MODULES = sorted((ROOT / "backend" / "apps").glob("*/views*.py"))

# 末位方法名 → 必须同时出现 objects 才判违规（这些名字也是 dict/set 的合法方法）
ORM_MANAGER_WRITES = frozenset(
    {
        "create",
        "bulk_create",
        "get_or_create",
        "update_or_create",
        "update",
        "add",
        "remove",
        "set",
        "clear",
    }
)

# 末位方法名 → 无条件判违规（内建类型/常用库无同义方法）
UNCONDITIONAL_WRITES = frozenset({"save", "delete"})

pytestmark = [pytest.mark.unit, pytest.mark.arch]


def _receiver_chain(func: ast.AST) -> list[str]:
    """把调用接收者拍平成名字链。

    `Model.objects.filter(...).delete` → `["Model", "objects", "filter", "delete"]`
    （中间夹着 Call 也要穿过去，否则 `.filter(...).delete()` 会被漏掉）
    """
    parts: list[str] = []
    node: ast.AST = func
    while True:
        if isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        elif isinstance(node, ast.Call):
            node = node.func
        else:
            break
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return list(reversed(parts))


def find_orm_writes(source: str) -> list[tuple[int, str]]:
    """返回 [(行号, 调用链名)]，即该源码里的直写 ORM 调用。"""
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        chain = _receiver_chain(node.func)
        if not chain:
            continue
        method = chain[-1]
        if method in UNCONDITIONAL_WRITES:
            found.append((node.lineno, ".".join(chain)))
        elif method in ORM_MANAGER_WRITES and "objects" in chain:
            found.append((node.lineno, ".".join(chain)))
    return found


def test_view_modules_discovered():
    """范围自检：通配失效时守卫会静默变成空测试，故必须断言真的发现了模块。"""
    assert VIEW_MODULES, "未发现 backend/apps/*/views*.py —— 守卫范围失效"
    assert len(VIEW_MODULES) >= 10, f"仅发现 {len(VIEW_MODULES)} 个 views 模块，范围可疑"


@pytest.mark.parametrize("module_path", VIEW_MODULES, ids=lambda p: p.name)
def test_view_module_has_no_direct_orm_write(module_path: Path):
    """View 层直写 ORM 即违规（D3 契约：写库只经 api.py）。"""
    writes = find_orm_writes(module_path.read_text(encoding="utf-8"))

    assert not writes, f"{module_path.name} 直接写 ORM，应改为调用本 App api.py：" + "; ".join(
        f"L{line} {name}" for line, name in writes
    )


def test_detector_flags_known_violations():
    """正对照：守卫必须能命中已知违规写法，否则它只是一条永远绿的假门禁。"""
    snippet = (
        "instance.delete()\n"
        "serializer.save()\n"
        'Element.objects.create(alias="x")\n'
        "EvalRun.objects.filter(id=1).delete()\n"
        'Element.objects.filter(id=1).update(alias="y")\n'
        "request.data.update({'a': 1})\n"
        "# Model.objects.create() 只出现在注释里，不应命中\n"
    )

    names = [name for _, name in find_orm_writes(snippet)]

    assert "instance.delete" in names
    assert "serializer.save" in names
    assert "Element.objects.create" in names
    assert "EvalRun.objects.filter.delete" in names
    assert "Element.objects.filter.update" in names
    # 判据 2 的边界：没有 objects 的 .update() 是 dict 的合法方法，不得误报
    assert "request.data.update" not in names
