"""真机复验 #4：连接调试设备（observe）→ 路由离开 → 设备应恢复 ONLINE。"""

import json
import urllib.request

from playwright.sync_api import sync_playwright

CASE_ID = "TC-20260717-111221-7527"
DEVICE = "SM-G9730"
SERIAL = "RF8N21MSW7A"


def api(path, token, method="GET"):
    req = urllib.request.Request("http://127.0.0.1:8766" + path, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def login():
    req = urllib.request.Request("http://127.0.0.1:8766/api/auth/login", method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(
        req, data=json.dumps({"username": "admin", "password": "admin123"}).encode()
    ) as r:
        return json.loads(r.read().decode())["data"]["access_token"]


def device_status(token):
    resp = api("/api/devices", token)
    dev = next((d for d in resp["data"]["devices"] if d["serial"] == SERIAL), None)
    return (dev or {}).get("status"), (dev or {}).get("occupied_by")


token = login()
print("初始:", device_status(token))

pw = sync_playwright().start()
try:
    b = pw.chromium.launch(headless=False)
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.set_default_timeout(30000)

    def on_request(req):
        if "disconnect-observe" in req.url:
            print(f"[请求观测] {req.method} {req.url}")

    page.on("request", on_request)
    page.goto("http://localhost:5173/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')")
    page.goto(f"http://localhost:5173/cases/{CASE_ID}/edit", wait_until="load")
    page.wait_for_selector('.el-select:has-text("选择调试设备")', timeout=60000)
    # HMR 下 keep-alive 缓存旧模块 → 硬刷新确保加载 onDeactivated 钩子的新代码
    page.reload(wait_until="load")
    page.wait_for_selector('.el-select:has-text("选择调试设备")', timeout=60000)
    page.wait_for_timeout(1500)
    page.click('.el-select:has-text("选择调试设备") .el-select__wrapper')
    page.wait_for_selector(".el-select-dropdown:visible")
    page.click(
        f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{DEVICE}")', force=True
    )
    page.click('button:has-text("连接设备")')
    page.wait_for_timeout(8000)
    print("连接后:", device_status(token))

    # SPA 内部导航（点击侧边栏）→ 触发 keep-alive deactivated（真实用户路径）
    page.click("text=仪表盘")
    page.wait_for_timeout(5000)
    print("路由离开后:", device_status(token))
    b.close()
finally:
    pw.stop()
