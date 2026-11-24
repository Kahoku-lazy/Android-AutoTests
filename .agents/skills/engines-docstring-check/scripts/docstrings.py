"""Python 模块 docstring 读取与合规检查（单一脚本，两个子命令）。

2026-11-24 起规范范围是全仓在册 Python 代码（正文 `.agents/rules/python-docstring-style.md`），
不再是「仅 engines」；技能目录名沿用历史。

本模块的业务功能如下：
1. check: 按规范校验模块头 4 字段 + 引擎工具函数摘要/Args。
2. read: 抽取模块字段 + 类/函数签名与 docstring，用于「读代码前先看注释了解详情」。

python -m 调试路径: scripts.docstrings
（cwd 必须是本技能目录 `.agents/skills/engines-docstring-check`）

Usage（先 cd 到本技能目录）:

    python -m scripts.docstrings check              # 默认：只查 git 改动文件，只报本次新引入
    python -m scripts.docstrings check --include-existing   # 连 HEAD 已有存量一起报
    python -m scripts.docstrings check --all        # 全仓在册文件全量审计（会列出存量欠账）
    python -m scripts.docstrings check --all --summary      # 只出按规则聚合的计数（门禁用）
    python -m scripts.docstrings check --path utils
    python -m scripts.docstrings check --format json

    python -m scripts.docstrings read --path utils/gen_arch_stats.py
    python -m scripts.docstrings read --changed --format md
    python -m scripts.docstrings read --path engines --depth module

Exit codes:
    check: 0 无 error（--strict 时 warn 也算失败）；1 有 error
    read : 0 正常；1 目标不存在
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# 仓库定位与文件遍历
# --------------------------------------------------------------------------


def _find_repo_root(start: Path) -> Path:
    """Walk parents from *start* until a dir with engines/AGENTS.md is found.

    Args:
        start: 起始路径（通常是本脚本所在目录）。

    Returns:
        仓库根目录。

    Raises:
        SystemExit: 找不到仓库根（缺 engines/AGENTS.md）。
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
        "Cannot locate repo root from "
        f"{start}: expected a parent containing engines/AGENTS.md "
        "(preferably also .agents/skills/)."
    )


ROOT = _find_repo_root(Path(__file__).resolve())
DEFAULT_ROOT = ROOT

SKIP_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".venv",
        "venv",
        ".dvenv",
        "node_modules",
        ".git",
        ".pytest-tmp",
        ".testtmp",
        ".pytest_cache",
        ".ruff_cache",
        ".import_linter_cache",
    }
)
# 供应商技能树已随 engines/agents 退役（变更 retire-engines-agents）。

# --------------------------------------------------------------------------
# 注释规范范围（唯一判定入口；与 .agents/rules/python-docstring-style.md §1 逐行对应）
# --------------------------------------------------------------------------

# 纳入是**白名单**口径：新增顶层目录必须同时登记到这里与规则文档，否则不检查。
IN_SCOPE_ROOTS = ("engines", "backend", "tests", "utils")
# 仓库根的独立脚本按文件名白名单（manage.py 属 Django 脚手架，见排除表）。
IN_SCOPE_ROOT_FILES = frozenset({"run.py", "run_daphne.py"})

# Django 固定脚手架：文件名 + 模式（api.py / api_rows.py 只差一个词，必须确定性判定）。
EXCLUDED_FILE_NAMES = frozenset(
    {
        "models.py",
        "views.py",
        "serializers.py",
        "admin.py",
        "urls.py",
        "apps.py",
        "asgi.py",
        "wsgi.py",
        "settings.py",
        "api.py",
        "manage.py",
    }
)
EXCLUDED_FILE_PATTERNS = (
    re.compile(r"^views_.*\.py$"),
    re.compile(r"^.*_views\.py$"),
    re.compile(r"^api_.*\.py$"),
    re.compile(r"^serializers_.*\.py$"),
)
EXCLUDED_DIR_SEGMENTS = frozenset({"migrations"})


def exclusion_reason(rel: str) -> str:
    """Return why *rel* is out of the docstring rule scope ("" when in scope).

    Django 固定脚手架的判定只在 `backend/` 下生效：`engines/**/models.py` 是引擎自己的
    领域模型，不是 Django ORM 骨架，必须照常检查。

    Args:
        rel: 仓库相对路径（posix）。

    Returns:
        排除原因；在册时返回空串。
    """
    parts = rel.split("/")
    name = parts[-1]
    if len(parts) == 1:
        if name in EXCLUDED_FILE_NAMES:
            return "Django 固定脚手架文件"
        return "" if name in IN_SCOPE_ROOT_FILES else "非项目自写脚本（根目录白名单外）"
    if parts[0] not in IN_SCOPE_ROOTS:
        return f"顶层目录 {parts[0]}/ 不在注释规范范围"
    if parts[0] != "backend":
        return ""
    if EXCLUDED_DIR_SEGMENTS & set(parts[:-1]):
        return "Django migrations"
    if name in EXCLUDED_FILE_NAMES or any(p.match(name) for p in EXCLUDED_FILE_PATTERNS):
        return "Django 固定脚手架文件"
    return ""


