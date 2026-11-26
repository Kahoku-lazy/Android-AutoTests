"""engines-docstring-check 自检：用合成源码验证 8 条规则 + 范围判定是否按预期触发。

python -m 调试路径: scripts.selftest
（cwd 必须是本技能目录 `.agents/skills/engines-docstring-check`）

用途：改了 `scripts/docstrings.py` 的规则或范围常量后，跑一遍确认没退化，
不需要在仓库里造真实的坏文件。退出码 0 = 全部符合预期。
"""

from __future__ import annotations

import ast
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docstrings import (  # noqa: E402, I001 - 同目录脚本，需先插入 sys.path
    _function_rules,
    _module_rules,
    _tool_function_names,
    _walk_defs,
    exclusion_reason,
    in_scope,
    RULES,
)

REL = "engines/demo/sample.py"

GOOD_MODULE_DOC = """
模块功能：➡️ 演示模块，供自检使用 🏁
Python 调试：➡️python -m engines.demo.sample 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/engines/demo/test_sample.py: 演示
🏁
"""


def _rules_of_module(doc: str, rel: str = REL) -> list[str]:
    """Return the rule ids triggered by a module docstring at *rel*."""
    tree = ast.parse(f'"""{doc}"""\nx = 1\n')
    violations = _module_rules(rel, tree, ast.get_docstring(tree, clean=False) or "")
    return [v.rule for v in violations]


def _rules_of_module_with_def(doc: str, rel: str = REL) -> list[str]:
    """Same as _rules_of_module, but the module also defines a function (不是空壳)."""
    tree = ast.parse(f'"""{doc}"""\n\n\ndef demo():\n    return 1\n')
    violations = _module_rules(rel, tree, ast.get_docstring(tree, clean=False) or "")
    return [v.rule for v in violations]


def _rules_of_function(source: str, *, is_tool: bool = True) -> list[str]:
    """Return the rule ids triggered by one function source snippet."""
    tree = ast.parse(source)
    fn = tree.body[0]
    assert isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
    tool_names = {fn.name} if is_tool else set()
    return [v.rule for v in _function_rules(REL, fn, tool_names)]


def _rules_of_class(source: str) -> list[str]:
    """Return the rule ids triggered by one class source snippet."""
    tree = ast.parse(source)
    violations: list = []
    _walk_defs(tree.body, REL, violations)
    return [v.rule for v in violations]


CASES: list[tuple[str, list[str], list[str]]] = [
    (
        "合规模块头 4 字段应零报错",
        _rules_of_module(GOOD_MODULE_DOC),
        [],
    ),
    (
        "缺少其余字段",
        _rules_of_module("模块功能：➡️ 演示 🏁"),
        ["module-fields"],
    ),
    (
        "时间不是 YYYY-MM-DD",
        _rules_of_module(GOOD_MODULE_DOC.replace("2026-11-24", "2026/11/24")),
        ["module-fields"],
    ),
    (
        "模块功能写成编号列表",
        _rules_of_module(GOOD_MODULE_DOC.replace("演示模块，供自检使用", "1. demo: 演示")),
        ["module-summary"],
    ),
    (
        "测试 编号跳号",
        _rules_of_module(GOOD_MODULE_DOC.replace("1. tests/", "2. tests/")),
        ["module-numbering"],
    ),
    (
        "公开类不写 docstring 不再报错",
        _rules_of_class("class Demo:\n    x: int = 1\n"),
        [],
    ),
    (
        "普通函数不写 docstring 不再报错",
        _rules_of_function("def demo(a, b):\n    return a + b\n", is_tool=False),
        [],
    ),
    (
        "工具函数缺 docstring",
        _rules_of_function("def demo(a, b):\n    return a + b\n"),
        ["tool-docstring"],
    ),
    (
        "工具函数缺首行摘要",
        _rules_of_function(
            'def demo(a, b):\n    """\n    Args:\n        a: 甲。\n        b: 乙。\n    """\n'
            "    return a + b\n"
        ),
        ["tool-summary"],
    ),
    (
        "工具函数有参数但缺 Args",
        _rules_of_function('def demo(a, b):\n    """演示。"""\n    return a + b\n'),
        ["tool-args"],
    ),
    (
        "工具函数 Args 漏列参数",
        _rules_of_function(
            'def demo(a, b):\n    """演示。\n\n    Args:\n        a: 甲。\n    """\n    return a + b\n'
        ),
        ["tool-args"],
    ),
    (
        "工具函数写 Returns/Raises 不报错",
        _rules_of_function(
            'def demo(a):\n    """演示。\n\n    Args:\n        a: 甲。\n\n'
            '    Returns:\n        结果。\n\n    Raises:\n        ValueError: 甲为空。\n    """\n'
            "    if not a:\n        raise ValueError('x')\n    return a\n"
        ),
        [],
    ),
    # ---- 2026-11-24 全仓化：范围判定（回归护栏）----
    (
        "engines 之外的路径同样套 4 字段模板",
        _rules_of_module("普通说明，没有模板字段。", rel="tests/arch/unit/test_channels.py"),
        ["module-fields", "module-summary"],
    ),
    (
        "backend 非固定结构文件同样套模板",
        _rules_of_module("普通说明。", rel="backend/apps/accounts/services/pool.py"),
        ["module-fields", "module-summary"],
    ),
    (
        "Django api.py 不在范围（不报任何规则）",
        _rules_of_module("普通说明。", rel="backend/apps/accounts/api.py"),
        [],
    ),
    (
        "Django views_*.py / serializers.py 不在范围",
        _rules_of_module("普通说明。", rel="backend/apps/serial_log/views_upload.py"),
        [],
    ),
    (
        "migrations 不在范围",
        _rules_of_module("普通说明。", rel="backend/apps/accounts/migrations/0001_initial.py"),
        [],
    ),
    (
        "根 run.py 在范围、manage.py 不在范围",
        _rules_of_module("普通说明。", rel="run.py"),
        ["module-fields", "module-summary"],
    ),
    (
        "manage.py 按 Django 脚手架排除",
        _rules_of_module("普通说明。", rel="manage.py"),
        [],
    ),
    (
        "空壳 __init__.py 不要求模块头",
        _rules_of_module("", rel="tests/unit/__init__.py"),
        [],
    ),
    (
        "只有一行说明的 __init__.py 也算空壳（不报错）",
        _rules_of_module("知识库检索接口测试包。", rel="tests/knowledge_search/api/__init__.py"),
        [],
    ),
    (
        "带 def 的 __init__.py 不是空壳，照样要模板",
        _rules_of_module_with_def("测试包。", rel="tests/pkg/__init__.py"),
        ["module-fields", "module-summary"],
    ),
]

