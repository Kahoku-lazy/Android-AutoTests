# -*- coding: utf-8 -*-
"""
文件名：➡️ module_docstring.py 🏁
路径：➡️ utils/module_docstring.py 🏁
模块功能：➡️ 模块 docstring 字段解析、校验与按文件夹批量提取 🏁
Python 调试：➡️ python -m utils.module_docstring 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. parse_module_docstring: 从文本解析 ➡…🏁 字段为 dict（键齐全）
2. validate_module_docstring: 校验必填/类型/路径等，返回 issues 列表
3. read_module_docstring: 先校验后读取，返回 JSON 形字段 dict
4. iter_python_modules: 遍历文件夹下 *.py（跳过 __pycache__ / skill-creator）
5. extract_module_docstrings: 按文件夹批量 extract→parse→validate；strict=False 时收集 issues 不中断
🏁
关联模块：➡️ 1. （标准库）ast / pathlib / re / json / argparse: 解析与 CLI 🏁
测试：➡️
1. 暂无专门单测；python -m utils.module_docstring 可对样例冒烟
2. 单文件: python -m utils.module_docstring engines/agents/config/config.py --repo-root .
3. 批量文件夹: python -m utils.module_docstring engines/agents --repo-root . --out temps/agents_fields.json
4. 批量严格: python -m utils.module_docstring engines/agents --repo-root . --strict
🏁
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

MODULE_FIELDS: list[str] = [
    "文件名",
    "路径",
    "模块功能",
    "Python 调试",
    "时间",
    "作者",
    "版本",
    "类型",
    "简介说明",
    "关联模块",
    "测试",
    "修改时间",  # optional but always emitted
]

REQUIRED_FIELDS: list[str] = [
    "文件名",
    "路径",
    "模块功能",
    "Python 调试",
    "时间",
    "作者",
    "版本",
    "类型",
    "简介说明",
    "关联模块",
    "测试",
]

OPTIONAL_FIELDS: list[str] = ["修改时间"]

ALLOWED_TYPES: frozenset[str] = frozenset(
    {
        "工具模块",
        "模型配置模块",
        "Harness 配置模块",
        "Agent 能力模块",
    }
)

ARROW = "\u27a1"  # U+27A1
FLAG = "\U0001f3c1"  # U+1F3C1

_FIELD_RE_CACHE: dict[str, re.Pattern[str]] = {}

_LEGACY_SHUOMING_RE = re.compile(
    r"(?m)^说明\s*[:：]\s*"
    + ARROW
    + r"(?:\ufe0f)?"
    + r"(.*?)"
    + FLAG,
    re.DOTALL,
)

_DEBUG_PREFIX_RE = re.compile(
    r"^(?:Python\s*调试运行入口\s*[:：]?\s*|调试运行入口\s*[:：]?\s*)",
    re.IGNORECASE,
)


class ModuleDocstringValidationError(ValueError):
    """Raised by read_module_docstring when strict validation fails."""

    def __init__(self, issues: list[str], *, path: str | None = None) -> None:
        self.issues = list(issues)
        self.path = path
        msg = "; ".join(self.issues) if self.issues else "module docstring invalid"
        if path:
            msg = f"{path}: {msg}"
        super().__init__(msg)


def _field_re(name: str) -> re.Pattern[str]:
    """Match field markers: name[:：] + U+27A1 + optional U+FE0F + value + U+1F3C1."""
    if name not in _FIELD_RE_CACHE:
        _FIELD_RE_CACHE[name] = re.compile(
            re.escape(name)
            + r"\s*[:：]\s*"
            + ARROW
            + r"(?:\ufe0f)?"
            + r"(.*?)"
            + FLAG,
            re.DOTALL,
        )
    return _FIELD_RE_CACHE[name]


def normalize_python_debug(value: str) -> str:
    """Strip legacy prefixes; keep a trimmed python -m style value."""
    v = (value or "").strip()
    if not v:
        return ""
    return _DEBUG_PREFIX_RE.sub("", v).strip()


def looks_like_python_m(value: str) -> bool:
    """True if value looks like python -m package.module."""
    v = (value or "").strip()
    return bool(re.match(r"^python\s+-m\s+\S+", v, re.IGNORECASE))


def empty_module_fields() -> dict[str, str]:
    """Return a dict with every MODULE_FIELDS key set to empty string."""
    return {k: "" for k in MODULE_FIELDS}


def parse_module_docstring(text: str) -> dict[str, str]:
    """Parse module docstring fields into a dict (all MODULE_FIELDS keys).

    Legacy label 说明 maps into Python 调试 when that key is empty.
    Does not validate; use validate_module_docstring / read_module_docstring.
    """
    out = empty_module_fields()
    doc = text or ""
    for name in MODULE_FIELDS:
        m = _field_re(name).search(doc)
        out[name] = m.group(1).strip() if m else ""

    legacy = _LEGACY_SHUOMING_RE.search(doc)
    legacy_val = legacy.group(1).strip() if legacy else ""
    if not out.get("Python 调试") and legacy_val:
        out["Python 调试"] = normalize_python_debug(legacy_val)
    elif out.get("Python 调试"):
        out["Python 调试"] = normalize_python_debug(out["Python 调试"])
    return out


def validate_module_docstring(
    fields: dict[str, str] | None = None,
    *,
    text: str | None = None,
    rel_path: str | Path | None = None,
    require_allowed_type: bool = True,
    check_path_match: bool = True,
    check_python_debug_format: bool = True,
) -> list[str]:
    """Validate module docstring fields; return issue strings (empty = OK)."""
    if fields is None:
        if text is None:
            raise TypeError("validate_module_docstring requires fields= or text=")
        fields = parse_module_docstring(text)
    else:
        merged = empty_module_fields()
        merged.update({k: (v or "") for k, v in fields.items() if k in merged})
        if text is not None:
            parsed = parse_module_docstring(text)
            for k, v in parsed.items():
                if not merged.get(k) and v:
                    merged[k] = v
        elif merged.get("Python 调试"):
            merged["Python 调试"] = normalize_python_debug(merged["Python 调试"])
        fields = merged

    issues: list[str] = []

    if text is not None and not (text or "").strip():
        issues.append("缺少模块 docstring")
    elif text is not None and all(not fields.get(k) for k in REQUIRED_FIELDS):
        issues.append("有 docstring 但未使用➡️/🏁模板")

    for k in REQUIRED_FIELDS:
        if not (fields.get(k) or "").strip():
            msg = f"缺少字段：{k}"
            if msg not in issues:
                issues.append(msg)

    t = (fields.get("类型") or "").strip()
    if require_allowed_type and t and t not in ALLOWED_TYPES:
        issues.append(f"类型不合法：{t}")

    rel: str | None = None
    if rel_path is not None:
        rel = Path(rel_path).as_posix()

    if check_path_match and rel:
        if fields.get("路径") and fields["路径"] != rel:
            issues.append(
                f"路径不匹配：期望 {rel}，实际 {fields['路径']}"
            )
        expected_name = Path(rel).name
        if fields.get("文件名") and fields["文件名"] != expected_name:
            issues.append(
                f"文件名不匹配：期望 {expected_name}，实际 {fields['文件名']}"
            )

    py_dbg = (fields.get("Python 调试") or "").strip()
    if check_python_debug_format and py_dbg and not looks_like_python_m(py_dbg):
        issues.append(f"Python 调试格式异常（期望 python -m …）：{py_dbg}")

    seen: set[str] = set()
    out: list[str] = []
    for item in issues:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def extract_module_docstring_from_source(
    source: str, *, filename: str = "<unknown>"
) -> str:
    """Return the module docstring from Python source, or empty string."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return ""
    return ast.get_docstring(tree) or ""


