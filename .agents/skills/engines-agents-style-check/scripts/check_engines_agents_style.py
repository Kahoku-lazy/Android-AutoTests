"""engines 风格检查：用 AST 扫描 docstring / Raises / tool 命名与段序 / engines 禁 django·apps import。
风格正文：.agents/rules/engines-code-style.md（§§2、5、6 等可机械化子集）。
何时检查 / 流程入口：engines/AGENTS.md。仅依赖标准库。

本模块的业务功能如下：
1. check_engines_agents_style: 扫描 engines/ 并报告与规范正文不符的机械化项。

python -m 调试路径: scripts.check_engines_agents_style
（cwd 必须是本技能目录 `.agents/skills/engines-agents-style-check`）

Usage（请先 cd 到本技能目录，再执行）:

    python -m scripts.check_engines_agents_style
        默认全量扫描 <repo>/engines/，文本输出。
        退出码：无违规 0，有违规 1。

    python -m scripts.check_engines_agents_style --path engines/agents/tools
        只扫描指定目录或文件（相对路径相对仓库根，不是 cwd；也可传绝对路径）。

    python -m scripts.check_engines_agents_style --format json
        JSON 输出便于脚本/CI；可与 --path 同时使用。

Exit codes:
    0  no violations
    1  one or more violations
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Walk parents from *start* until a dir with engines/AGENTS.md is found.

    Prefer a candidate that also has `.agents/skills/` (this skill's home).
    """
    fallback: Path | None = None
    for parent in [start, *start.parents]:
        if not (parent / "engines" / "AGENTS.md").is_file():
            continue
        if (parent / ".agents" / "skills").is_dir():
            return parent
        if fallback is None:
            fallback = parent
    if fallback is not None:
        return fallback
    raise SystemExit(
        "Cannot locate Android-AutoTests repo root from "
        f"{start}: expected a parent directory containing engines/AGENTS.md "
        "(preferably also .agents/skills/)."
    )


ROOT = _find_repo_root(Path(__file__).resolve())
DEFAULT_ROOT = ROOT / "engines"

SKIP_DIR_NAMES = frozenset({"__pycache__", ".venv", "venv"})
# Same idea as ruff.toml: vendored skill-creator under engines/agents/skills
SKILL_CREATOR_MARKER = ("engines", "agents", "skills")

RULE_MODULE_DOC = "module-docstring"
RULE_RAISES = "raises-doc"
RULE_TOOL_NAME = "tool-naming"
RULE_TOOL_ORDER = "tool-doc-order"
RULE_NO_DJANGO = "no-django-apps-import"

SECTION_RE = re.compile(r"^(Args|Returns|Raises|Yields|Note|Notes|Example|Examples):\s*$")
RAISES_TYPE_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*:")


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    lineno: int
    message: str


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _is_skill_creator(path: Path) -> bool:
    """Skip engines/agents/skills/**/skill-creator/** (same idea as ruff.toml)."""
    parts = path.resolve().parts
    try:
        engines_idx = parts.index("engines")
    except ValueError:
        return False
    tail = parts[engines_idx:]
    if len(tail) < 4:
        return False
    if tail[0] == "engines" and tail[1] == "agents" and tail[2] == "skills":
        return "skill-creator" in tail[3:]
    return False


def iter_py_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    if base.is_file():
        return [base] if base.suffix == ".py" else []
    out: list[Path] = []
    for path in sorted(base.rglob("*.py")):
        if SKIP_DIR_NAMES & set(path.parts):
            continue
        if _is_skill_creator(path):
            continue
        out.append(path)
    return out


def _module_docstring(tree: ast.Module) -> str | None:
    return ast.get_docstring(tree, clean=False)


