"""场景：无线连接（浏览器）— 真机清单第 3 项。

用例 A：有效地址 10.162.95.96:46561（已在 adb，SM-S9010）→ 连接成功路径
用例 B：无效地址 10.162.95.96:59999 → 失败文案（不暴露技术术语）
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
ART = Path(__file__).resolve().parent / "artifacts"

MESSAGES = []


def run(page):
    page.set_default_timeout(30000)
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')")
    page.goto(BASE + "/devices", wait_until="networkidle")
    page.wait_for_selector('button:has-text("局域网")', timeout=20000)
    page.wait_for_timeout(2000)

    def capture_message():
        # Element Plus ElMessage 文本
        try:
            msg = page.locator(".el-message").last.inner_text(timeout=3000)
            MESSAGES.append(msg)
            print(f"[ElMessage] {msg}")
        except Exception:
            pass

    # ── 用例 A：有效无线设备 ──
    page.click('button:has-text("局域网")')
    page.wait_for_selector('.el-dialog:has-text("局域网连接设备")')
    page.fill('.el-dialog input[placeholder="如 192.168.1.100"]', "10.162.95.96")
    page.fill('.el-dialog input[placeholder="默认 5555"]', "46561")
    page.screenshot(path=str(ART / "09-net-dialog-valid.png"), full_page=True)
    page.click('.el-dialog button:has-text("连接")')
    page.wait_for_timeout(4000)
    capture_message()
    # 关闭可能还开着的弹窗
    try:
        page.locator('.el-dialog:visible button:has-text("取消")').first.click(timeout=2000)
    except Exception:
        pass
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)

    # ── 用例 B：无效地址 ──
    page.click('button:has-text("局域网")')
    page.wait_for_selector('.el-dialog:has-text("局域网连接设备")')
    page.fill('.el-dialog input[placeholder="如 192.168.1.100"]', "10.162.95.96")
    page.fill('.el-dialog input[placeholder="默认 5555"]', "59999")
    page.click('.el-dialog button:has-text("连接")')
    page.wait_for_timeout(6000)
    capture_message()
    page.screenshot(path=str(ART / "10-net-dialog-invalid.png"), full_page=True)

    print("[结果] " + " | ".join(MESSAGES))


with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    run(page)
    b.close()