def read_module_docstring(
    path: str | Path,
    *,
    repo_root: str | Path | None = None,
    rel_path: str | Path | None = None,
    strict: bool = True,
) -> dict[str, str]:
    """Validate first, then return module docstring fields (all keys present).

    Flow: extract → parse → validate → (raise if strict) → return fields.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = file_path.read_text(encoding="utf-8", errors="replace")

    raw = extract_module_docstring_from_source(source, filename=str(file_path))
    fields = parse_module_docstring(raw)

    if rel_path is not None:
        rel = Path(rel_path).as_posix()
    elif repo_root is not None:
        try:
            rel = file_path.resolve().relative_to(Path(repo_root).resolve()).as_posix()
        except ValueError:
            rel = file_path.as_posix()
    else:
        rel = None

    issues = validate_module_docstring(fields, text=raw, rel_path=rel)
    if strict and issues:
        raise ModuleDocstringValidationError(issues, path=str(file_path))
    return fields


def is_compliant(fields: dict[str, str], rel_path: str | Path) -> bool:
    """True when required fields, type, path/filename, and python -m look OK."""
    return not validate_module_docstring(fields, rel_path=rel_path)



def iter_python_modules(
    root: str | Path,
    *,
    recursive: bool = True,
    include_init: bool = True,
) -> Iterator[Path]:
    """Yield *.py paths under root, skipping __pycache__ and skill-creator trees.

    Args:
        root: Folder to walk.
        recursive: If True (default), rglob; else only the immediate directory.
        include_init: If False, skip __init__.py files.
    """
    base = Path(root)
    if not base.is_dir():
        return iter(())

    def _skip(path: Path) -> bool:
        parts = path.as_posix()
        if "__pycache__" in parts or "skill-creator" in parts:
            return True
        if not include_init and path.name == "__init__.py":
            return True
        return False

    pattern_iter = base.rglob("*.py") if recursive else base.glob("*.py")
    return (p for p in sorted(pattern_iter) if not _skip(p))


def extract_module_docstrings(
    folder: str | Path,
    *,
    repo_root: str | Path | None = None,
    recursive: bool = True,
    strict: bool = False,
    include_init: bool = True,
) -> list[dict[str, Any]]:
    """Batch extract->parse->validate module docstring fields under a folder.

    Returns a list of records::

        {"file": "<rel_posix>", "fields": {...}, "issues": [...]}

    ``strict=False`` (default for batch): one bad file does not abort the folder;
    that file still appears with a non-empty ``issues`` list (and empty/partial
    fields as parsed).

    ``strict=True``: raise ``ModuleDocstringValidationError`` on the first file
    that has validation issues (or cannot be read). Earlier successful records
    are not returned.

    Relative ``file`` paths are computed against ``repo_root`` when given,
    otherwise against ``folder``.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise NotADirectoryError(str(folder_path))

    root_path = Path(repo_root).resolve() if repo_root is not None else folder_path.resolve()
    records: list[dict[str, Any]] = []

    for file_path in iter_python_modules(
        folder_path, recursive=recursive, include_init=include_init
    ):
        try:
            rel = file_path.resolve().relative_to(root_path).as_posix()
        except ValueError:
            try:
                rel = file_path.resolve().relative_to(folder_path.resolve()).as_posix()
            except ValueError:
                rel = file_path.as_posix()

        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            issues = [f"无法读取文件：{e}"]
            if strict:
                raise ModuleDocstringValidationError(issues, path=str(file_path)) from e
            records.append(
                {
                    "file": rel,
                    "fields": empty_module_fields(),
                    "issues": issues,
                }
            )
            continue

        raw = extract_module_docstring_from_source(source, filename=str(file_path))
        fields = parse_module_docstring(raw)
        issues = validate_module_docstring(fields, text=raw, rel_path=rel)
        if strict and issues:
            raise ModuleDocstringValidationError(issues, path=str(file_path))
        records.append({"file": rel, "fields": fields, "issues": issues})

    return records