def _body_without_doc(tree: ast.Module) -> list[ast.stmt]:
    body = list(tree.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(
        getattr(body[0], "value", None), ast.Constant
    ):
        if isinstance(body[0].value.value, str):
            return body[1:]
    return body


def _has_defs(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Skip nested? For __init__ skip decision, any top-level or nested counts
            # as "has classes/functions"
            if node is tree:
                continue
            return True
    # walk includes the module itself only as Module, so FunctionDef/ClassDef are enough
    return any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in ast.walk(tree)
    )


def check_module_docstring(path: Path, tree: ast.Module) -> list[Violation]:
    rel = _rel(path)
    if path.name == "__init__.py":
        stmts = _body_without_doc(tree)
        has_defs = any(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for n in tree.body
        )
        if not has_defs and len(stmts) <= 2:
            return []
    if _module_docstring(tree) is None or not str(_module_docstring(tree)).strip():
        return [
            Violation(
                RULE_MODULE_DOC,
                rel,
                1,
                "missing module docstring (.agents/rules/engines-code-style.md §2)",
            )
        ]
    return []


def _looks_like_exc_type(name: str) -> bool:
    """Heuristic: exception types are PascalCase / *Error / *Exception; skip vars like last_error."""
    if name.endswith(("Error", "Exception", "Exit", "Warning")):
        return True
    return bool(name) and name[0].isupper() and "_" not in name


def _exc_name_from_raise(node: ast.Raise) -> str | None:
    """Return exception type name for `raise Name` / `raise Name(...)` / attr forms.

    Bare `raise some_var` (stored instance) is ignored; `raise SomeError` / `raise SomeError(...)`
    are checked.
    """
    exc = node.exc
    if exc is None:
        return None  # bare re-raise
    if isinstance(exc, ast.Name):
        return exc.id if _looks_like_exc_type(exc.id) else None
    if isinstance(exc, ast.Attribute):
        return exc.attr if _looks_like_exc_type(exc.attr) else None
    if isinstance(exc, ast.Call):
        func = exc.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
    return None


def _doc_sections(doc: str) -> dict[str, tuple[int, str]]:
    """Map section title → (1-based line offset within docstring, section body text)."""
    lines = doc.splitlines()
    sections: dict[str, tuple[int, str]] = {}
    current: str | None = None
    start = 0
    buf: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = SECTION_RE.match(stripped)
        if m:
            if current is not None:
                sections[current] = (start, "\n".join(buf))
            current = m.group(1)
            start = i + 1  # 1-based within docstring
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = (start, "\n".join(buf))
    return sections


def _raises_types(raises_body: str) -> set[str]:
    found: set[str] = set()
    for line in raises_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = RAISES_TYPE_RE.match(stripped)
        if m:
            name = m.group(1)
            # Allow "pkg.Error" → also match leaf
            found.add(name)
            if "." in name:
                found.add(name.rsplit(".", 1)[-1])
    return found


def _qualname(stack: list[str], name: str) -> str:
    return ".".join([*stack, name]) if stack else name


def check_raises_docs(path: Path, tree: ast.Module, source: str) -> list[Violation]:
    """Each function/method with explicit named raise must document it under Raises:."""
    rel = _rel(path)
    violations: list[Violation] = []
    source_lines = source.splitlines()

    def visit_function(node: ast.FunctionDef | ast.AsyncFunctionDef, class_stack: list[str]) -> None:
        raised: dict[str, int] = {}
        # Collect raises only in this function body, not nested functions
        nested_defs = {
            n
            for n in ast.walk(node)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda))
            and n is not node
        }

        def in_nested(n: ast.AST) -> bool:
            for nested in nested_defs:
                for sub in ast.walk(nested):
                    if sub is n:
                        return True
            return False

        for child in ast.walk(node):
            if not isinstance(child, ast.Raise):
                continue
            if in_nested(child):
                continue
            name = _exc_name_from_raise(child)
            if name is None:
                continue
            raised.setdefault(name, child.lineno)

        if not raised:
            return

        doc = ast.get_docstring(node, clean=False)
        qname = _qualname(class_stack, node.name)
        if doc is None or not doc.strip():
            violations.append(
                Violation(
                    RULE_RAISES,
                    rel,
                    node.lineno,
                    f"{qname}: has raise but missing docstring / Raises: "
                    f"({', '.join(sorted(raised))})",
                )
            )
            return

        sections = _doc_sections(doc)
        if "Raises" not in sections:
            violations.append(
                Violation(
                    RULE_RAISES,
                    rel,
                    node.lineno,
                    f"{qname}: has raise but docstring missing Raises: "
                    f"({', '.join(sorted(raised))})",
                )
            )
            return

        documented = _raises_types(sections["Raises"][1])
        for exc_name, lineno in sorted(raised.items(), key=lambda x: x[1]):
            if exc_name not in documented and not any(
                d == exc_name or d.endswith("." + exc_name) for d in documented
            ):
                # show a snippet of the raise line when available
                snippet = ""
                if 1 <= lineno <= len(source_lines):
                    snippet = f" — `{source_lines[lineno - 1].strip()}`"
                violations.append(
                    Violation(
                        RULE_RAISES,
                        rel,
                        lineno,
                        f"{qname}: raise {exc_name} not listed in Raises:{snippet}",
                    )
                )

    def walk_body(body: list[ast.stmt], class_stack: list[str]) -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit_function(stmt, class_stack)
                # nested functions
                walk_body(stmt.body, [*class_stack, stmt.name])
            elif isinstance(stmt, ast.ClassDef):
                walk_body(stmt.body, [*class_stack, stmt.name])
            elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.AsyncWith, ast.AsyncFor)):
                walk_body(stmt.body, class_stack)
                for handler in getattr(stmt, "handlers", []) or []:
                    walk_body(handler.body, class_stack)
                walk_body(getattr(stmt, "orelse", []) or [], class_stack)
                walk_body(getattr(stmt, "finalbody", []) or [], class_stack)
            elif isinstance(stmt, ast.Try):
                walk_body(stmt.body, class_stack)
                for handler in stmt.handlers:
                    walk_body(handler.body, class_stack)
                walk_body(stmt.orelse, class_stack)
                walk_body(stmt.finalbody, class_stack)

    walk_body(tree.body, [])
    return violations