def in_scope(rel: str) -> bool:
    """True when *rel* must carry the 4-field module header."""
    return not exclusion_reason(rel)


def should_skip(path: Path) -> bool:
    """True for cache dirs and vendored skill trees that must never be checked.

    Args:
        path: 待判断路径。

    Returns:
        命中跳过规则时为 True。
    """
    parts = set(path.parts)
    return bool(SKIP_DIR_NAMES & parts)


def iter_py_files(base: Path) -> list[Path]:
    """Return *.py files under base, skipping caches and vendored skill trees.

    Args:
        base: 文件或目录。

    Returns:
        Python 文件列表（已排序）；base 不存在时为空。
    """
    if not base.exists():
        return []
    if base.is_file():
        return [base] if base.suffix == ".py" and not should_skip(base) else []
    return [path for path in sorted(base.rglob("*.py")) if not should_skip(path)]


def rel_posix(path: Path) -> str:
    """Return path relative to repo root in posix form (best effort)."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


# --------------------------------------------------------------------------
# git 改动范围
# --------------------------------------------------------------------------


def _git(*args: str) -> str:
    """Run a git command in the repo root and return stdout.

    Args:
        *args: git 子命令与参数。

    Returns:
        标准输出文本。

    Raises:
        SystemExit: git 不可用或命令失败。
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:  # git 未安装
        raise SystemExit(f"git 不可用：{exc}") from exc
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc.stdout


def changed_python_paths(base_ref: str = "HEAD") -> list[str]:
    """Collect changed python paths vs *base_ref* (tracked changes + untracked files).

    Args:
        base_ref: 比较基准（默认 HEAD，含已暂存与工作区改动）。

    Returns:
        仓库相对路径列表（posix），已过滤缓存与供应商目录。
    """
    diff = _git("diff", "--name-only", "--no-color", base_ref)
    untracked = _git("ls-files", "--others", "--exclude-standard")
    paths = {line.strip() for line in (diff + "\n" + untracked).splitlines() if line.strip()}
    return sorted(p for p in paths if p.endswith(".py") and not should_skip(Path(p)))


def baseline_keys(rel: str, base_ref: str = "HEAD") -> set[tuple[str, str, str]]:
    """Return violation keys for the file's *base_ref* version (HEAD baseline).

    Args:
        rel: 仓库相对路径。
        base_ref: 比较基准（默认 HEAD）。

    Returns:
        {(rule, symbol, message)}；文件在基准里不存在时为空集。
    """
    try:
        source = _git("show", f"{base_ref}:{rel}")
    except SystemExit:
        return set()  # 新文件：基准为空
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError:
        return set()
    raw = ast.get_docstring(tree, clean=False) or ""
    violations: list[Violation] = []
    violations.extend(_module_rules(rel, tree, raw))
    _walk_defs(tree.body, rel, violations, _tool_function_names(tree))
    return {violation_key(v) for v in violations}


def violation_key(violation: Violation) -> tuple[str, str, str]:
    """Stable identity of a violation, used to subtract the HEAD baseline."""
    return (violation.rule, violation.symbol, violation.message)


# 「有 docstring 才成立」的规则：若该符号在 HEAD 里已经有了 docstring 问题，
# 说明它本来就没达标，这次补注释又引出 Args 缺失，不算你引入的新问题。
PRESENCE_RULES = frozenset({"module-docstring", "tool-docstring"})


# --------------------------------------------------------------------------
# docstring 解析工具
# --------------------------------------------------------------------------

SECTION_RE = re.compile(
    r"^(Args|Arguments|Returns|Yields|Raises|Attributes|Note|Notes|Example|Examples):\s*$"
)
ARG_ENTRY_RE = re.compile(r"^(\*{0,2}[A-Za-z_]\w*)\s*(?:\(([^)]*)\))?\s*:\s*(.*)$")
RAISES_ENTRY_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*:")
NUMBERED_RE = re.compile(r"(?m)^\s*(\d+)[.、]")

SECTION_ORDER = ("Args", "Returns", "Raises")


@dataclass(frozen=True)
class Violation:
    """一条 docstring 违规。"""

    rule: str
    severity: str
    path: str
    lineno: int
    symbol: str
    message: str


