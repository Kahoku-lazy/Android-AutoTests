#!/usr/bin/env python3
"""Architecture Review Report Generator — 生成动物森友会主题 HTML 架构审查报告。

Usage:
    python report_generator.py --output report.html
    python report_generator.py --data analysis.json --output report.html
"""

import json
import argparse
from datetime import datetime
from pathlib import Path

ANIMAL_ISLAND_PALETTE = {
    "green": "#6fba2c", "blue": "#889df0", "yellow": "#f7cd67",
    "pink": "#f8a6b2", "teal": "#19c8b9", "purple": "#b39ef3",
    "orange": "#f7a8c4", "brown": "#8b7355", "red": "#e85f5f",
}


def _build_html(data: dict, timestamp: str) -> str:
    """Generate the complete HTML report from analysis data."""

    kpi = data.get("kpi", {})
    layers = data.get("layers", [])
    gaps = data.get("gaps", [])
    tasks = data.get("tasks", [])
    conclusion = data.get("conclusion", {})
    checks = data.get("verification", [])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Architecture Review Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --green:  {ANIMAL_ISLAND_PALETTE['green']}; --blue:   {ANIMAL_ISLAND_PALETTE['blue']};
    --yellow: {ANIMAL_ISLAND_PALETTE['yellow']}; --pink:   {ANIMAL_ISLAND_PALETTE['pink']};
    --teal:   {ANIMAL_ISLAND_PALETTE['teal']}; --purple: {ANIMAL_ISLAND_PALETTE['purple']};
    --orange: {ANIMAL_ISLAND_PALETTE['orange']}; --brown:  {ANIMAL_ISLAND_PALETTE['brown']};
    --red:    {ANIMAL_ISLAND_PALETTE['red']};
    --bg:     #fdf8f0; --card:   #fffaf5;
    --text:   #794f27; --text2:  #9f927d;
    --radius-lg: 24px; --radius-md: 16px; --radius-sm: 10px;
    --shadow: 0 2px 12px rgba(139,115,85,.08);
    --font-display: 'Nunito', -apple-system, sans-serif;
    --font-body: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: var(--font-body); background: var(--bg);
    background-image: radial-gradient(ellipse at 20% 0%, rgba(136,157,240,.06) 0%, transparent 50%),
                      radial-gradient(ellipse at 80% 100%, rgba(111,186,44,.04) 0%, transparent 50%);
    color: var(--text); padding: 32px 24px; line-height: 1.6;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  .header {{ text-align: center; margin-bottom: 32px; }}
  .header-icon {{ font-size: 40px; margin-bottom: 8px; }}
  h1 {{ font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--brown); }}
  .meta {{ color: var(--text2); font-size: 13px; margin-top: 4px; }}
  .summary {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 28px; }}
  .kpi {{
    background: var(--card); border-radius: var(--radius-lg); padding: 20px 24px;
    box-shadow: var(--shadow); border: 1.5px solid rgba(139,115,85,.08);
    position: relative; overflow: hidden;
  }}
  .kpi::before {{
    content: ''; position: absolute; top: -12px; right: -12px;
    width: 48px; height: 48px; border-radius: 50%; opacity: .12;
  }}
  .kpi:nth-child(1)::before {{ background: var(--blue); }}
  .kpi:nth-child(2)::before {{ background: var(--green); }}
  .kpi:nth-child(3)::before {{ background: var(--red); }}
  .kpi:nth-child(4)::before {{ background: var(--yellow); }}
  .kpi-label {{ font-size: 11px; letter-spacing: .6px; color: var(--text2); font-weight: 700; }}
  .kpi-value {{ font-family: var(--font-display); font-size: 36px; font-weight: 800; margin-top: 4px; }}
  .kpi-green {{ color: var(--green); }} .kpi-red {{ color: var(--red); }}
  .kpi-blue {{ color: var(--blue); }} .kpi-yellow {{ color: var(--brown); }}
  .conclusion {{
    background: var(--card); border-radius: var(--radius-lg); padding: 20px 24px;
    margin-bottom: 28px; border-left: 5px solid var(--teal); box-shadow: var(--shadow);
  }}
  .conclusion-text {{ font-size: 15px; font-weight: 600; }}
  .conclusion-next {{ font-size: 13px; color: var(--text2); margin-top: 6px; }}
  h2 {{ font-family: var(--font-display); font-size: 18px; font-weight: 700;
    color: var(--brown); margin: 32px 0 14px; padding-left: 4px; }}
  .table-wrap {{
    background: var(--card); border-radius: var(--radius-lg); overflow: hidden;
    box-shadow: var(--shadow); margin-bottom: 20px;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    background: linear-gradient(180deg, #faf5ed 0%, #f3ede2 100%);
    padding: 12px 14px; text-align: left; font-size: 10px;
    letter-spacing: .6px; color: var(--text2); font-weight: 700;
    border-bottom: 2px solid #e8dcc8;
  }}
  td {{ padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f3ede2; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:nth-child(even) {{ background: #fefbf7; }}
  .pass {{ color: var(--green); font-weight: 700; }}
  .fail {{ color: var(--red); font-weight: 700; }}
  .warn {{ color: #c7840a; font-weight: 700; }}

  /* Architecture layers */
  .arch-layer {{
    background: var(--card); border-radius: var(--radius-lg); padding: 24px;
    box-shadow: var(--shadow); margin-bottom: 20px; border: 2px dashed #e8dcc8;
  }}
  .arch-layer-title {{
    font-family: var(--font-display); font-size: 14px; font-weight: 800; margin-bottom: 16px;
  }}
  .layer-badge {{
    font-size: 11px; padding: 4px 12px; border-radius: 20px; color: #fff; font-weight: 700; margin-right: 8px;
  }}
  .layer-l1 {{ background: var(--purple); }}
  .layer-l2 {{ background: var(--blue); }}
  .layer-l3 {{ background: var(--teal); }}
  .layer-l4 {{ background: var(--brown); }}
  .module-grid {{
    display: grid; gap: 16px;
  }}
  .module-grid.cols-auto {{ grid-template-columns: repeat(auto-fit, minmax(140px,1fr)); }}
  .module-card {{
    background: #fff; border-radius: var(--radius-md); padding: 16px;
    text-align: center; border: 2px solid #e8dcc8; transition: transform .15s;
  }}
  .module-card:hover {{ transform: translateY(-2px); }}
  .module-card-icon {{ font-size: 24px; margin-bottom: 6px; }}
  .module-card-name {{ font-family: var(--font-display); font-weight: 700; font-size: 13px; }}
  .module-card-desc {{ font-size: 10px; color: var(--text2); margin-top: 4px; line-height: 1.4; }}
  .module-card-endpoints {{ font-size: 10px; color: var(--blue); font-weight: 600; margin-top: 6px; }}

  /* Communication lines */
  .comm-line-group {{ margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }}
  .comm-line {{
    display: flex; align-items: center; gap: 6px; padding: 4px 10px;
    background: #faf7f0; border-radius: var(--radius-sm); font-size: 11px;
  }}
  .comm-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .comm-rest {{ background: var(--blue); }} .comm-ws {{ background: var(--purple); }}
  .comm-sse {{ background: var(--teal); }} .comm-orm {{ background: var(--brown); }}

  /* Sub-grouping */
  .sub-group {{
    border: 1.5px dashed #e0d6c4; border-radius: var(--radius-md); padding: 20px 16px 16px;
    margin: 12px 0; position: relative;
  }}
  .sub-group-label {{
    position: absolute; top: -10px; left: 16px; background: var(--bg);
    padding: 2px 12px; font-size: 11px; font-weight: 700; color: var(--brown);
  }}

  /* Focus items */
  .focus-list {{ list-style: none; display: flex; flex-direction: column; gap: 8px; }}
  .focus-item {{ display: flex; gap: 14px; align-items: flex-start; padding: 12px 18px;
    background: var(--card); border-radius: var(--radius-sm); box-shadow: var(--shadow); }}
  .focus-prio {{ font-family: var(--font-display); font-weight: 800; font-size: 12px;
    padding: 4px 10px; border-radius: 20px; min-width: 36px; text-align: center; flex-shrink: 0; }}
  .prio-p0 {{ background: #fde8e8; color: var(--red); }}
  .prio-p1 {{ background: #fef3cd; color: #8a6d14; }}
  .prio-p2 {{ background: #e8f0fe; color: var(--blue); }}
  .focus-body {{ flex: 1; }}
  .focus-title {{ font-weight: 700; font-size: 14px; margin-bottom: 2px; }}
  .focus-desc {{ font-size: 12px; color: var(--text2); }}

  /* Status badges */
  .gap-badge {{
    display: inline-block; font-size: 10px; padding: 2px 8px; border-radius: 12px; font-weight: 700;
  }}
  .gap-new {{ background: #e8f5e0; color: var(--green); }}
  .gap-fix {{ background: #fef3cd; color: #8a6d14; }}
  .gap-remove {{ background: #fde8e8; color: var(--red); }}

  .footer {{ text-align: center; color: var(--text2); font-size: 11px; margin-top: 40px;
    padding-top: 20px; border-top: 2px dashed #e8dcc8; }}
  .footer-leaf {{ display: inline-block; animation: sway 2s ease-in-out infinite; }}
  @keyframes sway {{ 0%,100% {{ transform: rotate(-3deg); }} 50% {{ transform: rotate(3deg); }} }}

  @media (max-width: 900px) {{ .summary {{ grid-template-columns: repeat(2,1fr); }} }}
  @media print {{ body {{ background: #fff; }} }}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <div class="header-icon">🏗️</div>
  <h1>{data.get('title', 'Architecture Review Report')}</h1>
  <div class="meta">{timestamp} &middot; {data.get('subtitle', '')}</div>
</div>

{_build_kpi_section(kpi)}

{_build_conclusion(conclusion)}

{_build_layers_section(layers)}

<h2>📡 跨模块通信规范</h2>
<div class="table-wrap"><table>
<thead><tr><th>通信场景</th><th>协议/方式</th><th>约束</th></tr></thead>
<tbody>
<tr><td><strong>前端 → 后端</strong></td><td>HTTP REST + JWT Bearer</td><td>必须通过模块自己的 api.js</td></tr>
<tr><td><strong>前端 → 后端（实时）</strong></td><td>WebSocket</td><td>connect() 必须验证 JWT</td></tr>
<tr><td><strong>前端 → AI</strong></td><td>SSE 流式</td><td>AgentScope 独立鉴权</td></tr>
<tr><td><strong>后端跨模块读</strong></td><td>Django ORM 直接查询</td><td>防火墙 #2：读放开</td></tr>
<tr><td><strong>后端跨模块写</strong></td><td>api.py __all__ 函数</td><td>防火墙 #2：写收敛</td></tr>
<tr><td><strong>AgentScope → 后端</strong></td><td>同进程直接调用</td><td>不走 HTTP</td></tr>
</tbody>
</table></div>

{_build_gaps_section(gaps)}

{_build_tasks_section(tasks)}

{_build_verification(checks)}

<div class="footer"><span class="footer-leaf">🍃</span> Architecture Review 生成 &middot; {timestamp}</div>
</div>
</body>
</html>"""


def _build_kpi_section(kpi: dict) -> str:
    if not kpi:
        return ""
    items = kpi.get("items", [])
    if not items:
        return ""
    cells = "\n".join(
        f'<div class="kpi"><div class="kpi-label">{it["label"]}</div>'
        f'<div class="kpi-value {it.get("color", "kpi-blue")}">{it["value"]}</div></div>'
        for it in items
    )
    return f'<div class="summary">{cells}</div>'


def _build_conclusion(conclusion: dict) -> str:
    if not conclusion:
        return ""
    text = conclusion.get("text", "")
    next_step = conclusion.get("next", "")
    if not text:
        return ""
    border = conclusion.get("border", "var(--teal)")
    return (
        f'<div class="conclusion" style="border-left-color:{border}">'
        f'<div class="conclusion-text">{text}</div>'
        + (f'<div class="conclusion-next">{next_step}</div>' if next_step else "")
        + "</div>"
    )


def _build_layers_section(layers: list) -> str:
    if not layers:
        return ""
    sections = []
    for layer in layers:
        name = layer.get("name", "")
        level = layer.get("level", "")
        badge_class = f"layer-l{level}" if level else "layer-l1"
        modules = layer.get("modules", [])
        subs = layer.get("subgroups", [])
        comm_lines = layer.get("communication", [])

        cards = ""
        if modules:
            cards = '<div class="module-grid cols-auto">' + "\n".join(
                f'<div class="module-card" style="border-color:{m.get("color","#e8dcc8")}">'
                f'<div class="module-card-icon">{m.get("icon","")}</div>'
                f'<div class="module-card-name">{m.get("name","")}</div>'
                f'<div class="module-card-desc">{m.get("desc","")}</div>'
                + (f'<div class="module-card-endpoints">{m.get("endpoints","")}</div>' if m.get("endpoints") else "")
                + "</div>"
                for m in modules
            ) + "</div>"

        subs_html = ""
        if subs:
            subs_html = "\n".join(
                f'<div class="sub-group"><div class="sub-group-label">{sg["label"]}</div>'
                + (
                    f'<div class="module-grid cols-auto">'
                    + "\n".join(
                        f'<div class="module-card" style="border-color:{m.get("color","#e8dcc8")}">'
                        f'<div class="module-card-icon">{m.get("icon","")}</div>'
                        f'<div class="module-card-name">{m.get("name","")}</div>'
                        f'<div class="module-card-desc">{m.get("desc","")}</div>'
                        + (f'<div class="module-card-endpoints">{m.get("endpoints","")}</div>' if m.get("endpoints") else "")
                        + "</div>"
                        for m in sg.get("modules", [])
                    )
                    + "</div>"
                )
                + "</div>"
                for sg in subs
            )

        comm_html = ""
        if comm_lines:
            comm_html = '<div class="comm-line-group">' + "\n".join(
                f'<div class="comm-line"><span class="comm-dot comm-{cl.get("type","rest")}"></span>{cl.get("text","")}</div>'
                for cl in comm_lines
            ) + "</div>"

        sections.append(
            f'<div class="arch-layer">'
            f'<div class="arch-layer-title"><span class="layer-badge {badge_class}">{level}</span>{name}</div>'
            f'{cards}{subs_html}{comm_html}'
            f'</div>'
        )
    return f'<h2>🍃 理想架构图</h2>{"".join(sections)}'


def _build_gaps_section(gaps: list) -> str:
    if not gaps:
        return ""
    rows = "\n".join(
        f'<tr>'
        f'<td>{g.get("id","")}</td>'
        f'<td>{g.get("layer","")}</td>'
        f'<td><strong>{g.get("gap","")}</strong></td>'
        f'<td>{g.get("ideal","")}</td>'
        f'<td>{g.get("actual","")}</td>'
        f'<td class="{"fail" if g.get("severity")=="high" else "warn" if g.get("severity")=="medium" else ""}">'
        f'{g.get("severity_label","")}</td>'
        f'<td style="font-size:12px">{g.get("fix","")}</td>'
        f'</tr>'
        for g in gaps
    )
    return f"""<h2>🔍 差距对照表</h2>
<div class="table-wrap"><table>
<thead><tr><th>#</th><th>层</th><th>差距</th><th>理想</th><th>实际</th><th>严重度</th><th>修复</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>"""


def _build_tasks_section(tasks: list) -> str:
    if not tasks:
        return ""
    items = "\n".join(
        f'<li class="focus-item">'
        f'<span class="focus-prio prio-{t.get("priority","p2").lower()}">{t.get("priority","P2")}</span>'
        f'<div class="focus-body">'
        f'<div class="focus-title">{t.get("title","")}</div>'
        f'<div class="focus-desc">{t.get("desc","")}</div>'
        f'</div></li>'
        for t in tasks
    )
    return f'<h2>🛠️ 实施路线</h2><ul class="focus-list">{items}</ul>'


def _build_verification(checks: list) -> str:
    if not checks:
        return ""
    rows = "\n".join(
        f'<tr><td><code>{c.get("cmd","")}</code></td><td>{c.get("expect","")}</td></tr>'
        for c in checks
    )
    return f"""<h2>✅ 验证清单</h2>
<div class="table-wrap"><table>
<thead><tr><th>检查项</th><th>预期结果</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>"""


# ── Example data ──

EXAMPLE_DATA = {
    "title": "Android-AutoTests 架构审查报告",
    "subtitle": "理想架构 vs 实际架构 · 差距分析与实施建议",
    "kpi": {
        "items": [
            {"label": "目标模块数", "value": "7", "color": "kpi-blue"},
            {"label": "现有模块数", "value": "6", "color": "kpi-green"},
            {"label": "架构问题", "value": "5", "color": "kpi-red"},
            {"label": "实施周期", "value": "3d", "color": "kpi-yellow"},
        ]
    },
    "conclusion": {
        "text": "🏁 结论: 依赖方向正确（无循环），模块边界基本清晰。核心差距在 dashboard 错位、前端模块重叠、WebSocket 安全缺失。",
        "next": "下一步: 提取 dashboard 为独立 App → 合并 element-manager → 补齐 WebSocket JWT 认证",
    },
    "layers": [
        {
            "name": "前端展示层 — Vue 3 SPA :5173",
            "level": "L1",
            "modules": [
                {"icon": "📊", "name": "dashboard", "desc": "跨模块统计", "endpoints": "GET ×4", "color": "#f7cd67"},
                {"icon": "📱", "name": "device-pool", "desc": "设备连接/锁定", "endpoints": "12 端点", "color": "#6fba2c"},
                {"icon": "🔍", "name": "element-locator", "desc": "UI Dump/元素库", "endpoints": "11 端点", "color": "#b39ef3"},
                {"icon": "📋", "name": "case-manager", "desc": "用例定义/编辑", "endpoints": "5 端点", "color": "#19c8b9"},
                {"icon": "▶️", "name": "test-runner", "desc": "执行引擎", "endpoints": "6 端点", "color": "#f8a6b2"},
                {"icon": "📄", "name": "report-generator", "desc": "报告生成", "endpoints": "3 端点", "color": "#8b7355"},
                {"icon": "🤖", "name": "ai-assistant", "desc": "Agent/对话", "endpoints": "26 端点", "color": "#f7a8c4"},
            ],
            "communication": [
                {"type": "rest", "text": "HTTP REST + JWT Bearer"},
                {"type": "ws", "text": "WebSocket (截图流, 测试状态)"},
                {"type": "sse", "text": "SSE 流式对话 (AgentScope)"},
            ],
        },
        {
            "name": "API 网关层 — Django :8765",
            "level": "L2",
            "modules": [
                {"icon": "🔑", "name": "JWT Middleware", "desc": "Token 验证"},
                {"icon": "🔀", "name": "URL Router", "desc": "7 模块路由分发"},
                {"icon": "🔌", "name": "WS Router", "desc": "截图流 + 测试推送"},
            ],
        },
        {
            "name": "业务模块层 — 7 Django Apps",
            "level": "L3",
            "subgroups": [
                {
                    "label": "底层（零依赖）",
                    "modules": [
                        {"icon": "📱", "name": "device_pool", "desc": "设备注册/锁定/排队", "color": "#6fba2c"},
                        {"icon": "📄", "name": "report_generator", "desc": "报告生成/模板", "color": "#8b7355"},
                        {"icon": "📊", "name": "dashboard 🆕", "desc": "跨模块聚合统计", "color": "#f7cd67"},
                    ],
                },
                {
                    "label": "中层（单向依赖底层）",
                    "modules": [
                        {"icon": "🔍", "name": "element_locator", "desc": "→ device_pool (FK)", "color": "#b39ef3"},
                        {"icon": "📋", "name": "case_manager", "desc": "→ element_locator (FK)", "color": "#19c8b9"},
                        {"icon": "▶️", "name": "test_runner", "desc": "→ DP+CM+RG", "color": "#f8a6b2"},
                    ],
                },
                {
                    "label": "聚合层",
                    "modules": [
                        {"icon": "🤖", "name": "ai_assistant", "desc": "→ 5 Apps", "color": "#f7a8c4"},
                    ],
                },
            ],
            "communication": [
                {"type": "orm", "text": "Django ORM (同进程)"},
                {"type": "orm", "text": "api.py 白名单 (跨模块写)"},
            ],
        },
    ],
    "gaps": [
        {
            "id": 1, "layer": "L3", "gap": "Dashboard 职责错位",
            "ideal": "独立的 apps/dashboard/", "actual": "散落在 ai_assistant/dashboard_views.py",
            "severity": "high", "severity_label": "🔴 高",
            "fix": "新建 apps/dashboard/ → 迁移 views + urls",
        },
        {
            "id": 2, "layer": "L2", "gap": "WebSocket 无认证",
            "ideal": "connect() 验证 JWT", "actual": "直接 accept()",
            "severity": "high", "severity_label": "🔴 高",
            "fix": "consumers.py 添加 token 验证",
        },
        {
            "id": 3, "layer": "L1", "gap": "element-manager 重叠",
            "ideal": "element-locator 子视图", "actual": "独立前端模块",
            "severity": "medium", "severity_label": "🟠 中",
            "fix": "合并到 element-locator",
        },
    ],
    "tasks": [
        {
            "priority": "P0", "title": "提取 Dashboard 为独立 App",
            "desc": "新建 apps/dashboard/，从 ai_assistant 迁移 4 个统计视图，更新 config/urls.py",
        },
        {
            "priority": "P0", "title": "添加 WebSocket JWT 认证",
            "desc": "在 ScreenshotConsumer 和 TestRunConsumer 的 connect() 中验证 token",
        },
        {
            "priority": "P1", "title": "合并 element-manager → element-locator",
            "desc": "前端合并路由，将 element-manager/index.vue 迁移为 ElementManager.vue 子组件",
        },
    ],
    "verification": [
        {"cmd": "grep -r \"dashboard_views\" config/", "expect": "指向 apps.dashboard"},
        {"cmd": "grep -r \"element-manager\" frontend/src/router.js", "expect": "无匹配"},
        {"cmd": "python manage.py check", "expect": "0 issues"},
        {"cmd": "npx vite build --mode development", "expect": "✓ built"},
        {"cmd": "python run.py start", "expect": "4 服务 ONLINE"},
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Architecture Review Report Generator")
    parser.add_argument("--data", type=Path, help="JSON data file (uses example if omitted)")
    parser.add_argument("--output", type=Path, default=Path("architecture_review.html"),
                        help="Output HTML file path")
    args = parser.parse_args()

    if args.data:
        with open(args.data, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = EXAMPLE_DATA

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = _build_html(data, timestamp)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Report generated: {args.output.resolve()}")


if __name__ == "__main__":
    main()
