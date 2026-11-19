"""生成前端 10 个 + 后端 12 个模块页（同一套模板，靠 scope 区分）。

页面统一写到 html/ 子目录；模板与生成脚本留在 tools/。

用法：
    python dev_docs/project-viz/tools/gen_module_pages.py
"""

from __future__ import annotations

import json

from pathlib import Path

VIZ = Path(__file__).resolve().parents[1]
PAGES = VIZ / "html"
TEMPLATE = VIZ / "tools" / "module-page.template.html"

GROUPS = (
    ("frontend", "frontendModules", "前端"),
    ("backend", "backendModules", "后端"),
)


def main() -> int:
    board = json.loads((VIZ / "data" / "board.json").read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")

    def items(scope: str, active: str) -> str:
        """某个分组下的侧栏项；active 为空串表示当前页不属于该分组。"""
        keys = [module["key"] for module in board[f"{scope}Modules"]["modules"]]
        lines = []
        for key in keys:
            cls = "sidebar__nav-item sidebar__nav-item--sub"
            current = ""
            if key == active:
                cls += " is-active"
                current = ' aria-current="page"'
            lines.append(f'          <a class="{cls}" href="{scope}-{key}.html"{current}>{key}</a>')
        return "\n".join(lines)

    total = 0
    for scope, _, scope_label in GROUPS:
        keys = [module["key"] for module in board[f"{scope}Modules"]["modules"]]
        for key in keys:
            html = (
                template.replace("__KEY__", key)
                .replace("__MODULE_TITLE__", key)
                .replace("__SCOPE__", scope)
                .replace("__SCOPE_LABEL__", scope_label)
                .replace(
                    "__FRONTEND_ITEMS__", items("frontend", key if scope == "frontend" else "")
                )
                .replace("__BACKEND_ITEMS__", items("backend", key if scope == "backend" else ""))
            )
            (PAGES / f"{scope}-{key}.html").write_text(html, encoding="utf-8")
            total += 1
        print(f"{scope_label}：{len(keys)} 个页面")  # noqa: T201

    print(f"合计 {total} 个模块页")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
