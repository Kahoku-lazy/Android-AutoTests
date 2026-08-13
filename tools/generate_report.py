"""Generate combined HTML test report with sidebar navigation.

Uses animal-island-ui design tokens. Self-contained single HTML file
with base64-embedded screenshots.

Usage:
    python tests/generate_report.py
"""

import base64
import io
import sys

from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCREENSHOT_DIR = Path(__file__).parent / "screenshots"

# ── Test case definitions ──
TEST_CASES = {
    "login": {
        "label": "登录页面",
        "icon": "🔑",
        "color": "#6fba2c",
        "steps": [
            {
                "file": "01_login_page_loaded.png",
                "title": "Step 1: 打开登录页面",
                "selector": "—",
                "action": "navigate",
                "desc": "浏览器导航到 <code>/login</code>，等待页面完全加载（networkidle）。",
                "expected": "页面显示登录卡片，包含用户名、密码输入框和登录按钮",
            },
            {
                "file": "02_username_filled.png",
                "title": "Step 2: 输入用户名",
                "selector": 'input[placeholder="账号"]',
                "action": "fill",
                "desc": "定位用户名输入框，填入 <code>admin</code>。红点标注输入框中心位置。",
                "expected": "输入框显示 'admin'",
            },
            {
                "file": "03_password_filled.png",
                "title": "Step 3: 输入密码",
                "selector": '.login-form input[type="password"]',
                "action": "fill",
                "desc": "定位密码输入框，填入密码。红点标注输入框中心。",
                "expected": "密码框显示圆点占位符",
            },
            {
                "file": "04_remember_toggled.png",
                "title": "Step 4: 切换记住账号",
                "selector": ".form-remember .el-switch",
                "action": "click",
                "desc": "点击开关组件，切换「记住账号」状态。红点标注开关中心。",
                "expected": "开关变为激活状态",
            },
            {
                "file": "05_after_login_click.png",
                "title": "Step 5: 点击登录按钮",
                "selector": 'text="开始使用"',
                "action": "click",
                "desc": "点击按钮提交表单。红点标注按钮中心。等待 1.5 秒观察跳转。",
                "expected": "跳转到 /dashboard 仪表盘页面",
            },
        ],
    },
    "register": {
        "label": "注册页面",
        "icon": "📝",
        "color": "#19c8b9",
        "steps": [
            {
                "file": "01_login_page_loaded.png",
                "title": "Step 1: 打开登录页面",
                "selector": "—",
                "action": "navigate",
                "desc": "浏览器导航到 <code>/login?add=1</code>，跳过已登录账号切换提示。",
                "expected": "页面显示登录卡片",
            },
            {
                "file": "02_switched_to_register.png",
                "title": "Step 2: 切换到注册模式",
                "selector": 'text="去注册"',
                "action": "click",
                "desc": "点击「去注册」链接切换到注册模式。红点标注链接位置。",
                "expected": "卡片切换为注册表单，显示 3 个输入框",
            },
            {
                "file": "03_username_filled.png",
                "title": "Step 3: 输入注册用户名",
                "selector": 'input[placeholder*="设置账号"]',
                "action": "fill",
                "desc": "定位用户名输入框，填入随机生成的用户名。",
                "expected": "输入框显示生成的用户名",
            },
            {
                "file": "04_password_filled.png",
                "title": "Step 4: 输入注册密码",
                "selector": '.login-form input[placeholder*="设置密码"]',
                "action": "fill",
                "desc": "定位密码输入框，填入密码（>=6位）。",
                "expected": "密码框显示圆点占位符",
            },
            {
                "file": "05_confirm_password_filled.png",
                "title": "Step 5: 确认密码",
                "selector": 'input[placeholder="确认密码"]',
                "action": "fill",
                "desc": "定位确认密码输入框，填入相同密码。两次输入必须一致。",
                "expected": "确认密码框已填入，注册按钮变为可点击",
            },
            {
                "file": "06_after_register_click.png",
                "title": "Step 6: 点击注册按钮",
                "selector": 'text="完成注册"',
                "action": "click",
                "desc": "点击按钮提交表单。红点标注按钮中心。",
                "expected": "显示绿色成功提示，0.6 秒后跳转 dashboard",
            },
        ],
    },
}


