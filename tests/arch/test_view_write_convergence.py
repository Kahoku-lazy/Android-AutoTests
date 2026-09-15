"""D3 写库收敛守卫 — View 层不得直写 ORM，写库只经 api.py。

依据 `apps/AGENTS.md` §1.2 红线（「View / Consumer / Tool 直接 ORM 写」与
「写库路径：View / Tool → api.py → ORM」），把 `django-backend-check/references/calibration.md` §7
列为**手工** `rg` 扫描的那条固化成可执行的 `arch` 层门禁。

判据（用 `ast` 只判定调用，避免命中注释/字符串中提到的模式）：

1. 调用接收链末位是 `save` / `delete` —— 无条件判违规。
   `save` / `delete` 在内建类型与常用库里没有同义方法，裸名接收者
   （`instance.delete()` / `serializer.save()`）几乎必然是 ORM —— 这正是 ③-1 修掉的写法。
2. 链上出现 `objects` 且末位是 `create` / `bulk_create` / `get_or_create` /
   `update_or_create` / `update` / `add` / `remove` / `set` / `clear` —— 判违规。
   这些方法名同时是 `dict` / `set` 的合法方法（如 `request.data.update(...)`），
   故必须同时要求 `objects` 出现在接收链上。

**未覆盖**：经实例关系管理器写多对多（如 `bank.questions.add(q)`）—— 语法上与集合操作
无法区分，仍需按 `calibration.md` §7 人工扫描。本守卫只覆盖可静态判定的部分。

运行：`pytest tests/arch/test_view_write_convergence.py -v`   或   `pytest -m arch -v`
"""

from __future__ import annotations

import ast

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VIEW_MODULES = sorted((ROOT / "apps").glob("*/views*.py"))

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
    assert VIEW_MODULES, "未发现 apps/*/views*.py —— 守卫范围失效"
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
        'WebElement.objects.create(name="x")\n'
        "EvalRun.objects.filter(id=1).delete()\n"
        'WebElement.objects.filter(id=1).update(name="y")\n'
        "request.data.update({'a': 1})\n"
        "# Model.objects.create() 只出现在注释里，不应命中\n"
    )

    names = [name for _, name in find_orm_writes(snippet)]

    assert "instance.delete" in names
    assert "serializer.save" in names
    assert "WebElement.objects.create" in names
    assert "EvalRun.objects.filter.delete" in names
    assert "WebElement.objects.filter.update" in names
    # 判据 2 的边界：没有 objects 的 .update() 是 dict 的合法方法，不得误报
    assert "request.data.update" not in names