def _under_agents_tools(path: Path) -> bool:
    """True if path is a direct file under engines/.../agents/tools/."""
    if path.parent.name != "tools":
        return False
    parts = path.parts
    try:
        ai = parts.index("agents")
    except ValueError:
        return False
    return ai + 1 < len(parts) and parts[ai + 1] == "tools"


def check_tool_naming(path: Path) -> list[Violation]:
    if not _under_agents_tools(path):
        return []
    name = path.name
    if name == "__init__.py":
        return []
    if not (name.startswith("tool_") and name.endswith(".py")):
        return [
            Violation(
                RULE_TOOL_NAME,
                _rel(path),
                1,
                f"agents tool module must be named tool_*.py (got {name})",
            )
        ]
    return []


def check_tool_doc_order(path: Path, tree: ast.Module) -> list[Violation]:
    """For engines/agents/tools/tool_*.py: Raises after Returns; Raises not before Args."""
    if not _under_agents_tools(path):
        return []
    if path.name == "__init__.py" or not path.name.startswith("tool_"):
        return []

    rel = _rel(path)
    violations: list[Violation] = []

    def check_doc(node: ast.AST, qname: str) -> None:
        doc = ast.get_docstring(node, clean=False)
        if not doc:
            return
        doc_lineno = getattr(node, "lineno", 1)
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr):
            doc_lineno = body[0].lineno

        positions: dict[str, int] = {}
        for i, line in enumerate(doc.splitlines()):
            m = SECTION_RE.match(line.strip())
            if m and m.group(1) not in positions:
                positions[m.group(1)] = i

        if "Raises" not in positions:
            return

        raises_i = positions["Raises"]
        abs_line = doc_lineno + raises_i

        if "Args" in positions and raises_i < positions["Args"]:
            violations.append(
                Violation(
                    RULE_TOOL_ORDER,
                    rel,
                    abs_line,
                    f"{qname}: Raises: must not appear before Args: "
                    "(.agents/rules/engines-code-style.md §6 — summary -> Args -> Raises)",
                )
            )
        if "Returns" in positions and raises_i < positions["Returns"]:
            violations.append(
                Violation(
                    RULE_TOOL_ORDER,
                    rel,
                    abs_line,
                    f"{qname}: Raises: must appear after Returns: when Returns: exists",
                )
            )

    def walk(body: list[ast.stmt], stack: list[str]) -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                check_doc(stmt, _qualname(stack, stmt.name))
                walk(stmt.body, [*stack, stmt.name])
            elif isinstance(stmt, ast.ClassDef):
                check_doc(stmt, _qualname(stack, stmt.name))
                walk(stmt.body, [*stack, stmt.name])
            elif isinstance(stmt, ast.Try):
                walk(stmt.body, stack)
                for h in stmt.handlers:
                    walk(h.body, stack)
                walk(stmt.orelse, stack)
                walk(stmt.finalbody, stack)
            elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.AsyncWith, ast.AsyncFor)):
                walk(stmt.body, stack)
                walk(getattr(stmt, "orelse", []) or [], stack)

    walk(tree.body, [])
    return violations