def img_to_b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def find_latest_run(name: str) -> dict:
    d = SCREENSHOT_DIR / name
    if not d.exists():
        return None
    runs = sorted([x for x in d.iterdir() if x.is_dir()], key=lambda x: x.name, reverse=True)
    return {"dir": runs[0], "time": runs[0].name} if runs else None


def collect_test_data():
    """Gather all test case data with base64 images."""
    cases = []
    for key, cfg in TEST_CASES.items():
        run = find_latest_run(key)
        if not run:
            continue
        steps = []
        for s in cfg["steps"]:
            img_path = run["dir"] / s["file"]
            steps.append(
                {
                    **s,
                    "has_image": img_path.exists(),
                    "b64": img_to_b64(img_path) if img_path.exists() else None,
                }
            )
        cases.append(
            {
                "key": key,
                "label": cfg["label"],
                "icon": cfg["icon"],
                "color": cfg["color"],
                "run_time": run["time"],
                "steps": steps,
                "total": len(steps),
                "captured": sum(1 for s in steps if s["has_image"]),
            }
        )
    return cases


def build_html(cases: list) -> str:
    # Build sidebar items
    sidebar_items = ""
    for i, c in enumerate(cases):
        active = "active" if i == 0 else ""
        sidebar_items += f"""
        <li class="nav-item {active}" data-case="{c["key"]}" onclick="switchCase('{c["key"]}')">
            <span class="nav-icon">{c["icon"]}</span>
            <div class="nav-text">
                <span class="nav-label">{c["label"]}</span>
                <span class="nav-meta">{c["captured"]}/{c["total"]} screenshots</span>
            </div>
            <span class="nav-badge" style="background:{c["color"]}">{c["captured"]}/{c["total"]}</span>
        </li>"""

    # Build case panels
    case_panels = ""
    for ci, c in enumerate(cases):
        active = "active" if ci == 0 else ""
        steps_html = ""
        for i, s in enumerate(c["steps"]):
            status_cls = "pass" if s["has_image"] else "missing"
            img_tag = ""
            if s["b64"]:
                img_tag = f'<div class="screenshot-wrap"><img src="data:image/png;base64,{s["b64"]}" alt="{s["title"]}" onclick="this.classList.toggle(\'zoomed\')" loading="lazy" /></div>'
            else:
                img_tag = '<div class="screenshot-wrap missing"><p>No screenshot</p></div>'

            steps_html += f"""
            <div class="step-card {status_cls}">
                <div class="step-header">
                    <span class="step-num">{i + 1}</span>
                    <div class="step-title-group">
                        <h3>{s["title"]}</h3>
                        <div class="step-meta">
                            <span class="meta-tag">{s["action"].upper()}</span>
                            <code>{s["selector"]}</code>
                        </div>
                    </div>
                </div>
                <div class="step-body">
                    <p class="step-desc">{s["desc"]}</p>
                    <p class="step-expected"><strong>Expected:</strong> {s["expected"]}</p>
                </div>
                {img_tag}
            </div>"""

        case_panels += f"""
        <div class="case-panel {active}" id="panel-{c["key"]}">
            <div class="case-header">
                <h2>{c["icon"]} {c["label"]}</h2>
                <span class="case-meta">Run: {c["run_time"]} &middot; {c["captured"]}/{c["total"]} screenshots</span>
            </div>
            {steps_html}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Web UI Test Report — Login &amp; Register</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {{
    --primary: #19c8b9; --primary-hover: #3dd4c6; --primary-active: #11a89b; --primary-bg: #e6f9f6;
    --text: #794f27; --text-body: #725d42; --text-secondary: #9f927d; --text-muted: #8a7b66; --text-disabled: #c4b89e;
    --bg: #f8f8f0; --bg-content: rgb(247,243,223); --bg-disabled: #f0ece2;
    --border: #c4b89e; --border-hover: #a89878; --border-strong: #9f927d;
    --success: #6fba2c; --success-active: #5a9e1e; --warning: #f5c31c; --error: #e05a5a; --error-active: #c94444;
    --focus-yellow: #ffcc00; --r-sm: 12px; --r-base: 18px; --r-lg: 24px; --r-pill: 50px;
    --ease: cubic-bezier(0.4, 0, 0.2, 1); --d-fast: 0.15s; --d-base: 0.25s; --d-slow: 0.35s;
    --shadow-btn: #bdaea0; --shadow-input: #d4c9b4;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: Nunito, 'Noto Sans SC', -apple-system, 'PingFang SC', sans-serif;
    font-weight: 500; letter-spacing: 0.01em; background: var(--bg); color: var(--text-body);
    line-height: 1.6; display: flex; min-height: 100vh;
}}
/* ── Sidebar ── */
.sidebar {{
    width: 260px; min-width: 260px; background: #fff; border-right: 1px solid var(--border);
    padding: 24px 0; display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh;
    overflow-y: auto; box-shadow: 0 2px 12px rgba(61,52,40,0.04);
}}
.sidebar-header {{
    padding: 0 20px 20px; border-bottom: 1px dashed var(--border); margin-bottom: 8px;
}}
.sidebar-header h1 {{ font-size: 18px; font-weight: 800; color: var(--text); letter-spacing: 0.02em; }}
.sidebar-header .sub {{ font-size: 11px; color: var(--text-secondary); margin-top: 2px; }}
.nav-list {{ list-style: none; padding: 8px 12px; }}
.nav-item {{
    display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-radius: var(--r-sm);
    cursor: pointer; transition: background var(--d-fast) var(--ease), transform var(--d-fast) var(--ease);
    margin-bottom: 4px; border: 1.5px solid transparent;
}}
.nav-item:hover {{ background: var(--primary-bg); transform: translateX(2px); }}
.nav-item.active {{ background: var(--primary-bg); border-color: var(--primary); font-weight: 600; }}
.nav-icon {{ font-size: 22px; flex-shrink: 0; }}
.nav-text {{ flex: 1; min-width: 0; }}
.nav-label {{ display: block; font-size: 14px; font-weight: 600; color: var(--text); letter-spacing: 0.02em; }}
.nav-meta {{ display: block; font-size: 11px; color: var(--text-secondary); margin-top: 1px; }}
.nav-badge {{ font-size: 10px; font-weight: 700; color: #fff; padding: 2px 8px; border-radius: var(--r-pill); flex-shrink: 0; letter-spacing: 0.02em; }}
.sidebar-footer {{ margin-top: auto; padding: 16px 20px 0; border-top: 1px dashed var(--border); font-size: 11px; color: var(--text-secondary); }}
/* ── Main ── */
.main {{ flex: 1; padding: 32px 40px; overflow-y: auto; max-height: 100vh; }}
.case-panel {{ display: none; }}
.case-panel.active {{ display: block; animation: fadeIn var(--d-base) var(--ease); }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.case-header {{ margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid var(--primary); }}
.case-header h2 {{ font-size: 24px; font-weight: 800; color: var(--text); letter-spacing: 0.02em; }}
.case-meta {{ font-size: 12px; color: var(--text-secondary); }}
/* ── Summary banner ── */
.summary-row {{ display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }}
.summary-card {{ flex: 1; min-width: 120px; background: #fff; border-radius: var(--r-base); padding: 18px 20px;
    border-left: 4px solid var(--primary); box-shadow: 0 2px 8px rgba(61,52,40,0.03); }}
.summary-card .num {{ font-size: 28px; font-weight: 900; color: var(--text); letter-spacing: 0.02em; }}
.summary-card .lbl {{ font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; margin-top: 2px; }}
/* ── Step cards ── */
.step-card {{ background: #fff; border-radius: var(--r-base); margin-bottom: 20px; overflow: hidden;
    border: 1.5px solid var(--border); transition: box-shadow var(--d-base) var(--ease); }}
.step-card:hover {{ box-shadow: 0 4px 16px rgba(61,52,40,0.06); }}
.step-card.pass {{ border-left: 4px solid var(--success); }}
.step-card.missing {{ border-left: 4px solid var(--warning); opacity: 0.85; }}
.step-header {{ display: flex; align-items: flex-start; gap: 14px; padding: 18px 20px 12px; }}
.step-num {{ width: 32px; height: 32px; border-radius: 50%; background: var(--primary); color: #fff;
    display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800;
    flex-shrink: 0; letter-spacing: 0.02em; }}
.step-card.missing .step-num {{ background: var(--warning); color: #5a4a20; }}
.step-title-group {{ flex: 1; }}
.step-title-group h3 {{ font-size: 16px; font-weight: 700; color: var(--text); letter-spacing: 0.02em; margin-bottom: 4px; }}
.step-meta {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
.meta-tag {{ display: inline-block; padding: 2px 10px; border-radius: var(--r-pill); font-size: 10px;
    font-weight: 700; color: #fff; background: var(--primary); letter-spacing: 0.04em; }}
.step-meta code {{ font-family: 'SF Mono','Fira Code',Consolas,monospace; font-weight: 600; font-size: 12px;
    background: var(--bg); padding: 2px 8px; border-radius: 6px; color: var(--text-muted); }}
.step-body {{ padding: 0 20px 14px; }}
.step-desc {{ font-size: 14px; color: var(--text-body); margin-bottom: 4px; }}
.step-expected {{ font-size: 13px; color: var(--success); font-weight: 500; }}
.screenshot-wrap {{ border-radius: var(--r-sm); overflow: hidden; margin: 0 20px 18px;
    border: 1.5px solid var(--border); cursor: pointer; }}
.screenshot-wrap img {{ width: 100%; display: block; transition: transform var(--d-slow) var(--ease); }}
.screenshot-wrap img.zoomed {{ transform: scale(1.8); transform-origin: top left; box-shadow: 0 20px 60px rgba(61,52,40,0.2); z-index: 100; position: relative; }}
.screenshot-wrap.missing {{ background: var(--bg-disabled); display: flex; align-items: center;
    justify-content: center; min-height: 140px; color: var(--text-disabled); font-size: 14px; }}
/* ── Responsive ── */
@media (max-width: 768px) {{
    body {{ flex-direction: column; }}
    .sidebar {{ width: 100%; min-width: 0; height: auto; position: static; flex-direction: row;
        overflow-x: auto; padding: 12px; gap: 8px; }}
    .nav-list {{ display: flex; gap: 6px; padding: 0; }}
    .nav-item {{ flex: 1; min-width: 120px; flex-direction: column; text-align: center; padding: 10px; }}
    .main {{ padding: 20px 16px; max-height: none; }}
    .sidebar-header, .sidebar-footer {{ display: none; }}
}}
@media print {{
    .sidebar {{ display: none; }}
    .main {{ max-height: none; padding: 0; }}
    .case-panel {{ display: block !important; }} .case-panel.active {{ display: block !important; }}
    .step-card {{ break-inside: avoid; box-shadow: none; }}
    .screenshot-wrap {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
<aside class="sidebar">
    <div class="sidebar-header">
        <h1>Web UI Test Report</h1>
        <p class="sub">Playwright &middot; Chromium &middot; {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    <ul class="nav-list">{sidebar_items}</ul>
    <div class="sidebar-footer">AI Automated Testing Platform</div>
</aside>
<main class="main">
    <div class="summary-row">
        {"".join(f'<div class="summary-card"><div class="num">{c["captured"]}/{c["total"]}</div><div class="lbl">{c["label"]} Screenshots</div></div>' for c in cases)}
        <div class="summary-card"><div class="num">{sum(c["captured"] for c in cases)}</div><div class="lbl">Total Captured</div></div>
    </div>
    {case_panels}
</main>
<script>
function switchCase(key) {{
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`.nav-item[data-case="${{key}}"]`)?.classList.add('active');
    document.querySelectorAll('.case-panel').forEach(el => el.classList.remove('active'));
    document.getElementById(`panel-${{key}}`)?.classList.add('active');
}}
</script>
</body>
</html>"""


def main():
    cases = collect_test_data()
    if not cases:
        print("No screenshot data found. Run test scripts first:")
        print("  python tests/test_web_login.py")
        print("  python tests/test_web_register.py")
        return

    html = build_html(cases)
    out_path = SCREENSHOT_DIR / "report_combined.html"
    out_path.write_text(html, encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Combined report: {out_path}")
    print(
        f"     {len(cases)} test cases, {sum(c['captured'] for c in cases)} screenshots embedded, {size_mb:.1f} MB"
    )
    for c in cases:
        print(f"     - {c['icon']} {c['label']}: {c['captured']}/{c['total']} images")


if __name__ == "__main__":
    main()
