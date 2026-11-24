"""engines-docstring-check 自检：用合成源码验证 8 条规则是否按预期触发。

python -m 调试路径: scripts.selftest
（cwd 必须是本技能目录 `.agents/skills/engines-docstring-check`）

用途：改了 `scripts/docstrings.py` 的规则后，跑一遍确认规则没退化，
不需要在仓库里造真实的坏文件（那会污染 engines/）。退出码 0 = 全部符合预期。
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


def _rules_of_module(doc: str) -> list[str]:
    """Return the rule ids triggered by a module docstring."""
    tree = ast.parse(f'"""{doc}"""\nx = 1\n')
    violations = _module_rules(REL, tree, ast.get_docstring(tree, clean=False) or "")
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
]


def _check_tool_detection() -> list[str]:
    """FunctionTool(...) 注册的函数应被识别为工具函数。"""
    tree = ast.parse(
        "def demo(a):\n    return a\n\n"
        "def build():\n    return [FunctionTool(demo, is_concurrency_safe=False)]\n"
    )
    detected = _tool_function_names(tree)
    return [] if detected == {"demo"} else [f"tool-detect={sorted(detected)}"]


def main() -> int:
    """Run every self-check case and report mismatches."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    total = len(CASES) + 1
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

    print()
    print(f"{total - failed}/{total} case(s) passed; rules registered: {len(RULES)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
