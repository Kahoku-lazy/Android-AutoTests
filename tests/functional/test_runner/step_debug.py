"""场景：单步调试（浏览器）— 真机清单第 6 项（pool.ad/u2d 兼容面 + 协议链）。"""

import time

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
ART = Path(__file__).resolve().parent / "artifacts"
CASE_ID = "TC-20260717-111221-7527"

pw = sync_playwright().start()
try:
    b = pw.chromium.launch(headless=False)
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.set_default_timeout(30000)
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')")
    page.goto(f"{BASE}/cases/{CASE_ID}/edit", wait_until="load")
    page.wait_for_selector(
        '.el-select:has-text("选择调试设备"), input[placeholder="选择调试设备"]', timeout=60000
    )
    page.wait_for_timeout(1500)

    # 选调试设备
    page.click('.el-select:has-text("选择调试设备") .el-select__wrapper')
    page.wait_for_selector(".el-select-dropdown:visible")
    page.click(
        '.el-select-dropdown:visible .el-select-dropdown__item:has-text("SM-G9730")', force=True
    )
    print("[OK] 选择调试设备 SM-G9730")

    # 连接设备（observe 模式）
    page.click('button:has-text("连接设备")')
    page.wait_for_function(
        "() => { const b=[...document.querySelectorAll('button')].find(x=>x.innerText.includes('连接设备')); return !b; }",
        timeout=30000,
    )
    print("[OK] 调试设备已连接")

    # 第一步 ▶ 单步执行（adb_start_app com.govee.home → 真机启动）
    run_btn = page.locator('button[title="单步执行"]').first
    run_btn.click()
    print("[OK] 已点击第 1 步单步执行")
    deadline = time.time() + 60
    step_done = False
    while time.time() < deadline:
        body = page.inner_text("body")
        if "通过" in body or "✓" in body or "成功" in body:
            step_done = True
            break
        page.wait_for_timeout(2000)
    print(f"[结果标记] {'通过/成功 出现' if step_done else '未检测到结果标记'}")
    page.screenshot(path=str(ART / "13-step-debug.png"), full_page=True)

    # 步骤行附近文本
    rows = page.locator(".step-row, [class*=step]").all_inner_texts()
    hit = [r for r in rows if "adb_start_app" in r or "com.govee" in r]
    print("[步骤行] " + (hit[0].replace("\n", " | ")[:200] if hit else "未定位到步骤行"))
    b.close()
finally:
    pw.stop()
