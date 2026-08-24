"""场景：inspector 抓快照（浏览器）— 真机清单第 5 项（Step 2 算法下沉 + Step 4 会话链）。"""

import json
import urllib.request

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
ART = Path(__file__).resolve().parent / "artifacts"


def api(path, token):
    req = urllib.request.Request("http://127.0.0.1:8766" + path)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def main():
    import json as _json

    req = urllib.request.Request("http://127.0.0.1:8766/api/auth/login", method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(
        req, data=_json.dumps({"username": "admin", "password": "admin123"}).encode()
    ) as r:
        token = _json.loads(r.read().decode())["data"]["access_token"]

    before = api("/api/inspector/snapshots?offset=0&limit=1", token)
    before_count = before.get("count", before.get("total", "?"))

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
        page.goto(BASE + "/inspector", wait_until="networkidle")
        page.wait_for_selector('[data-testid="capture-device-select"]')
        page.wait_for_timeout(1500)

        # 选设备
        page.click('[data-testid="capture-device-select"] .el-select__wrapper')
        page.wait_for_selector(".el-select-dropdown:visible")
        page.click(
            '.el-select-dropdown:visible .el-select-dropdown__item:has-text("SM-G9730")', force=True
        )
        print("[OK] 选择设备 SM-G9730（默认方法 Dump+OCR）")

        # 抓取
        page.click('[data-testid="capture-btn"]')
        page.wait_for_selector(".filter-bar", timeout=90000)  # store.snapshot 就绪后出现
        print("[OK] 快照就绪")

        # 元素计数与 OCR 文本
        info = page.locator("text=/\\d+\\/\\d+ 元素/").first.inner_text(timeout=5000)
        print(f"[元素计数] {info}")
        body = page.inner_text("body")
        ocr_hint = "OCR" in body or "ocr" in body.lower()
        print(f"[含 OCR 区域文本] {ocr_hint}")
        page.screenshot(path=str(ART / "11-inspector-snapshot.png"), full_page=True)

        after = api("/api/inspector/snapshots?offset=0&limit=1", token)
        after_count = after.get("count", after.get("total", "?"))
        print(f"[快照计数] before={before_count} after={after_count}")
        b.close()
    finally:
        pw.stop()


if __name__ == "__main__":
    main()