def extract_module_docstrings_map(
    folder: str | Path,
    *,
    repo_root: str | Path | None = None,
    recursive: bool = True,
    strict: bool = False,
    include_init: bool = True,
) -> dict[str, dict[str, str]]:
    """Same as extract_module_docstrings, but return mapping rel_path -> fields only.

    Validation issues are discarded in the map; use extract_module_docstrings
    when you need per-file issues. ``strict`` behaves the same (raise on first).
    """
    records = extract_module_docstrings(
        folder,
        repo_root=repo_root,
        recursive=recursive,
        strict=strict,
        include_init=include_init,
    )
    return {r["file"]: r["fields"] for r in records}


# Back-compat aliases used by temps/ scripts
parse_module_fields = parse_module_docstring


def main(argv: list[str] | None = None) -> int:
    """CLI: read one .py or batch a folder; print JSON fields / records.

    Single file (default path engines/agents/config/config.py):
      python -m utils.module_docstring [path.py] [--repo-root .] [--no-strict]

    Folder batch (strict defaults to False; use --strict to abort on first issue):
      python -m utils.module_docstring engines/agents --repo-root .
      python -m utils.module_docstring engines/agents --repo-root . --out temps/out.json
      python -m utils.module_docstring engines/agents --repo-root . --strict
    """
    parser = argparse.ArgumentParser(
        description="Parse/validate module docstring fields (file or folder batch)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="",
        help="Python file or folder (default file: engines/agents/config/config.py)",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repo root for relative path checks",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Single-file: return fields even when validation fails",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Batch: raise/exit on first validation failure (default: collect issues)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional path to write JSON (UTF-8); still prints to stdout",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Batch: only immediate directory (default: recursive)",
    )
    parser.add_argument(
        "--skip-init",
        action="store_true",
        help="Batch: skip __init__.py files",
    )
    parser.add_argument(
        "--as-map",
        action="store_true",
        help="Batch: emit {rel_path: fields} object instead of records array",
    )
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    target = args.path or "engines/agents/config/config.py"
    target_path = Path(target)
    root = Path(args.repo_root) if args.repo_root else None

    # Directory -> batch mode
    if target_path.is_dir():
        try:
            records = extract_module_docstrings(
                target_path,
                repo_root=root,
                recursive=not args.no_recursive,
                strict=args.strict,
                include_init=not args.skip_init,
            )
        except ModuleDocstringValidationError as e:
            payload = {"error": str(e), "issues": e.issues, "path": e.path}
            text = json.dumps(payload, ensure_ascii=False, indent=2)
            print(text)
            if args.out:
                out_path = Path(args.out)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(text + "\n", encoding="utf-8")
            return 1

        if args.as_map:
            data: Any = {r["file"]: r["fields"] for r in records}
        else:
            data = records
        text = json.dumps(data, ensure_ascii=False, indent=2)
        print(text)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text + "\n", encoding="utf-8")

        n_issues = sum(1 for r in records if r.get("issues"))
        n_issue_items = sum(len(r.get("issues") or []) for r in records)
        print(
            f"files={len(records)} with_issues={n_issues} issue_items={n_issue_items}",
            file=sys.stderr,
        )
        return 0

    # Single-file mode (default strict unless --no-strict)
    try:
        fields = read_module_docstring(
            target_path, repo_root=root, strict=not args.no_strict
        )
    except ModuleDocstringValidationError as e:
        text = json.dumps(
            {"error": str(e), "issues": e.issues}, ensure_ascii=False, indent=2
        )
        print(text)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text + "\n", encoding="utf-8")
        return 1
    text = json.dumps(fields, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print("validate: OK", file=sys.stderr)
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