# 规则表：id -> (severity, 说明)。severity 决定退出码与默认可见性。
# 2026-11-24 起：模块头 4 字段；普通函数/类不要求注释；只有 FunctionTool 注册的工具函数要摘要 + Args。
RULES: dict[str, tuple[str, str]] = {
    "module-docstring": ("error", "缺少模块 docstring（§2.1）"),
    "module-fields": (
        "error",
        "模块头 4 字段不齐 / 时间或调试入口格式错（§2）",
    ),
    "module-summary": ("error", "模块功能字段写坏（编号开头、命令开头或为空）（§2）"),
    "module-numbering": ("error", "测试 段编号不连续（§2 模板：➡️…🏁 内编号列表）"),
    "tool-docstring": ("error", "工具函数缺少 docstring（模型侧读不到工具说明）（§2.3 / §6.1）"),
    "tool-summary": ("error", "工具函数 docstring 缺少首行一句话摘要（§6.1）"),
    "tool-args": ("error", "工具函数有参数但缺 Args: 段或漏列参数名（§6.1）"),
    "tool-args-empty": ("warn", "Args: 条目缺说明文字（§2.3）"),
}


def _severity(rule: str) -> str:
    return RULES.get(rule, ("error", ""))[0]


def split_sections(doc: str) -> dict[str, list[str]]:
    """Split a docstring into section bodies keyed by section title.

    Args:
        doc: docstring 原文。

    Returns:
        {段名: 该段的行列表}，按首次出现记录。
    """
    out: dict[str, list[str]] = {}
    current: str | None = None
    buf: list[str] = []
    for line in doc.splitlines():
        match = SECTION_RE.match(line.strip())
        if match:
            if current is not None:
                out.setdefault(current, buf)
            current = match.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out.setdefault(current, buf)
    return out


def section_offsets(doc: str) -> dict[str, int]:
    """Return {section title: index of its line in the docstring}."""
    positions: dict[str, int] = {}
    for index, line in enumerate(doc.splitlines()):
        match = SECTION_RE.match(line.strip())
        if match and match.group(1) not in positions:
            positions[match.group(1)] = index
    return positions


def args_entries(body: list[str]) -> list[tuple[str, str]]:
    """Parse Args: body into [(参数名, 说明)] entries."""
    out: list[tuple[str, str]] = []
    for line in body:
        match = ARG_ENTRY_RE.match(line.strip())
        if match:
            out.append((match.group(1).lstrip("*"), match.group(3).strip()))
    return out


def param_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Return declared parameter names, excluding self/cls."""
    args = fn.args
    names = [a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)]
    if args.vararg:
        names.append(args.vararg.arg)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return [n for n in names if n not in {"self", "cls"}]


def annotation_text(node: ast.AST | None) -> str:
    """Render an annotation node as source text (short, defensive)."""
    if node is None:
        return ""
    try:
        text = ast.unparse(node)
    except Exception:  # 老版本 / 异常节点
        return ""
    return text if len(text) <= 80 else text[:77] + "..."


def signature_text(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render a compact signature: name(params) -> ret."""
    args = fn.args
    positional = [*args.posonlyargs, *args.args]
    defaults: list[ast.AST | None] = [None] * (len(positional) - len(args.defaults))
    defaults.extend(args.defaults)
    parts: list[str] = []
    for arg, default in zip(positional, defaults):
        text = arg.arg
        ann = annotation_text(arg.annotation)
        if ann:
            text += f": {ann}"
        if default is not None:
            text += "=..."
        parts.append(text)
    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        parts.append("*")
    for arg in args.kwonlyargs:
        text = arg.arg
        ann = annotation_text(arg.annotation)
        if ann:
            text += f": {ann}"
        parts.append(text)
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")
    ret = annotation_text(fn.returns)
    prefix = "async " if isinstance(fn, ast.AsyncFunctionDef) else ""
    return f"{prefix}{fn.name}({', '.join(parts)})" + (f" -> {ret}" if ret else "")


def raise_types(fn: ast.AST) -> list[str]:
    """Return exception type names explicitly raised inside fn (bare raise ignored)."""
    found: list[str] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        if isinstance(exc, ast.Name):
            name = exc.id
        elif isinstance(exc, ast.Attribute):
            name = exc.attr
        else:
            continue
        if name not in found:
            found.append(name)
    return found


def has_return_value(fn: ast.AST) -> bool:
    """True when fn contains a `return <expr>` that is not `return None`."""
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        value = node.value
        if isinstance(value, ast.Constant) and value.value is None:
            continue
        return True
    return False


def is_generator(fn: ast.AST) -> bool:
    """True when fn contains yield / yield from."""
    return any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(fn))


def first_summary(doc: str) -> str:
    """Return the first non-empty line of a docstring."""
    for line in doc.strip().splitlines():
        text = line.strip()
        if text:
            return text
    return ""


def is_public(name: str) -> bool:
    """Public = 不以 _ 开头，或 __init__（构造入口）。"""
    return not name.startswith("_") or name == "__init__"


