from __future__ import annotations

import ast
import fnmatch

from collections.abc import Iterator
from pathlib import Path

from utils.linting.model import Config, Edge


def is_excluded(rel_posix: str, exclude: frozenset[str]) -> bool:
    parts = rel_posix.split("/")
    for depth in range(1, len(parts) + 1):
        prefix = "/".join(parts[:depth])
        if any(fnmatch.fnmatch(prefix, pattern) for pattern in exclude):
            return True
    return False


def iter_py_files(config: Config) -> Iterator[tuple[Path, str]]:
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
    return rel_posix[: -len(".py")].replace("/", ".").removesuffix(".__init__")


def package_of(rel_posix: str) -> str:
    dotted = rel_posix[: -len(".py")].replace("/", ".").removesuffix(".__init__")
    return dotted.rpartition(".")[0]


def nearest_module(dotted_path: str, modules: dict[str, dict]) -> str:
    best = ""
    for module_path in modules:
        if (dotted_path == module_path or dotted_path.startswith(module_path + ".")) and (
            len(module_path) > len(best)
        ):
            best = module_path
    return best


def is_type_checking_guard(test: ast.expr) -> bool:
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def iter_imports(tree: ast.AST) -> Iterator[tuple[ast.Import | ast.ImportFrom, bool]]:
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
    importable: set[str] = set()
    for _, rel_posix in files:
        parts = to_dotted(rel_posix).split(".")
        importable.update(".".join(parts[: depth + 1]) for depth in range(len(parts)))
    return importable


def is_internal(path: str, root_packages: list[str]) -> bool:
    return any(path == root or path.startswith(root + ".") for root in root_packages)


def collect_edges(config: Config) -> tuple[list[Edge], int]:
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
