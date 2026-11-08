"""engines-docstring-check 自检：用合成源码验证 13 条规则是否按预期触发。

python -m 调试路径: scripts.selftest
（cwd 必须是本技能目录 `.agents/skills/engines-docstring-check`）

用途：改了 `scripts/docstrings.py` 的规则后，跑一遍确认规则没退化，
不需要在仓库里造真实的坏文件（那会污染 engines/）。退出码 0 = 全部符合预期。
"""

from __future__ import annotations

import ast
import sys

from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docstrings import (  # noqa: E402, I001 - 同目录脚本，需先插入 sys.path
    _function_rules,
    _module_rules,
    _walk_defs,
    RULES,
)

REL = "engines/demo/sample.py"

GOOD_MODULE_DOC = """
文件名: ➡️ sample.py 🏁
路径: ➡️ engines/demo/sample.py 🏁
模块功能：➡️ 演示模块，供自检使用 🏁
Python 调试：➡️ python -m engines.demo.sample 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoko 🏁
版本：➡️ 1.0.0 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. demo: 演示函数
2. helper: 辅助函数
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/engines/demo/test_sample.py: 演示
🏁
"""


@dataclass
class Case:
    """一个自检用例。"""

    name: str
    expected: list[str]


def _rules_of_module(doc: str) -> list[str]:
    """Return the rule ids triggered by a module docstring."""
    tree = ast.parse(f'"""{doc}"""\nx = 1\n')
    violations = _module_rules(REL, tree, ast.get_docstring(tree, clean=False) or "")
    return [v.rule for v in violations]


def _rules_of_function(source: str) -> list[str]:
    """Return the rule ids triggered by one function source snippet."""
    tree = ast.parse(source)
    fn = tree.body[0]
    assert isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
    return [v.rule for v in _function_rules(REL, fn)]


def _rules_of_class(source: str) -> list[str]:
    """Return the rule ids triggered by one class source snippet."""
    tree = ast.parse(source)
    violations: list = []
    _walk_defs(tree.body, REL, violations)
    return [v.rule for v in violations]


CASES: list[tuple[str, list[str], list[str]]] = [
    (
        "合规模块 docstring 应零报错",
        _rules_of_module(GOOD_MODULE_DOC),
        [],
    ),
    (
        "缺字段 + 类型非法",
        _rules_of_module("文件名: ➡️ sample.py 🏁\n模块功能：➡️ 演示 🏁\n类型: ➡️ 随便模块 🏁"),
        ["module-fields"],
    ),
    (
        "模块功能写成编号列表",
        _rules_of_module(GOOD_MODULE_DOC.replace("演示模块，供自检使用", "1. demo: 演示")),
        ["module-summary"],
    ),
    (
        "简介说明编号跳号",
        _rules_of_module(GOOD_MODULE_DOC.replace("2. helper: 辅助函数", "3. helper: 辅助函数")),
        ["module-numbering"],
    ),
    (
        "公开类缺 docstring",
        _rules_of_class("class Demo:\n    x: int = 1\n"),
        ["class-docstring"],
    ),
    (
        "类字段未写 Attributes",
        _rules_of_class('class Demo:\n    """演示类。"""\n\n    x: int = 1\n'),
        ["class-attributes"],
    ),
    (
        "公开函数缺 docstring",
        _rules_of_function("def demo(a, b):\n    return a + b\n"),
        ["def-docstring"],
    ),
    (
        "缺摘要 + 缺 Args/Returns",
        _rules_of_function(
            'def demo(a, b):\n    """\n    Args:\n        a: 甲。\n    """\n    return a + b\n'
        ),
        ["doc-summary", "doc-args", "doc-returns"],
    ),
    (
        "Args 漏列参数",
        _rules_of_function(
            'def demo(a, b):\n    """演示。\n\n    Args:\n        a: 甲。\n\n'
            '    Returns:\n        和。\n    """\n    return a + b\n'
        ),
        ["doc-args"],
    ),
    (
        "有 raise 缺 Raises",
        _rules_of_function(
            'def demo(a):\n    """演示。\n\n    Args:\n        a: 甲。\n    """\n'
            '    raise ValueError("x")\n'
        ),
        ["doc-raises"],
    ),
    (
        "段序错（Raises 在 Returns 前）",
        _rules_of_function(
            'def demo(a):\n    """演示。\n\n    Args:\n        a: 甲。\n\n'
            '    Raises:\n        ValueError: 甲为空。\n\n    Returns:\n        结果。\n    """\n'
            "    if not a:\n        raise ValueError('x')\n    return a\n"
        ),
        ["doc-order"],
    ),
    (
        "生成器用 Yields 不强制 Returns",
        _rules_of_function(
            'def demo(a):\n    """演示。\n\n    Args:\n        a: 甲。\n\n'
            '    Yields:\n        甲。\n    """\n    yield a\n'
        ),
        [],
    ),
]


def main() -> int:
    """Run every self-check case and report mismatches."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    unknown = len(RULES)
    failed = 0
    for name, actual, expected in CASES:
        ok = set(actual) == set(expected)
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            print(f"      expected: {sorted(set(expected))}")
            print(f"      actual  : {sorted(set(actual))}")

    print()
    print(f"{len(CASES) - failed}/{len(CASES)} case(s) passed; rules registered: {unknown}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
