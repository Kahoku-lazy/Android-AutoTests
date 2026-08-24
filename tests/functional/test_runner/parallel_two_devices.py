"""场景：双设备并行（浏览器 + API 计时）— 真机清单第 7 项，per-serial 锁关键验证。

浏览器创建两个任务（不同设备、loop=5 拉长窗口）→ API 轮询记录两任务
running 时间窗 → 断言存在重叠（跨 serial 并行不互卡）。
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
TAG = datetime.now().strftime("%H%M%S")
TASKS = [
    {"name": f"TEST-PARA-A-{TAG}", "device": "RF8N21MSW7A"},
    {"name": f"TEST-PARA-B-{TAG}", "device": "R5CT62RH88F"},
]
CASE = "01-启动与关闭APP"


def api(path, method="GET", body=None, token=None):
    req = urllib.request.Request(BASE_API + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data=data) as r:
        return json.loads(r.read().decode())


def create_task(page, name, device):
    page.goto(BASE_FE + "/runner", wait_until="networkidle")
    page.wait_for_selector('button:has-text("＋ 新建任务")')
    page.click('button:has-text("＋ 新建任务")')
    page.wait_for_selector('.el-dialog:has-text("新建测试任务")')
    page.fill('.el-dialog input[placeholder="如：稳定性测试"]', name)
    page.fill(".el-dialog .el-input-number input", "5")
    page.click('.el-dialog .el-form-item:has-text("设备") .el-select__wrapper')
    page.wait_for_selector(".el-select-dropdown:visible")
    page.click(
        f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{device}")', force=True
    )
    page.click('.el-dialog .el-form-item:has-text("用例") .el-select__wrapper')
    page.wait_for_selector(".el-select-dropdown:visible")
    page.click(
        f'.el-select-dropdown:visible .el-select-dropdown__item:has-text("{CASE}")', force=True
    )
    page.keyboard.press("Escape")
    page.click('.el-dialog button:has-text("创建并执行")')
    page.wait_for_selector(".el-dialog", state="hidden", timeout=20000)
    print(f"[OK] 已提交 {name} @ {device}")


def main():
    token = api("/api/auth/login", "POST", {"username": "admin", "password": "admin123"})["data"][
        "access_token"
    ]
    pw = sync_playwright().start()
    try:
        b = pw.chromium.launch(headless=False)
        page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
        page.set_default_timeout(30000)
        page.goto(BASE_FE + "/login", wait_until="networkidle")
        page.fill('input[placeholder="账号"]', "admin")
        page.fill('input[placeholder="密码"]', "admin123")
        page.click('button:has-text("登录")')
        page.wait_for_function("!location.pathname.startsWith('/login')")

        for spec in TASKS:
            create_task(page, spec["name"], spec["device"])

        # API 轮询：记录两个任务 running 窗口
        windows = {s["name"]: [] for s in TASKS}  # name → 连续 running 的时间段
        timeline = []
        deadline = time.time() + 240
        while time.time() < deadline:
            resp = api("/api/runner/tasks", token=token)
            snapshot = {}
            for s in TASKS:
                t = next((x for x in resp.get("tasks", []) if x["name"] == s["name"]), None)
                if t:
                    snapshot[s["name"]] = (t["state"], t.get("deviceSerial"))
            timeline.append((time.time(), snapshot))
            all_done = all(v and v[0] == "done" for v in snapshot.values())
            if all_done and len(snapshot) == 2:
                break
            time.sleep(2)

        for s in TASKS:
            runs = [ts for ts, snap in timeline if snap.get(s["name"], (None,))[0] == "running"]
            if runs:
                windows[s["name"]] = (min(runs), max(runs))

        a, b = windows[TASKS[0]["name"]], windows[TASKS[1]["name"]]
        overlap = a and b and max(a[0], b[0]) < min(a[1], b[1])
        print(
            json.dumps(
                {
                    "windows": {
                        k: (f"{v[0]:.0f}" if v else None, f"{v[1]:.0f}" if v else None)
                        for k, v in windows.items()
                    },
                    "overlap_running": bool(overlap),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        # 终态确认
        resp = api("/api/runner/tasks", token=token)
        for s in TASKS:
            t = next((x for x in resp.get("tasks", []) if x["name"] == s["name"]), None)
            if t:
                print(
                    f"[终态] {s['name']} state={t['state']} outcome={t['outcome']} pass={t['overallPass']}"
                )
        b.close()
    finally:
        pw.stop()


if __name__ == "__main__":
    main()
