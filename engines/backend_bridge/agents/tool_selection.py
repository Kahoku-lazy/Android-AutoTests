from __future__ import annotations

from engines.ae_harness.tools import build_adb_readonly_tools, build_adb_tools, list_tool_catalog
from engines.ae_harness.tools.case_library.tools import (
    build_case_library_readonly_tools,
    build_case_library_tools,
)
from engines.ae_harness.tools.document.tools import (
    build_document_readonly_tools,
    build_document_tools,
)

__all__ = ["ToolSelectionError", "select_tools"]

_BUILDERS = {
    ("adb", "all"): build_adb_tools,
    ("adb", "readonly"): build_adb_readonly_tools,
    ("case_library", "all"): build_case_library_tools,
    ("case_library", "readonly"): build_case_library_readonly_tools,
    ("document", "all"): build_document_tools,
    ("document", "readonly"): build_document_readonly_tools,
}
_ALL_TOOLS = {
    "adb": build_adb_tools,
    "case_library": build_case_library_tools,
    "document": build_document_tools,
}


class ToolSelectionError(ValueError):
    pass


KIND_DOMAINS = {
    "ui_automation": {"adb"},
    "case_authoring": {"case_library"},
    "requirement_breakdown": {"document"},
}


def select_tools(selections: list[dict] | None, *, kind: str = "ui_automation") -> list:
    catalog = {item["domain"]: item for item in list_tool_catalog()}
    allowed = KIND_DOMAINS.get(kind, set())
    chosen: list = []
    for item in selections or []:
        if str(item.get("domain") or "") not in allowed:
            continue
        domain = str(item.get("domain") or "")
        preset = str(item.get("preset") or "")
        entry = catalog.get(domain)
        builder = _BUILDERS.get((domain, preset))
        if entry is None or builder is None:
            raise ToolSelectionError(f"未知工具域或预设：{domain}/{preset}")
        known = {tool["name"] for tool in entry["tools"]}
        add = list(item.get("add") or [])
        remove = list(item.get("remove") or [])
        unknown = [name for name in [*add, *remove] if name not in known]
        if unknown:
            raise ToolSelectionError(f"未知工具：{', '.join(unknown)}")
        names = {tool.name for tool in builder()}
        names.update(add)
        names.difference_update(remove)
        chosen.extend(tool for tool in _ALL_TOOLS[domain]() if tool.name in names)
    return chosen


if __name__ == "__main__":
    print(len(select_tools([{"domain": "adb", "preset": "readonly", "add": [], "remove": []}])))  # noqa: T201