# --------------------------------------------------------------------------
# 模块级 docstring 字段（复用 utils.module_docstring）
# --------------------------------------------------------------------------


def load_module_fields_tools() -> tuple[Any, Any] | None:
    """Import utils.module_docstring helpers; None when unavailable.

    Returns:
        (parse_module_docstring, validate_module_docstring) 或 None。
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        from utils.module_docstring import (  # noqa: PLC0415 - 延迟导入
            parse_module_docstring,
            validate_module_docstring,
        )
    except Exception:  # 仓库结构变化时不阻塞其他规则
        return None
    return parse_module_docstring, validate_module_docstring


MODULE_TOOLS = load_module_fields_tools()


def module_fields(raw: str) -> dict[str, str]:
    """Parse module docstring fields into a dict (empty dict when tool missing)."""
    if MODULE_TOOLS is None:
        return {}
    parse_fn = MODULE_TOOLS[0]
    return parse_fn(raw)


def _is_engines_path(rel: str) -> bool:
    """True when the file lives under engines/ (仅用于 read 提示文案)."""
    return rel == "engines" or rel.startswith("engines/")


# --------------------------------------------------------------------------
# check：单文件规则
# --------------------------------------------------------------------------


def _is_empty_shell(tree: ast.Module, rel: str) -> bool:
    """True for a package marker：`__init__.py` 无 def/class 且只有少量语句（含仅一行 docstring）。"""
    if Path(rel).name != "__init__.py":
        return False
    has_defs = any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in tree.body
    )
    stmts = [
        s
        for s in tree.body
        if not (isinstance(s, ast.Expr) and isinstance(getattr(s, "value", None), ast.Constant))
    ]
    return not has_defs and len(stmts) <= 2


def _module_rules(rel: str, tree: ast.Module, raw: str) -> list[Violation]:
    """Module-level docstring rules."""
    out: list[Violation] = []
    # 空壳 __init__.py：无 defs 且只有少量语句时豁免（写不写模块头都行，写了不校验）
    if _is_empty_shell(tree, rel):
        return out
    if not raw.strip():
        return [
            Violation(
                "module-docstring",
                _severity("module-docstring"),
                rel,
                1,
                "<module>",
                "缺少模块 docstring",
            )
        ]

    if not in_scope(rel) or MODULE_TOOLS is None:
        return out

    fields = module_fields(raw)
    validate_fn = MODULE_TOOLS[1]
    for issue in validate_fn(fields, text=raw, rel_path=rel):
        out.append(
            Violation("module-fields", _severity("module-fields"), rel, 1, "<module>", issue)
        )

    summary = (fields.get("模块功能") or "").strip()
    if not summary:
        out.append(
            Violation(
                "module-summary", _severity("module-summary"), rel, 1, "<module>", "模块功能 为空"
            )
        )
    elif re.match(r"^\d+[.、]", summary) or re.match(r"^(python|py)\s+-m\b", summary, re.I):
        out.append(
            Violation(
                "module-summary",
                _severity("module-summary"),
                rel,
                1,
                "<module>",
                f"模块功能 应是一句话职责，不要写编号或调试命令：{summary[:40]}",
            )
        )

    for name in ("测试",):
        numbers = [int(m.group(1)) for m in NUMBERED_RE.finditer(fields.get(name) or "")]
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            out.append(
                Violation(
                    "module-numbering",
                    _severity("module-numbering"),
                    rel,
                    1,
                    f"<module:{name}>",
                    f"{name} 编号不连续：{numbers[:8]}",
                )
            )
    return out


def _tool_function_names(tree: ast.Module) -> set[str]:
    """Return function names registered via FunctionTool(...).

    Args:
        tree: 模块 AST。

    Returns:
        被注册为工具的函数名集合（模型可见的工具说明来源）。
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func
        if isinstance(func, ast.Name):
            callee = func.id
        elif isinstance(func, ast.Attribute):
            callee = func.attr
        else:
            continue
        if callee != "FunctionTool":
            continue
        first = node.args[0]
        if isinstance(first, ast.Name):
            names.add(first.id)
        elif isinstance(first, ast.Attribute):
            names.add(first.attr)
    return names


