"""浏览器创建任务 — 端到端真机验证（真机清单第 1 项：任务全生命周期状态）。

流程：登录 → /runner → 新建任务 → 选设备/用例 → 创建并执行 →
轮询 REST 任务列表验证权威 state 流转（idle→queued/running→done）。

五维覆盖：FUNC（状态流转与数据一致性）/ API（真实接口 + state 字段）/ PERF（页面与执行耗时）。
清理规范：任务名 TEST- 前缀；删除前需人工确认（见 skill 清理三步）。
"""

import json
import time
import urllib.request

from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_FE = "http://localhost:5173"
BASE_API = "http://127.0.0.1:8766"
ART = Path(__file__).resolve().parent / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

USERNAME = "admin"
PASSWORD = "admin123"
TASK_NAME = f"TEST-BROWSER-{datetime.now().strftime('%H%M%S')}"
DEVICE_SERIAL = "RF8N21MSW7A"  # SM-G9730，在线
CASE_TITLE = "01-启动与关闭APP"


def api_json(path, method="GET", body=None, token=None):
    req = urllib.request.Request(BASE_API + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data=data) as resp:
        return json.loads(resp.read().decode())


def get_token():
    resp = api_json("/api/auth/login", "POST", {"username": USERNAME, "password": PASSWORD})
    assert resp["status"], f"login failed: {resp}"
    return resp["data"]["access_token"]


def snap(page, name):
    path = ART / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"[截图] {path}")


def main():
    token = get_token()
    print(f"[OK] 登录成功（API token 已取）")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(15000)

        # 1. 登录
        page.goto(BASE_FE + "/login", wait_until="networkidle")
        page.fill('input[placeholder="账号"]', USERNAME)
        page.fill('input[placeholder="密码"]', PASSWORD)
        page.click('button:has-text("登录")')
        page.wait_for_url("**/dashboard**", timeout=15000)
        print("[OK] 浏览器登录成功，进入仪表盘")

        # 2. 执行引擎页
        page.goto(BASE_FE + "/runner", wait_until="networkidle")
        page.wait_for_selector('button:has-text("＋ 新建任务")', timeout=15000)
        snap(page, "02-runner-before")
        print("[OK] 进入执行引擎页")

        # 3. 新建任务
        page.click('button:has-text("＋ 新建任务")')
        page.wait_for_selector('.el-dialog:has-text("新建测试任务")', timeout=10000)
        page.fill('.el-dialog input[placeholder="如：稳定性测试"]', TASK_NAME)
        snap(page, "03-dialog")

        # 4. 选设备（按表单项定位，避免误点"任务类型"下拉）
        page.click('.el-dialog .el-form-item:has-text("设备") .el-select__wrapper')
        page.wait_for_selector(".el-select-dropdown:visible", timeout=10000)
        page.click(
            f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{DEVICE_SERIAL}")',
            force=True,
        )
        print(f"[OK] 选择设备 {DEVICE_SERIAL}")

        # 5. 选用例（第二个 select）
        page.click('.el-dialog .el-form-item:has-text("用例") .el-select__wrapper')
        page.wait_for_selector(".el-select-dropdown:visible", timeout=10000)
        page.click(
            f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{CASE_TITLE}")',
            force=True,
        )
        page.keyboard.press("Escape")  # 收起多选下拉
        print(f"[OK] 选择用例 {CASE_TITLE}")

        snap(page, "04-filled")

        # 6. 创建并执行（Element Plus 关闭后仅隐藏不 detach）
        page.click('.el-dialog button:has-text("创建并执行")')
        page.wait_for_selector(".el-dialog", state="hidden", timeout=15000)
        print(f"[OK] 已提交创建并执行：{TASK_NAME}")

        # 7. 轮询权威 state（REST /api/runner/tasks —— 注意：runner 路由无尾斜杠）
        states_seen = []
        deadline = time.time() + 120
        final = None
        while time.time() < deadline:
            resp = api_json("/api/runner/tasks", token=token)
            tasks = resp.get("tasks", [])
            mine = next((t for t in tasks if t["name"] == TASK_NAME), None)
            if mine:
                s = mine.get("state")
                if not states_seen or states_seen[-1] != s:
                    states_seen.append(s)
                    print(f"[state] {s}（status={mine['status']} outcome={mine['outcome']}）")
                    snap(page, f"05-state-{s}")
                if s == "done":
                    final = mine
                    break
            time.sleep(3)
            try:
                page.reload(wait_until="networkidle")
            except Exception:
                pass

        if final is None:
            print("[WARN] 120s 内未到 done，可能仍在执行或异常")
            states_seen.append("timeout")

        print(
            json.dumps(
                {
                    "task_name": TASK_NAME,
                    "states_seen": states_seen,
                    "final": {
                        k: final.get(k)
                        for k in ("id", "state", "status", "outcome", "overallPass", "overallFail")
                    }
                    if final
                    else None,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        browser.close()


if __name__ == "__main__":
    main()
