"""engines 风格检查：用 AST 扫描 module-docstring 存在性 / tool 命名 / engines 禁 django·apps import。
风格正文：.agents/rules/engines-code-style.md（§§2、3、6 等可机械化子集）。
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
RULE_TOOL_NAME = "tool-naming"
RULE_NO_DJANGO = "no-django-apps-import"


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
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(getattr(body[0], "value", None), ast.Constant)
    ):
        if isinstance(body[0].value.value, str):
            return body[1:]
    return body


def check_module_docstring(path: Path, tree: ast.Module) -> list[Violation]:
    rel = _rel(path)
    if path.name == "__init__.py":
        stmts = _body_without_doc(tree)
        has_defs = any(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in tree.body
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

    parser = argparse.ArgumentParser(
        description="Check engines/ against .agents/rules/engines-code-style.md (mechanizable subset; see engines/AGENTS.md for process)"
    )
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