def _function_rules(
    rel: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    tool_names: set[str] | frozenset[str] = frozenset(),
) -> list[Violation]:
    """Tool-function docstring rules: presence, summary, Args coverage.

    Args:
        rel: 仓库相对路径。
        node: 函数/方法节点。
        tool_names: 被 FunctionTool 注册的函数名；不在其中的函数不查注释。

    Returns:
        违规列表（普通函数恒为空）。
    """
    out: list[Violation] = []
    name = node.name
    if name not in tool_names:
        return out

    doc = ast.get_docstring(node, clean=False) or ""
    if not doc.strip():
        out.append(
            Violation(
                "tool-docstring",
                _severity("tool-docstring"),
                rel,
                node.lineno,
                name,
                f"工具函数 {name} 缺少 docstring（模型侧读不到工具说明）",
            )
        )
        return out

    summary = first_summary(doc)
    if not summary or SECTION_RE.match(summary):
        out.append(
            Violation(
                "tool-summary",
                _severity("tool-summary"),
                rel,
                node.lineno,
                name,
                f"{name}: 工具 docstring 应以一句话摘要开头",
            )
        )

    sections = split_sections(doc)
    params = param_names(node)

    if params:
        if "Args" not in sections:
            out.append(
                Violation(
                    "tool-args",
                    _severity("tool-args"),
                    rel,
                    node.lineno,
                    name,
                    f"{name}: 有参数 {params} 但缺 Args: 段",
                )
            )
        else:
            entries = args_entries(sections["Args"])
            documented = [entry[0] for entry in entries]
            missing = [p for p in params if p not in documented]
            if missing:
                out.append(
                    Violation(
                        "tool-args",
                        _severity("tool-args"),
                        rel,
                        node.lineno,
                        name,
                        f"{name}: Args: 漏列参数 {missing}",
                    )
                )
            empty = [entry[0] for entry in entries if not entry[1]]
            if empty:
                out.append(
                    Violation(
                        "tool-args-empty",
                        _severity("tool-args-empty"),
                        rel,
                        node.lineno,
                        name,
                        f"{name}: Args: 条目缺说明 {empty}",
                    )
                )

    return out


def _walk_defs(
    body: list[ast.stmt],
    rel: str,
    out: list[Violation],
    tool_names: set[str] | frozenset[str] = frozenset(),
) -> None:
    """Walk module/class bodies (not function bodies) and collect violations."""
    for node in body:
        if isinstance(node, ast.ClassDef):
            _walk_defs(node.body, rel, out, tool_names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.extend(_function_rules(rel, node, tool_names))
        elif isinstance(node, (ast.If, ast.Try, ast.For, ast.While, ast.With, ast.AsyncWith)):
            _walk_defs(node.body, rel, out, tool_names)
            _walk_defs(getattr(node, "orelse", []) or [], rel, out, tool_names)
            _walk_defs(getattr(node, "finalbody", []) or [], rel, out, tool_names)
            for handler in getattr(node, "handlers", []) or []:
                _walk_defs(handler.body, rel, out, tool_names)


def check_file(path: Path) -> list[Violation]:
    """Run all docstring rules on one python file.

    Args:
        path: Python 文件路径。

    Returns:
        违规列表（含解析失败时的一条 syntax-error）。
    """
    rel = rel_posix(path)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Violation("io-error", "error", rel, 1, "<file>", f"无法读取文件：{exc}")]
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [
            Violation(
                "syntax-error", "error", rel, exc.lineno or 1, "<file>", f"语法错误：{exc.msg}"
            )
        ]

    raw = ast.get_docstring(tree, clean=False) or ""
    out: list[Violation] = []
    out.extend(_module_rules(rel, tree, raw))
    _walk_defs(tree.body, rel, out, _tool_function_names(tree))
    return out


# --------------------------------------------------------------------------
# read：模块/类/函数摘要
# --------------------------------------------------------------------------


def _class_digest(node: ast.ClassDef) -> dict[str, Any]:
    """Build a compact digest for one class."""
    doc = ast.get_docstring(node, clean=False) or ""
    sections = split_sections(doc)
    fields = [
        s.target.id
        for s in node.body
        if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
    ]
    documented = {name for name, _ in args_entries(sections.get("Attributes", []))}
    methods = [
        s.name
        for s in node.body
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(s.name)
    ]
    return {
        "name": node.name,
        "lineno": node.lineno,
        "summary": first_summary(doc),
        "attributes": fields,
        "attributes_documented": [f for f in fields if f in documented],
        "methods": methods,
    }


