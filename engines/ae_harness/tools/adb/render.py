"""
文件名: ➡️ render.py 🏁
路径: ➡️ engines/ae_harness/tools/adb/render.py 🏁
模块功能：➡️ adb 工具的专属展示片段：网格锚点表 🏁
Python 调试：➡️ python -m engines.ae_harness.tools.adb.render 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. render_grid_marks: 把 adb_screenshot_grid 的返回渲染成「网格参数 + 候选点表」。
2. 供 HtmlReportRenderer 通过 step_extras 注册，不反向依赖 event 的数据类型。
🏁
关联模块：➡️
1. engines.ae_harness.tools.adb.tools: adb_screenshot_grid 产出的 JSON 结构。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor 生成的报告。
🏁
"""

from __future__ import annotations

import html
import json

__all__ = ["render_grid_marks"]


def render_grid_marks(step: object) -> str:
    """
    把带网格锚点的一步渲染成表格。

    Args:
        step: 步骤记录；只读它的 `output` 字段。

    Returns:
        已转义的 HTML 片段；解析不出 marks 时返回空串。
    """
    try:
        data = json.loads(getattr(step, "output", "") or "")
    except (TypeError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    marks = data.get("marks") or []
    if not isinstance(marks, list) or not marks:
        return ""

    grid = data.get("grid") or {}
    parts: list[str] = []
    if isinstance(grid, dict) and grid:
        center = (
            f"中心 ({grid.get('nx')}, {grid.get('ny')}) · "
            f"{grid.get('size')}×{grid.get('size')} · 步长 {grid.get('step')}"
        )
        parts.append(f'<div class="io"><b>网格</b>{html.escape(center)}</div>')
    parts.append('<table class="marks"><tr><th>序号</th><th>nx</th><th>ny</th></tr>')
    for mark in marks:
        if not isinstance(mark, dict):
            continue
        parts.append(
            f"<tr><td>{mark.get('index')}</td><td>{mark.get('nx')}</td>"
            f"<td>{mark.get('ny')}</td></tr>"
        )
    parts.append("</table>")
    return "".join(parts)
