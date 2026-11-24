from __future__ import annotations

import json

from pathlib import Path

from utils.linting.model import Config


def render_tach_toml(config: Config) -> str:
    lines = ["exclude = " + toml_list(config.exclude_raw), ""]
    lines.append("source_roots = " + toml_list(rels(config)))
    lines.append("forbid_circular_dependencies = false")
    lines.append(f"exact = {str(config.exact).lower()}")
    for module_path, entry in config.modules.items():
        lines.append("")
        lines.append("[[modules]]")
        lines.append(f'path = "{module_path}"')
        if entry.get("utility"):
            lines.append("utility = true")
        else:
            lines.append("depends_on = " + toml_list(entry.get("depends_on") or []))
        if entry.get("cannot_depend_on"):
            lines.append("cannot_depend_on = " + toml_list(entry["cannot_depend_on"]))
        if entry.get("unchecked"):
            lines.append("unchecked = true")
    return "\n".join(lines) + "\n"


def render_importlinter(config: Config) -> str:
    lines = ["[importlinter]", "root_packages ="]
    lines += [f"    {name}" for name in config.root_packages]
    lines.append(f"include_external_packages = {config.include_external}")
    for contract in config.forbids:
        lines.append("")
        lines.append(f"[importlinter:contract:{contract.slug}]")
        lines.append(f"name = {contract.name}")
        lines.append("type = forbidden")
        lines.append("source_modules =")
        lines += [f"    {name}" for name in contract.source]
        lines.append("forbidden_modules =")
        lines += [f"    {name}" for name in contract.forbidden]
        if contract.ignore_imports:
            lines.append("ignore_imports =")
            lines += [f"    {expr}" for expr in contract.ignore_imports]
        if contract.allow_indirect:
            lines.append("allow_indirect_imports = True")
        if contract.ignore_imports or contract.unmatched_alerting != "error":
            lines.append(f"unmatched_ignore_imports_alerting = {contract.unmatched_alerting}")
    return "\n".join(lines) + "\n"


def toml_list(values: list[str] | set[str]) -> str:
    return "[" + ", ".join(json.dumps(item, ensure_ascii=False) for item in values) + "]"


def rels(config: Config) -> list[str]:
    return [root.relative_to(config.root).as_posix() for root in config.source_roots]


def export(config: Config, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in (
        ("tach.toml", render_tach_toml(config)),
        (".importlinter", render_importlinter(config)),
    ):
        destination = out_dir / name
        destination.write_text(text, encoding="utf-8")
        written.append(destination)
    return written