def _function_digest(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    """Build a compact digest for one function/method (no body, no full doc)."""
    doc = ast.get_docstring(node, clean=False) or ""
    sections = split_sections(doc)
    return {
        "name": node.name,
        "lineno": node.lineno,
        "signature": signature_text(node),
        "summary": first_summary(doc),
        "doc": doc,
        "sections": [s for s in SECTION_ORDER if s in sections],
        "args": [name for name, _ in args_entries(sections.get("Args", []))],
        "raises": raise_types(node),
        "has_doc": bool(doc.strip()),
    }


def digest_file(path: Path) -> dict[str, Any]:
    """Build a read-mode digest for one python file.

    Args:
        path: Python 文件路径。

    Returns:
        {"file","fields","raw_doc","classes","functions","undocumented"}。
    """
    rel = rel_posix(path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    raw = ast.get_docstring(tree, clean=False) or ""

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    undocumented: list[dict[str, Any]] = []

    def visit(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                if is_public(node.name):
                    classes.append(_class_digest(node))
                    if not (ast.get_docstring(node) or "").strip():
                        undocumented.append(
                            {"kind": "class", "name": node.name, "lineno": node.lineno}
                        )
                visit(node.body)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if is_public(node.name):
                    functions.append(_function_digest(node))
                    if not (ast.get_docstring(node) or "").strip():
                        undocumented.append(
                            {"kind": "def", "name": node.name, "lineno": node.lineno}
                        )
            elif isinstance(node, (ast.If, ast.Try, ast.For, ast.While, ast.With, ast.AsyncWith)):
                visit(node.body)
                visit(getattr(node, "orelse", []) or [])
                visit(getattr(node, "finalbody", []) or [])
                for handler in getattr(node, "handlers", []) or []:
                    visit(handler.body)

    visit(tree.body)
    return {
        "file": rel,
        "fields": module_fields(raw),
        "raw_doc": raw,
        "classes": classes,
        "functions": functions,
        "undocumented": undocumented,
    }


def render_text(digest: dict[str, Any], *, full: bool = False, depth: str = "full") -> str:
    """Render one digest as readable text."""
    fields = digest["fields"]
    lines: list[str] = []
    header = [digest["file"]]
    if fields.get("时间"):
        header.append(f"时间 {fields['时间']}")
    lines.append("=" * 78)
    lines.append(" ".join(header))
    lines.append("-" * 78)

    if fields:
        lines.append(f"功能: {fields.get('模块功能') or '-'}")
        lines.append(f"入口: {fields.get('Python 调试') or '-'}")
        for label, key in (("简介", "简介说明"), ("依赖", "关联模块"), ("测试", "测试")):
            body = (fields.get(key) or "").strip()
            if not body:
                continue
            entries = [l.strip() for l in body.splitlines() if l.strip()]
            lines.append(f"{label} ({len(entries)} 条)")
            lines.extend(f"  {entry}" for entry in entries)
    else:
        summary = first_summary(digest["raw_doc"]) if digest["raw_doc"] else "-"
        lines.append(f"功能: {summary}")
        lines.append("（该文件没有 4 字段模板 docstring，只有普通说明）")

    if depth == "module":
        return "\n".join(lines)

    if digest["classes"]:
        lines.append("")
        lines.append(f"类 ({len(digest['classes'])})")
        for cls in digest["classes"]:
            lines.append(f"  L{cls['lineno']:<5} class {cls['name']}")
            if cls["summary"]:
                lines.append(f"         {cls['summary']}")
            if cls["attributes"]:
                missing = [f for f in cls["attributes"] if f not in cls["attributes_documented"]]
                note = f"（未写 Attributes: {missing}）" if missing else ""
                lines.append(f"         字段: {', '.join(cls['attributes'])}{note}")
            if cls["methods"]:
                lines.append(f"         方法: {', '.join(cls['methods'])}")

    if digest["functions"]:
        lines.append("")
        lines.append(f"函数 ({len(digest['functions'])})")
        for fn in digest["functions"]:
            lines.append(f"  L{fn['lineno']:<5} {fn['signature']}")
            if fn["summary"]:
                lines.append(f"         {fn['summary']}")
            if full and fn["doc"]:
                for line in fn["doc"].strip().splitlines():
                    lines.append(f"         | {line}")
            elif fn["sections"]:
                lines.append(f"         段: {' → '.join(fn['sections'])}")
            if fn["raises"]:
                lines.append(f"         抛出: {', '.join(fn['raises'])}")
    return "\n".join(lines)


def render_md(digest: dict[str, Any]) -> str:
    """Render one digest as markdown."""
    fields = digest["fields"]
    out: list[str] = [f"## `{digest['file']}`"]
    if fields:
        out.append("")
        out.append(f"- **模块功能**：{fields.get('模块功能') or '-'}")
        out.append(f"- **时间**：{fields.get('时间') or '-'}")
        out.append(f"- **调试入口**：`{fields.get('Python 调试') or '-'}`")
        for label, key in (("简介说明", "简介说明"), ("关联模块", "关联模块"), ("测试", "测试")):
            body = (fields.get(key) or "").strip()
            if body:
                out.append(f"- **{label}**：")
                out.extend(f"  {l.strip()}" for l in body.splitlines() if l.strip())
    if digest["classes"]:
        out.append("")
        out.append("### 类")
        for cls in digest["classes"]:
            out.append(f"- `L{cls['lineno']} class {cls['name']}` — {cls['summary']}")
    if digest["functions"]:
        out.append("")
        out.append("### 函数")
        for fn in digest["functions"]:
            extra = f"（段：{'/'.join(fn['sections'])}）" if fn["sections"] else ""
            out.append(f"- `L{fn['lineno']} {fn['signature']}` — {fn['summary']}{extra}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _resolve_targets(args: argparse.Namespace) -> tuple[list[Path], dict[str, Any]]:
    """Resolve CLI scope into a file list plus a description of the scope.

    Args:
        args: 解析后的命令行参数。

    Returns:
        (文件列表, 范围说明 dict)。

    Raises:
        SystemExit: --path 指向不存在的路径。
    """
    if args.path:
        base = Path(args.path)
        if not base.is_absolute():
            base = (ROOT / base).resolve()
        if not base.exists():
            raise SystemExit(f"--path 不存在：{base}")
        scope = {"mode": "path", "path": rel_posix(base)}
        return iter_py_files(base), scope

    if args.all:
        scope = {"mode": "all", "path": "(repo-wide)"}
        return iter_py_files(DEFAULT_ROOT), scope

    changes = changed_python_paths(args.base)
    # 规范范围见 .agents/rules/python-docstring-style.md §1（白名单 + Django 排除表）。
    # 已删除的文件不参与检查（git diff 仍会列出它们）。
    paths = [p for p in changes if in_scope(p) and (ROOT / p).is_file()]
    scope = {
        "mode": "changed",
        "base": args.base,
        "changed_files": len(changes),
        "in_scope": len(paths),
        "deleted": len(changes) - sum(1 for p in changes if (ROOT / p).is_file()),
        "excluded": sum(1 for p in changes if not in_scope(p)),
    }
    return [ROOT / p for p in paths], scope


def cmd_check(args: argparse.Namespace) -> int:
    """Run the check subcommand.

    Args:
        args: 解析后的命令行参数。

    Returns:
        进程退出码（0 通过，1 有 error）。
    """
    files, scope = _resolve_targets(args)
    filtered: list[Violation] = []
    hidden = 0
    baseline_mode = scope.get("mode") == "changed" and not args.include_existing
    # 全量 / 指定路径：warn 一并展示；改动模式：默认只报 error，避免存量噪声
    show_warn = args.all or args.strict or scope.get("mode") == "path"

    # 排除清单（Django 固定脚手架、非产品代码）不是「暂时没写」，是「按规范不写」：
    # 直接跳过并计数，不产生 violation（否则退出码会被无意义地置 1）。
    scanned: list[Path] = []
    skipped: list[tuple[str, str]] = []
    for path in files:
        rel = rel_posix(path)
        reason = exclusion_reason(rel)
        if reason:
            skipped.append((rel, reason))
            continue
        scanned.append(path)

    if not scanned:
        print(
            f"没有需要检查的 Python 文件（范围：{scope}；跳过 {len(skipped)} 个排除文件）",
            file=sys.stderr,
        )
        return 0

    for path in scanned:
        try:
            violations = check_file(path)
        except OSError as exc:
            violations = [Violation("io-error", "error", rel_posix(path), 1, "<file>", str(exc))]
        if not violations:
            continue
        # 改动模式：只报「这次改动新引入」的违规——与 HEAD 版本对比，存量不算你头上
        baseline = baseline_keys(rel_posix(path), args.base) if baseline_mode else set()
        baseline_symbols = {symbol for _, symbol, _ in baseline}
        for violation in violations:
            if violation.severity == "warn" and not show_warn:
                hidden += 1
                continue
            if violation_key(violation) in baseline:
                hidden += 1
                continue
            if violation.rule not in PRESENCE_RULES and violation.symbol in baseline_symbols:
                hidden += 1
                continue
            filtered.append(violation)

    filtered.sort(key=lambda v: (v.path, v.lineno, v.rule))
    errors = [v for v in filtered if v.severity == "error"]
    warns = [v for v in filtered if v.severity == "warn"]

    if args.summary:
        by_rule = Counter(v.rule for v in filtered)
        by_path = Counter(v.path for v in filtered)
        print(f"files_in_scope: {len(scanned)}, files_excluded: {len(skipped)}")
        for rule, count in sorted(by_rule.items()):
            print(f"  {rule:<18} {count}")
        print(f"errors: {len(errors)}, warns: {len(warns)}, files_with_issues: {len(by_path)}")
        if by_path:
            top = ", ".join(f"{path}({n})" for path, n in by_path.most_common(5))
            print(f"top: {top}")
        failed = bool(errors) or (args.strict and bool(warns))
        return 1 if failed else 0

    if args.format == "json":
        print(
            json.dumps(
                {
                    "scope": scope,
                    "files_scanned": len(scanned),
                    "files_excluded": len(skipped),
                    "error_count": len(errors),
                    "warn_count": len(warns),
                    "hidden_out_of_scope": hidden,
                    "by_rule": dict(Counter(v.rule for v in filtered)),
                    "violations": [asdict(v) for v in filtered],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for v in filtered:
            print(f"{v.path}:{v.lineno}: [{v.rule}] ({v.severity}) {v.message}")
        if filtered:
            print()
        by_rule = Counter(v.rule for v in filtered)
        detail = ", ".join(f"{k}={by_rule[k]}" for k in sorted(by_rule)) or "none"
        if scope.get("mode") == "changed":
            where = (
                f"changed vs {scope.get('base')}: "
                f"{scope.get('in_scope')}/{scope.get('changed_files')} 个改动文件"
            )
            if scope.get("deleted"):
                where += f"（跳过 {scope['deleted']} 个已删除文件）"
            if scope.get("excluded"):
                where += f"（{scope['excluded']} 个改动文件不在注释规范范围）"
        else:
            where = f"{scope.get('mode')}: {scope.get('path')}"
        print(
            f"scanned {len(scanned)} file(s) [排除 {len(skipped)} 个] [{where}]; "
            f"{len(errors)} error(s), {len(warns)} warn(s): {detail}"
        )
        if hidden:
            print(
                f"（另有 {hidden} 条未计入：HEAD 已有的存量、warn 级，或不在当前展示级别；"
                f"加 --include-existing / --all / --strict 查看）"
            )

    failed = bool(errors) or (args.strict and bool(warns))
    return 1 if failed else 0


def cmd_read(args: argparse.Namespace) -> int:
    """Run the read subcommand.

    Args:
        args: 解析后的命令行参数。

    Returns:
        进程退出码（0 正常）。
    """
    files, scope = _resolve_targets(args)
    if not files:
        print(f"没有可读取的 Python 文件（范围：{scope}）", file=sys.stderr)
        return 0

    digests: list[dict[str, Any]] = []
    for path in files:
        try:
            digests.append(digest_file(path))
        except (OSError, SyntaxError) as exc:
            print(f"跳过 {rel_posix(path)}：{exc}", file=sys.stderr)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "scope": {k: v for k, v in scope.items() if k != "ranges"},
                    "files": digests,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.format == "md":
        print("\n\n".join(render_md(d) for d in digests))
        return 0

    blocks = [render_text(d, full=args.full, depth=args.depth) for d in digests]
    print("\n".join(blocks))
    total_defs = sum(len(d["functions"]) + len(d["classes"]) for d in digests)
    total_missing = sum(len(d["undocumented"]) for d in digests)
    print()
    print(
        f"共 {len(digests)} 个模块；公开符号 {total_defs} 个，其中未写 docstring {total_missing} 个。"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser with check/read subcommands."""
    parser = argparse.ArgumentParser(
        prog="scripts.docstrings",
        description=(
            "Python 模块 docstring 读取与合规检查"
            "（规范：.agents/rules/python-docstring-style.md；engines 工具函数另见 engines-code-style.md §6）"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_scope(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--path", default="", help="目录或文件（相对仓库根；优先于 --all/--changed）"
        )
        p.add_argument(
            "--all",
            action="store_true",
            help="全量扫描全仓在册文件（白名单见规范 §1，Django 固定脚手架自动跳过）",
        )
        p.add_argument(
            "--changed",
            action="store_true",
            help="只看 git 改动文件（不给 --path/--all 时的默认行为，写上更直观）",
        )
        p.add_argument("--base", default="HEAD", help="git 比较基准（默认 HEAD）")
        p.add_argument(
            "--repo",
            action="store_true",
            help="[deprecated] 2026-11-24 起范围已是全仓，此开关无效果，保留仅为兼容旧命令",
        )

    check = sub.add_parser("check", help="校验 docstring 合规（默认只查 git 改动）")
    add_scope(check)
    check.add_argument(
        "--include-existing",
        dest="include_existing",
        action="store_true",
        help="改动模式：连 HEAD 已有的存量违规一起报（默认只报这次改动新引入的）",
    )
    check.add_argument("--strict", action="store_true", help="warn 也视为失败，并全部展示")
    check.add_argument(
        "--summary",
        action="store_true",
        help="只输出按规则聚合的计数（门禁 / 全量巡检用，不逐条打印）",
    )
    check.add_argument("--format", choices=("text", "json"), default="text")

    read = sub.add_parser("read", help="抽取 docstring/签名，用于读代码前了解详情")
    add_scope(read)
    read.add_argument(
        "--depth",
        choices=("module", "full"),
        default="full",
        help="module=只看模块级字段；full=含类/函数",
    )
    read.add_argument("--full", action="store_true", help="打印函数 docstring 全文")
    read.add_argument("--format", choices=("text", "json", "md"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check(args)
    return cmd_read(args)


if __name__ == "__main__":
    raise SystemExit(main())
