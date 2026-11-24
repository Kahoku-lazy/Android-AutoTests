"""
模块功能：➡️ 扫描源码抽取 import 事实：文件遍历、AST 解析、模块路径归一化 🏁
Python 调试：➡️ python -m utils.linting.scan 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无
🏁
"""

from __future__ import annotations

import ast
import fnmatch

from collections.abc import Iterator
from pathlib import Path

from utils.linting.model import Config, Edge


def is_excluded(rel_posix: str, exclude: frozenset[str]) -> bool:
    """文件自身或任一层父目录命中 exclude 即排除。"""
    parts = rel_posix.split("/")
    for depth in range(1, len(parts) + 1):
        prefix = "/".join(parts[:depth])
        if any(fnmatch.fnmatch(prefix, pattern) for pattern in exclude):
            return True
    return False


def iter_py_files(config: Config) -> Iterator[tuple[Path, str]]:
    """按 source_roots 递归收 .py，产出 (绝对路径, 相对项目根的正斜杠路径)。"""
    seen: set[Path] = set()
    for source_root in config.source_roots:
        for path in sorted(source_root.rglob("*.py")):
            if path in seen:
                continue
            seen.add(path)
            rel_posix = path.relative_to(config.root).as_posix()
            if not is_excluded(rel_posix, config.exclude):
                yield path, rel_posix


def to_dotted(rel_posix: str) -> str:
    """a/b/c.py → a.b.c；a/b/__init__.py → a.b。"""
    return rel_posix[: -len(".py")].replace("/", ".").removesuffix(".__init__")


def package_of(rel_posix: str) -> str:
    """文件所在包的导入路径，作为相对 import 的锚点。"""
    dotted = rel_posix[: -len(".py")].replace("/", ".").removesuffix(".__init__")
    return dotted.rpartition(".")[0]


def nearest_module(dotted_path: str, modules: dict[str, dict]) -> str:
    """最长前缀匹配：该路径归属的最近一个已登记模块；空串表示 root 模块。"""
    best = ""
    for module_path in modules:
        if (dotted_path == module_path or dotted_path.startswith(module_path + ".")) and (
            len(module_path) > len(best)
        ):
            best = module_path
    return best


def is_type_checking_guard(test: ast.expr) -> bool:
    """识别 `if TYPE_CHECKING:` 与 `if typing.TYPE_CHECKING:` 两种写法。"""
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def iter_imports(tree: ast.AST) -> Iterator[tuple[ast.Import | ast.ImportFrom, bool]]:
    """遍历全部 import 节点，并标记它是否位于 TYPE_CHECKING 分支内。"""

    def walk(
        node: ast.AST, inside_type_checking: bool
    ) -> Iterator[tuple[ast.Import | ast.ImportFrom, bool]]:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node, inside_type_checking
            return
        guarded = isinstance(node, ast.If) and is_type_checking_guard(node.test)
        for child in ast.iter_child_nodes(node):
            yield from walk(child, inside_type_checking or (guarded and child in node.body))

    yield from walk(tree, False)


def imports_of(
    node: ast.Import | ast.ImportFrom, package: str, importable: set[str]
) -> list[tuple[str, int]]:
    """把一条 import 归一化成 [(完整模块路径, 行号)]。

    `from a import b` 里的 b 可能是子模块、也可能是 a 里的符号：只有项目内确实存在
    `a.b` 这个可导入路径时才取更长的那条，否则按 `a` 计算。
    """
    if isinstance(node, ast.Import):
        return [(alias.name, node.lineno) for alias in node.names]

    base = node.module or ""
    if node.level:
        parts = package.split(".") if package else []
        if node.level > 1:
            parts = parts[: len(parts) - (node.level - 1)]
        base = ".".join([*parts, base]).strip(".")

    found: list[tuple[str, int]] = []
    for alias in node.names:
        candidate = f"{base}.{alias.name}" if base else alias.name
        found.append((candidate if candidate in importable else base, node.lineno))
    return found


def collect_importable(files: list[tuple[Path, str]]) -> set[str]:
    """项目内所有可 import 的路径（各级包与模块），用于判定子模块。"""
    importable: set[str] = set()
    for _, rel_posix in files:
        parts = to_dotted(rel_posix).split(".")
        importable.update(".".join(parts[: depth + 1]) for depth in range(len(parts)))
    return importable


def is_internal(path: str, root_packages: list[str]) -> bool:
    """该路径是否落在某个 root package（内部包）内。"""
    return any(path == root or path.startswith(root + ".") for root in root_packages)


def collect_edges(config: Config) -> tuple[list[Edge], int]:
    """扫全量文件，产出统一的三元事实：文件 → import → 目标节点。"""
    files = list(iter_py_files(config))
    importable = collect_importable(files)
    edges: list[Edge] = []
    scanned = 0

    for path, rel_posix in files:
        scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        importer = to_dotted(rel_posix)
        for node, inside_type_checking in iter_imports(tree):
            if inside_type_checking and config.ignore_type_checking:
                continue
            for imported, line in imports_of(node, package_of(rel_posix), importable):
                if is_internal(imported, config.root_packages):
                    target = imported
                elif config.include_external:
                    target = imported.split(".")[0]
                else:
                    target = imported
                edges.append(Edge(importer, imported, target, rel_posix, line))

    return edges, scanned
