"""
文件名: ➡️ catalog.py 🏁
路径: ➡️ engines/ae_harness/tools/catalog.py 🏁
模块功能：➡️ 只读列出已注册工具域、预设与函数名 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.catalog 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-16 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. list_tool_catalog: 返回域、预设和函数说明，不含实现。
2. 不造 Agent，不读配置，不执行工具。
🏁
关联模块：➡️
1. engines.ae_harness.tools.adb: 只读取已导出的装配函数来取名字。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from .adb import build_adb_readonly_tools, build_adb_tools
from .case_library.tools import build_case_library_readonly_tools, build_case_library_tools
from .document.tools import build_document_readonly_tools, build_document_tools

__all__ = ["list_tool_catalog"]

_DOMAINS = (
    {
        "domain": "adb",
        "label": "adb",
        "all_builder": build_adb_tools,
        "readonly_builder": build_adb_readonly_tools,
    },
    {
        "domain": "case_library",
        "label": "用例库",
        "all_builder": build_case_library_tools,
        "readonly_builder": build_case_library_readonly_tools,
    },
    {
        "domain": "document",
        "label": "文档",
        "all_builder": build_document_tools,
        "readonly_builder": build_document_readonly_tools,
    },
)


def list_tool_catalog() -> list[dict]:
    """
    列出已注册工具域。

    Returns:
        每个域含 domain、label、presets 与 tools。tools 只有 name 与 description。
    """
    catalog: list[dict] = []
    for item in _DOMAINS:
        tools = item["all_builder"]()
        readonly = {tool.name for tool in item["readonly_builder"]()}
        catalog.append(
            {
                "domain": item["domain"],
                "label": item["label"],
                "presets": [
                    {"id": "all", "label": "全部"},
                    {"id": "readonly", "label": "只读"},
                ],
                "tools": [
                    {
                        "name": tool.name,
                        "description": (tool.description or "").split("\n", 1)[0],
                        "read_only": tool.name in readonly,
                    }
                    for tool in tools
                ],
            }
        )
    return catalog


if __name__ == "__main__":
    print([item["domain"] for item in list_tool_catalog()])  # noqa: T201
