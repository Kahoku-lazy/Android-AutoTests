"""侧栏同步器：把五个主页面的侧栏与模块页模板刷成与 board.json 一致的模块清单。

模块清单来自 data/board.json（生成器产出），不在脚本里硬编码，避免下次再对不上。
模块增删时跑一次：python dev_docs/project-viz/tools/sync_sidebar.py
"""

from __future__ import annotations

import json
import re
import sys

from pathlib import Path

VIZ = Path(__file__).resolve().parents[1]
BOARD = json.loads((VIZ / "data" / "board.json").read_text(encoding="utf-8"))
FRONTEND_KEYS = [row["key"] for row in BOARD["frontendModules"]["modules"]]
BACKEND_KEYS = [row["key"] for row in BOARD["backendModules"]["modules"]]

PAGES = ("index.html", "frontend.html", "backend.html", "agents.html", "ae-harness.html")
ENGINES_LABEL = "引擎功能模块"


def link(href: str, label: str, *, active: bool = False, sub: bool = False) -> str:
    """一行侧栏链接；sub 表示缩进的模块子项。"""
    cls = "sidebar__nav-item"
    if sub:
        cls += " sidebar__nav-item--sub"
    if active:
        cls += " is-active"
    current = ' aria-current="page"' if active else ""
    return f'          <a class="{cls}" href="{href}"{current}>{label}</a>'


def page_href(target: str, *, root: bool) -> str:
    """页面之间的链接。

    入口 `index.html` 在项目根，其余页面在 `html/`：
    - 根目录入口页：指向别的页面要带 `html/` 前缀，指向自己就是 `index.html`；
    - `html/` 里的页面：指向入口写 `../index.html`，指向同级页面直接写文件名。

    Args:
        target: 目标页文件名。
        root: 当前页面是否就是根目录的 index.html。

    Returns:
        可用的相对 href。
    """
    if target == "index.html":
        return "index.html" if root else "../index.html"
    return f"html/{target}" if root else target


def nav_html(active: str | list[str], *, template: bool = False, root: bool = False) -> str:
    """整段侧栏导航；active 可以是单个 href 主干或主干列表。"""
    active_keys = {active} if isinstance(active, str) else set(active)
    lines = [
        '          <p class="sidebar__group">视图</p>',
        link(page_href("index.html", root=root), "总览", active="index" in active_keys),
        '          <p class="sidebar__group">前端</p>',
        link(
            page_href("frontend.html", root=root), "前端功能模块", active="frontend" in active_keys
        ),
    ]
    if template:
        lines.append("__FRONTEND_ITEMS__")
    else:
        for key in FRONTEND_KEYS:
            lines.append(
                link(
                    page_href(f"frontend-{key}.html", root=root),
                    key,
                    sub=True,
                    active=f"frontend-{key}" in active_keys,
                )
            )
    lines += [
        '          <p class="sidebar__group">后端</p>',
        link(page_href("backend.html", root=root), "后端功能模块", active="backend" in active_keys),
    ]
    if template:
        lines.append("__BACKEND_ITEMS__")
    else:
        for key in BACKEND_KEYS:
            lines.append(
                link(
                    page_href(f"backend-{key}.html", root=root),
                    key,
                    sub=True,
                    active=f"backend-{key}" in active_keys,
                )
            )
    lines += [
        '          <p class="sidebar__group">引擎</p>',
        link(page_href("agents.html", root=root), ENGINES_LABEL, active="agents" in active_keys),
        '          <p class="sidebar__group">ae_harness</p>',
        link(
            page_href("ae-harness.html", root=root), "原型链路", active="ae-harness" in active_keys
        ),
    ]
    return "\n".join(lines)


NAV_RE = re.compile(r'(<nav class="sidebar__nav" aria-label="导航">\n)(.*?)(\n\s*</nav>)', re.S)


def rewrite(
    path: Path, active: str | list[str], *, template: bool = False, root: bool = False
) -> bool:
    """把某个文件的侧栏替换成生成内容，返回是否有改动。"""
    text = path.read_text(encoding="utf-8")
    match = NAV_RE.search(text)
    if not match:
        return False
    updated = (
        text[: match.start(2)]
        + nav_html(active, template=template, root=root)
        + text[match.end(2) :]
    )
    updated = updated.replace("智能体功能模块", ENGINES_LABEL)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    """跑一遍：入口页在根、其余页面在 html/，模板保留占位符。"""
    changed = rewrite(VIZ / "index.html", "index", root=True)
    print(f"index.html（入口）: {'updated' if changed else 'unchanged'}")
    pages_dir = VIZ / "html"
    for name in PAGES:
        if name == "index.html":
            continue
        stem = name.removesuffix(".html")
        changed = rewrite(pages_dir / name, stem)
        print(f"html/{name}: {'updated' if changed else 'unchanged'}")
    template = VIZ / "tools" / "module-page.template.html"
    changed = rewrite(template, [], template=True)
    print(f"module-page.template.html: {'updated' if changed else 'unchanged'}")
    print(f"frontend {len(FRONTEND_KEYS)} 项 / backend {len(BACKEND_KEYS)} 项")
    return 0


if __name__ == "__main__":
    sys.exit(main())