def check_no_django_apps_import(path: Path, tree: ast.Module) -> list[Violation]:
    """Flag module-level django/apps imports in engines/** (agent-harness).

    Function-body optional probes (e.g. ``from django.apps import apps`` inside
    ``_django_ready``) are allowed; top-level / module ``try`` imports are not.
    """
    rel = _rel(path)
    violations: list[Violation] = []

    def _bad_module(mod: str) -> bool:
        return (
            mod == "apps"
            or mod.startswith("apps.")
            or mod == "django"
            or mod.startswith("django.")
            or mod == "backend.apps"
            or mod.startswith("backend.apps.")
        )

    def _check_import(node: ast.AST) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if _bad_module(name):
                    violations.append(
                        Violation(
                            RULE_NO_DJANGO,
                            rel,
                            getattr(node, "lineno", 1),
                            f"engines must not import {name!r} at module level "
                            f"(see openspec/specs/agent-harness)",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if _bad_module(mod):
                violations.append(
                    Violation(
                        RULE_NO_DJANGO,
                        rel,
                        getattr(node, "lineno", 1),
                        f"engines must not import from {mod!r} at module level "
                        f"(see openspec/specs/agent-harness)",
                    )
                )
            if mod == "backend" and any(a.name == "apps" for a in node.names):
                violations.append(
                    Violation(
                        RULE_NO_DJANGO,
                        rel,
                        getattr(node, "lineno", 1),
                        "engines must not import backend.apps at module level "
                        "(see openspec/specs/agent-harness)",
                    )
                )

    def _walk_module_level(stmt: ast.stmt) -> None:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            _check_import(stmt)
        elif isinstance(stmt, (ast.Try,)):
            for block in (*stmt.body, *stmt.orelse, *stmt.finalbody):
                _walk_module_level(block)
            for handler in stmt.handlers:
                for block in handler.body:
                    _walk_module_level(block)
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            for block in stmt.body:
                _walk_module_level(block)
        elif isinstance(stmt, (ast.If,)):
            for block in (*stmt.body, *stmt.orelse):
                _walk_module_level(block)

    for stmt in tree.body:
        _walk_module_level(stmt)
    return violations


def scan_file(path: Path) -> list[Violation]:
    rel = _rel(path)
    violations: list[Violation] = []
    violations.extend(check_tool_naming(path))

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [
            Violation("io-error", rel, 1, f"cannot read file: {exc}"),
        ]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [
            Violation(
                "syntax-error",
                rel,
                exc.lineno or 1,
                f"syntax error: {exc.msg}",
            )
        ]

    if not isinstance(tree, ast.Module):
        return violations

    violations.extend(check_module_docstring(path, tree))
    violations.extend(check_raises_docs(path, tree, source))
    violations.extend(check_tool_doc_order(path, tree))
    violations.extend(check_no_django_apps_import(path, tree))
    return violations


def format_text(files_scanned: int, violations: list[Violation]) -> str:
    lines: list[str] = []
    by_rule = Counter(v.rule for v in violations)
    for v in violations:
        lines.append(f"{v.path}:{v.lineno}: [{v.rule}] {v.message}")
    lines.append("")
    lines.append(
        f"scanned {files_scanned} files; {len(violations)} violation(s): "
        + (", ".join(f"{k}={by_rule[k]}" for k in sorted(by_rule)) if by_rule else "none")
    )
    return "\n".join(lines)


def format_json(files_scanned: int, violations: list[Violation]) -> str:
    by_rule = Counter(v.rule for v in violations)
    payload = {
        "files_scanned": files_scanned,
        "violation_count": len(violations),
        "by_rule": dict(sorted(by_rule.items())),
        "violations": [asdict(v) for v in violations],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Check engines/ against .agents/rules/engines-code-style.md (mechanizable subset; see engines/AGENTS.md for process)")
    parser.add_argument(
        "--path",
        default=str(DEFAULT_ROOT),
        help="只扫该目录或文件；相对路径相对仓库根。默认 engines/ 全量",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        dest="fmt",
        help="text=可读汇总（默认）；json=机器可读，便于脚本解析",
    )
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.is_absolute():
        target = (ROOT / target).resolve()

    files = iter_py_files(target)
    all_violations: list[Violation] = []
    for path in files:
        all_violations.extend(scan_file(path))

    # Stable order
    all_violations.sort(key=lambda v: (v.path, v.lineno, v.rule, v.message))

    if args.fmt == "json":
        print(format_json(len(files), all_violations))
    else:
        print(format_text(len(files), all_violations))

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