# 范围判定表：(路径, 是否在册, 期望的排除原因片段)
SCOPE_CASES: list[tuple[str, bool, str]] = [
    ("engines/ae_harness/tools/adb/tools.py", True, ""),
    ("backend/apps/accounts/services/pool.py", True, ""),
    ("backend/apps/case_manager/api_rows.py", False, "Django 固定脚手架"),
    ("backend/apps/task_list/media_views.py", False, "Django 固定脚手架"),
    ("backend/apps/accounts/models.py", False, "Django 固定脚手架"),
    ("backend/config/settings.py", False, "Django 固定脚手架"),
    ("backend/apps/accounts/migrations/0002_x.py", False, "migrations"),
    ("engines/ae_harness/agents/models.py", True, ""),
    ("engines/ae_harness/knowledge/models.py", True, ""),
    ("tests/arch/unit/test_channels.py", True, ""),
    ("utils/gen_arch_stats.py", True, ""),
    ("run.py", True, ""),
    ("manage.py", False, "Django 固定脚手架"),
    (".agents/skills/x/scripts/a.py", False, "顶层目录"),
    ("temps/measure.py", False, "顶层目录"),
    ("dev_docs/ARCH_PRD/a.py", False, "顶层目录"),
    ("frontend/src/x.py", False, "顶层目录"),
]


def _check_tool_detection() -> list[str]:
    """FunctionTool(...) 注册的函数应被识别为工具函数。"""
    tree = ast.parse(
        "def demo(a):\n    return a\n\n"
        "def build():\n    return [FunctionTool(demo, is_concurrency_safe=False)]\n"
    )
    detected = _tool_function_names(tree)
    return [] if detected == {"demo"} else [f"tool-detect={sorted(detected)}"]


def _check_scope_table() -> list[str]:
    """范围判定表：in_scope / exclusion_reason 必须与规范 §1 一致。"""
    problems: list[str] = []
    for rel, expected_scope, expected_reason in SCOPE_CASES:
        actual_scope = in_scope(rel)
        if actual_scope != expected_scope:
            problems.append(f"{rel}: in_scope={actual_scope} 期望 {expected_scope}")
            continue
        reason = exclusion_reason(rel)
        if expected_reason and expected_reason not in reason:
            problems.append(f"{rel}: reason={reason!r} 期望含 {expected_reason!r}")
        if not expected_reason and reason:
            problems.append(f"{rel}: 不应有排除原因，实际 {reason!r}")
    return problems


def main() -> int:
    """Run every self-check case and report mismatches."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    total = len(CASES) + 2
    failed = 0
    for name, actual, expected in CASES:
        ok = set(actual) == set(expected)
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            print(f"      expected: {sorted(set(expected))}")
            print(f"      actual  : {sorted(set(actual))}")

    detect = _check_tool_detection()
    print(f"{'PASS' if not detect else 'FAIL'}  FunctionTool 注册识别")
    if detect:
        failed += 1
        print(f"      {detect}")

    scope = _check_scope_table()
    print(f"{'PASS' if not scope else 'FAIL'}  范围判定表（规范 §1 排除清单）")
    if scope:
        failed += 1
        for problem in scope:
            print(f"      {problem}")

    print()
    print(f"{total - failed}/{total} case(s) passed; rules registered: {len(RULES)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
