from __future__ import annotations

import tomllib

from pathlib import Path

from utils.linting.model import Config, Forbid

CONFIG_NAME = ".linting"
ALERT_LEVELS = {"none", "warn", "error"}

CONFIG_KEYS = {
    "source_roots",
    "exclude",
    "exact",
    "forbid_circular_dependencies",
    "ignore_type_checking_imports",
    "root_packages",
    "include_external_packages",
    "modules",
    "forbid",
}
MODULE_KEYS = {"path", "depends_on", "cannot_depend_on", "utility", "unchecked"}
FORBID_KEYS = {
    "slug",
    "name",
    "source",
    "forbidden",
    "ignore_imports",
    "allow_indirect_imports",
    "unmatched_ignore_imports_alerting",
}


def load_config(config_path: Path) -> Config:
    if not config_path.is_file():
        raise ValueError(f"找不到配置文件：{config_path}")

    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    root = config_path.parent

    unknown = set(raw) - CONFIG_KEYS
    if unknown:
        raise ValueError(f"配置文件里有未知键：{', '.join(sorted(unknown))}")
    if raw.get("forbid_circular_dependencies"):
        raise ValueError("未支持 forbid_circular_dependencies（本工具不查环）")

    modules = _load_modules(raw.get("modules", []))
    forbids = _load_forbids(raw.get("forbid", []))
    exclude_raw = raw.get("exclude", [])

    return Config(
        root=root,
        source_roots=[root / entry for entry in raw.get("source_roots", ["."])],
        exclude=frozenset(expand_patterns(exclude_raw)),
        exclude_raw=exclude_raw,
        exact=bool(raw.get("exact", False)),
        ignore_type_checking=bool(raw.get("ignore_type_checking_imports", True)),
        root_packages=raw.get("root_packages", []),
        include_external=bool(raw.get("include_external_packages", False)),
        modules=modules,
        forbids=forbids,
    )


def _load_modules(entries: list[dict]) -> dict[str, dict]:
    modules: dict[str, dict] = {}
    for entry in entries:
        path = entry.get("path")
        if not path:
            raise ValueError("[[modules]] 缺少 path 字段")
        extra = set(entry) - MODULE_KEYS
        if extra:
            raise ValueError(f"模块 {path} 有未知字段：{', '.join(sorted(extra))}")
        for key in ("depends_on", "cannot_depend_on"):
            value = entry.get(key)
            if value is not None and not is_str_list(value):
                raise ValueError(f"模块 {path} 的 {key} 只支持字符串路径列表")
        modules[path] = entry
    return modules


def _load_forbids(entries: list[dict]) -> list[Forbid]:
    forbids: list[Forbid] = []
    for entry in entries:
        extra = set(entry) - FORBID_KEYS
        if extra:
            raise ValueError(f"禁止合同有未知字段：{', '.join(sorted(extra))}")
        for key in ("slug", "name", "source", "forbidden"):
            if not entry.get(key):
                raise ValueError(f"[[forbid]] 缺少 {key} 字段")
        for key in ("source", "forbidden", "ignore_imports"):
            if entry.get(key) is not None and not is_str_list(entry[key]):
                raise ValueError(f"禁止合同 {entry['slug']} 的 {key} 只支持字符串列表")
        alerting = entry.get("unmatched_ignore_imports_alerting", "error")
        if alerting not in ALERT_LEVELS:
            raise ValueError(f"禁止合同 {entry['slug']} 的告警级别非法：{alerting}")
        forbids.append(
            Forbid(
                slug=entry["slug"],
                name=entry["name"],
                source=entry["source"],
                forbidden=entry["forbidden"],
                ignore_imports=entry.get("ignore_imports", []),
                allow_indirect=bool(entry.get("allow_indirect_imports", False)),
                unmatched_alerting=alerting,
            )
        )
    return forbids


def is_str_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def expand_patterns(patterns: list[str]) -> set[str]:
    expanded: set[str] = set()
    for pattern in patterns:
        trimmed = pattern.rstrip("/")
        expanded.add(trimmed)
        expanded.add(trimmed[3:] if trimmed.startswith("**/") else trimmed)
    return expanded
