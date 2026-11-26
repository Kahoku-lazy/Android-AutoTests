# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
import json
import re
import sys

from pathlib import Path
from typing import Any, Iterator

REQUIRED_FIELDS: list[str] = [
    "模块功能",
    "Python 调试",
    "时间",
    "测试",
]

LEGACY_FIELDS: list[str] = [
    "文件名",
    "路径",
    "作者",
    "版本",
    "修改时间",
    "类型",
    "简介说明",
    "关联模块",
]

MODULE_FIELDS: list[str] = [*REQUIRED_FIELDS, *LEGACY_FIELDS]

OPTIONAL_FIELDS: list[str] = list(LEGACY_FIELDS)

ALLOWED_TYPES: frozenset[str] = frozenset(
    {
        "工具模块",
        "模型配置模块",
        "Harness 配置模块",
        "Agent 能力模块",
    }
)

ARROW = "\u27a1"
FLAG = "\U0001f3c1"

TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_FIELD_RE_CACHE: dict[str, re.Pattern[str]] = {}

_LEGACY_SHUOMING_RE = re.compile(
    r"(?m)^说明\s*[:：]\s*" + ARROW + r"(?:\ufe0f)?" + r"(.*?)" + FLAG,
    re.DOTALL,
)

_DEBUG_PREFIX_RE = re.compile(
    r"^(?:Python\s*调试运行入口\s*[:：]?\s*|调试运行入口\s*[:：]?\s*)",
    re.IGNORECASE,
)


class ModuleDocstringValidationError(ValueError):
    def __init__(self, issues: list[str], *, path: str | None = None) -> None:
        self.issues = list(issues)
        self.path = path
        msg = "; ".join(self.issues) if self.issues else "module docstring invalid"
        if path:
            msg = f"{path}: {msg}"
        super().__init__(msg)


def _field_re(name: str) -> re.Pattern[str]:
    if name not in _FIELD_RE_CACHE:
        _FIELD_RE_CACHE[name] = re.compile(
            re.escape(name) + r"\s*[:：]\s*" + ARROW + r"(?:\ufe0f)?" + r"(.*?)" + FLAG,
            re.DOTALL,
        )
    return _FIELD_RE_CACHE[name]


def normalize_python_debug(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    return _DEBUG_PREFIX_RE.sub("", v).strip()


def looks_like_python_m(value: str) -> bool:
    v = (value or "").strip()
    return bool(re.match(r"^python\s+-m\s+\S+", v, re.IGNORECASE))


def empty_module_fields() -> dict[str, str]:
    return {k: "" for k in MODULE_FIELDS}


def parse_module_docstring(text: str) -> dict[str, str]:
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
    check_time_format: bool = True,
) -> list[str]:
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
            issues.append(f"路径不匹配：期望 {rel}，实际 {fields['路径']}")
        expected_name = Path(rel).name
        if fields.get("文件名") and fields["文件名"] != expected_name:
            issues.append(f"文件名不匹配：期望 {expected_name}，实际 {fields['文件名']}")

    py_dbg = (fields.get("Python 调试") or "").strip()
    if check_python_debug_format and py_dbg and not looks_like_python_m(py_dbg):
        issues.append(f"Python 调试格式异常（期望 python -m …）：{py_dbg}")

    when = (fields.get("时间") or "").strip()
    if check_time_format and when and not TIME_RE.match(when):
        issues.append(f"时间格式应为 YYYY-MM-DD：{when}")

    seen: set[str] = set()
    out: list[str] = []
    for item in issues:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def extract_module_docstring_from_source(source: str, *, filename: str = "<unknown>") -> str:
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
    return not validate_module_docstring(fields, rel_path=rel_path)


def iter_python_modules(
    root: str | Path,
    *,
    recursive: bool = True,
    include_init: bool = True,
) -> Iterator[Path]:
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
    records = extract_module_docstrings(
        folder,
        repo_root=repo_root,
        recursive=recursive,
        strict=strict,
        include_init=include_init,
    )
    return {r["file"]: r["fields"] for r in records}


parse_module_fields = parse_module_docstring


def main(argv: list[str] | None = None) -> int:
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

    try:
        fields = read_module_docstring(target_path, repo_root=root, strict=not args.no_strict)
    except ModuleDocstringValidationError as e:
        text = json.dumps({"error": str(e), "issues": e.issues}, ensure_ascii=False, indent=2)
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
