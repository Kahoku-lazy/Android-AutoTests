"""场景：停止/中断流（浏览器全自动）— 真机清单第 2 项。

流程：登录 → 新建任务（loop=20 拉长执行）→ 创建并执行 → 运行中点击「停止」
→ 确认 → 轮询 state/outcome 应为 done/stopped → 看板显示「已停止」。
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
TASK_NAME = f"TEST-STOP-{datetime.now().strftime('%H%M%S')}"
DEVICE = "RF8N21MSW7A"
CASE = "01-启动与关闭APP"


def api(path, method="GET", body=None, token=None):
    req = urllib.request.Request(BASE_API + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data=data) as r:
        return json.loads(r.read().decode())


def get_task(token, name):
    resp = api("/api/runner/tasks", token=token)
    return next((t for t in resp.get("tasks", []) if t["name"] == name), None)


def main():
    token = api("/api/auth/login", "POST", {"username": "admin", "password": "admin123"})["data"][
        "access_token"
    ]

    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.set_default_timeout(20000)
        page.goto(BASE_FE + "/login", wait_until="networkidle")
        page.fill('input[placeholder="账号"]', "admin")
        page.fill('input[placeholder="密码"]', "admin123")
        page.click('button:has-text("登录")')
        page.wait_for_function("!location.pathname.startsWith('/login')", timeout=30000)
        page.goto(BASE_FE + "/runner", wait_until="networkidle")
        page.wait_for_selector('button:has-text("＋ 新建任务")')
        page.click('button:has-text("＋ 新建任务")')
        page.wait_for_selector('.el-dialog:has-text("新建测试任务")')
        page.fill('.el-dialog input[placeholder="如：稳定性测试"]', TASK_NAME)
        # loop=20（拉长执行窗口）
        page.fill(".el-dialog .el-input-number input", "20")
        page.click('.el-dialog .el-form-item:has-text("设备") .el-select__wrapper')
        page.wait_for_selector(".el-select-dropdown:visible")
        page.click(
            f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{DEVICE}")',
            force=True,
        )
        page.click('.el-dialog .el-form-item:has-text("用例") .el-select__wrapper')
        page.wait_for_selector(".el-select-dropdown:visible")
        page.click(
            f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{CASE}")', force=True
        )
        page.keyboard.press("Escape")
        page.screenshot(path=str(ART / "07-stop-before-submit.png"), full_page=True)
        page.click('.el-dialog button:has-text("创建并执行")')
        page.wait_for_selector(".el-dialog", state="hidden", timeout=20000)
        print(f"[OK] 已提交 {TASK_NAME}（loop=20）")

        # 等 running
        deadline = time.time() + 60
        task = None
        while time.time() < deadline:
            task = get_task(token, TASK_NAME)
            if task and task["state"] == "running":
                break
            time.sleep(2)
        assert task and task["state"] == "running", f"未进入 running: {task}"
        run_id = task.get("runId", "")
        print(f"[OK] state=running runId={run_id}")

        # 浏览器点击行内「停止」→ 确认
        page.reload(wait_until="networkidle")
        page.wait_for_selector('button:has-text("＋ 新建任务")')
        page.wait_for_timeout(1500)
        row = page.locator("tr", has_text=TASK_NAME)
        assert row.count(), "任务行未渲染"
        row.locator('button:has-text("停止")').click()
        # ConfirmButton 确认弹层
        try:
            page.locator(
                '.el-popper:visible button:has-text("确认"), .el-popconfirm button:has-text("确定"), [class*=confirm]:visible button:has-text("停止")'
            ).first.click(timeout=8000)
        except Exception:
            page.locator('button:has-text("确定"), button:has-text("确认")').last.click(
                timeout=8000
            )
        print("[OK] 已点击停止并确认")

        # 轮询终态
        deadline = time.time() + 60
        while time.time() < deadline:
            task = get_task(token, TASK_NAME)
            if task and task["state"] == "done":
                break
            time.sleep(2)
        print(
            json.dumps(
                {
                    "task": TASK_NAME,
                    "state": task["state"],
                    "status": task["status"],
                    "outcome": task["outcome"],
                    "runId": run_id,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        # UI 展示验证（已完成桶 → 已停止标签）
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(2500)
        page.locator(
            '.filter-tab:has-text("已完成"), [class*="tab"]:has-text("已完成")'
        ).first.click()
        page.wait_for_timeout(1500)
        rows = page.locator(".el-table__row").all_inner_texts()
        mine = [r for r in rows if TASK_NAME in r]
        print("[UI 行] " + (mine[0].replace("\n", " | ")[:200] if mine else "未找到"))
        page.screenshot(path=str(ART / "08-stop-final.png"), full_page=True)
        b.close()


if __name__ == "__main__":
    main()
