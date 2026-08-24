"""诊断 inspector capture 失败：API 快照计数 + 页面 ElMessage + 按钮状态 + 截图。"""

import json
import urllib.request

from pathlib import Path

from playwright.sync_api import sync_playwright

ART = Path(__file__).resolve().parent / "artifacts"


def login_token():
    req = urllib.request.Request("http://127.0.0.1:8766/api/auth/login", method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(
        req, data=json.dumps({"username": "admin", "password": "admin123"}).encode()
    ) as r:
        return json.loads(r.read().decode())["data"]["access_token"]


token = login_token()
req = urllib.request.Request("http://127.0.0.1:8766/api/inspector/snapshots?offset=0&limit=3")
req.add_header("Authorization", f"Bearer {token}")
with urllib.request.urlopen(req) as r:
    snaps = json.loads(r.read().decode())
print("[snapshots 响应键]", list(snaps.keys()))
print(json.dumps(snaps, ensure_ascii=False)[:500])

pw = sync_playwright().start()
try:
    b = pw.chromium.launch(headless=False)
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.set_default_timeout(30000)
    page.goto("http://localhost:5173/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')")
    page.goto("http://localhost:5173/inspector", wait_until="networkidle")
    page.wait_for_selector('[data-testid="capture-device-select"]')
    page.wait_for_timeout(1500)
    btn = page.locator('[data-testid="capture-btn"]')
    print("[capture 按钮 disabled]", btn.is_disabled())
    print("[capture 按钮文本]", btn.inner_text())
    page.click('[data-testid="capture-device-select"] .el-select__wrapper')
    page.wait_for_selector(".el-select-dropdown:visible")
    page.click(
        '.el-select-dropdown:visible .el-select-dropdown__item:has-text("SM-G9730")', force=True
    )
    page.wait_for_timeout(800)
    print("[选后按钮 disabled]", page.locator('[data-testid="capture-btn"]').is_disabled())
    page.click('[data-testid="capture-btn"]')
    page.wait_for_timeout(20000)
    msgs = page.locator(".el-message").all_inner_texts()
    print("[ElMessage]", msgs[-3:] if msgs else "无")
    err = page.locator(".el-message--error").all_inner_texts()
    print("[错误消息]", err if err else "无")
    body = page.inner_text("body")
    idx = body.find("快照")
    print("[快照相关文本]", body[idx : idx + 120].replace("\n", " | ") if idx >= 0 else "无")
    page.screenshot(path=str(ART / "12-inspector-diag.png"), full_page=True)
    b.close()
finally:
    pw.stop()
