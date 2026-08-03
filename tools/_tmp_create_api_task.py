# -*- coding: utf-8 -*-
"""Browser E2E: create API test task and report final status bucket."""

from __future__ import annotations

import json
from pathlib import Path
import time
import urllib.request

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8765"
OUT = Path("tools/_tmp_browser_out")
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name: str):
    p = OUT / f"{name}.png"
    page.screenshot(path=str(p), full_page=True)
    print(f"[shot] {p}")


def http_json(method: str, url: str, token: str = "", body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def classify(task: dict) -> str:
    status = task.get("status")
    outcome = task.get("outcome") or ""
    running = bool(task.get("running"))
    if running or status == "running":
        return "RUNNING"
    if status == "queued":
        return "WAITING"
    if outcome == "completed":
        return "COMPLETED"
    if outcome in ("stopped", "interrupted", "error"):
        return "INCOMPLETE"
    return "IDLE_NOT_EXECUTED"


def main():
    login = http_json(
        "POST",
        f"{API}/api/ai/auth/login",
        body={"username": "admin", "password": "admin123"},
    )
    access = login["access_token"]
    refresh = login.get("refresh_token", "")
    print("[auth] ok")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.set_default_timeout(30000)

        # Correct auth pool format used by LoginView/api-client
        page.goto(f"{BASE}/login")
        page.evaluate(
            """([access, refresh]) => {
              localStorage.setItem('auth_accounts', JSON.stringify({
                admin: { access_token: access, refresh_token: refresh || '' }
              }));
              sessionStorage.setItem('auth_active', 'admin');
            }""",
            [access, refresh],
        )
        page.goto(f"{BASE}/runner")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        print(f"[nav] {page.url}")
        shot(page, "01_runner")
        if "/login" in page.url:
            print("[fail] redirected to login")
            browser.close()
            return 2

        opened = page.evaluate(
            """() => {
              const btn = [...document.querySelectorAll('button')].find(b => (b.innerText||'').includes('\\u65b0\\u5efa\\u4efb\\u52a1'));
              if (!btn) return false;
              btn.click();
              return true;
            }"""
        )
        print(f"[open-dialog] {opened}")
        page.wait_for_selector(".el-dialog", timeout=10000)
        page.wait_for_timeout(400)
        shot(page, "02_dialog")

        task_name = f"browser-api-{int(time.time()) % 100000}"
        page.locator(".el-dialog .el-input__inner").first.fill(task_name)

        # Select API task type via unicode escapes in JS
        pick_type = page.evaluate(
            """() => {
              const items = [...document.querySelectorAll('.el-dialog .el-form-item')];
              const item = items.find(i => (i.innerText||'').includes('\\u4efb\\u52a1\\u7c7b\\u578b'));
              if (!item) return {ok:false, reason:'no-type-item'};
              const sel = item.querySelector('.el-select');
              if (!sel) return {ok:false, reason:'no-select'};
              sel.click();
              return {ok:true};
            }"""
        )
        print(f"[type-open] {pick_type}")
        page.wait_for_timeout(400)
        pick_api = page.evaluate(
            """() => {
              const opts = [...document.querySelectorAll('.el-select-dropdown__item, .el-option')];
              const visible = opts.filter(o => o.offsetParent !== null || o.getClientRects().length);
              const api = visible.find(o => (o.innerText||'').includes('API'));
              if (!api) return {ok:false, texts: visible.map(o => (o.innerText||'').trim()).slice(0,10)};
              api.click();
              return {ok:true, text: (api.innerText||'').trim()};
            }"""
        )
        print(f"[type-pick] {pick_api}")
        page.wait_for_timeout(1500)
        shot(page, "03_api_type")

        # Confirm type text
        type_now = page.evaluate(
            """() => {
              const items = [...document.querySelectorAll('.el-dialog .el-form-item')];
              const item = items.find(i => (i.innerText||'').includes('\\u4efb\\u52a1\\u7c7b\\u578b'));
              return item ? item.innerText : '';
            }"""
        )
        print(f"[type-now] {type_now!r}")

        # Pick case
        page.evaluate(
            """() => {
              const items = [...document.querySelectorAll('.el-dialog .el-form-item')];
              const item = items.find(i => (i.innerText||'').includes('\\u7528\\u4f8b'));
              item && item.querySelector('.el-select') && item.querySelector('.el-select').click();
            }"""
        )
        page.wait_for_timeout(700)
        case_pick = page.evaluate(
            """() => {
              const opts = [...document.querySelectorAll('.el-select-dropdown__item, .el-option')];
              const visible = opts.filter(o => o.getClientRects().length > 0);
              if (!visible.length) return {ok:false, count:0};
              const t = (visible[0].innerText||'').trim();
              visible[0].click();
              return {ok:true, count: visible.length, text: t.slice(0,100)};
            }"""
        )
        print(f"[case-pick] {case_pick}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        shot(page, "05_filled")

        if not case_pick.get("ok"):
            print("[fail] no API cases selectable")
            browser.close()
            return 3

        # loop = 1 via JS
        page.evaluate(
            """() => {
              const items = [...document.querySelectorAll('.el-dialog .el-form-item')];
              const item = items.find(i => (i.innerText||'').includes('\\u5faa\\u73af'));
              const input = item && item.querySelector('input');
              if (!input) return;
              const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
              setter.call(input, '1');
              input.dispatchEvent(new Event('input', {bubbles:true}));
              input.dispatchEvent(new Event('change', {bubbles:true}));
            }"""
        )

        run_resp = {"status": None, "body": None, "url": None}

        def on_response(resp):
            if "/runner/run" in resp.url and resp.request.method == "POST":
                run_resp["status"] = resp.status
                run_resp["url"] = resp.url
                try:
                    run_resp["body"] = resp.json()
                except Exception as e:
                    run_resp["body"] = {"err": str(e)}

        page.on("response", on_response)

        create = page.evaluate(
            """() => {
              const btn = [...document.querySelectorAll('.el-dialog button')].find(b => (b.innerText||'').includes('\\u521b\\u5efa\\u5e76\\u6267\\u884c'));
              if (!btn) return 'missing';
              if (btn.disabled) return 'disabled';
              btn.click();
              return 'clicked';
            }"""
        )
        print(f"[create] {create}")
        page.wait_for_timeout(6000)
        shot(page, "06_after_create")
        toasts = page.evaluate(
            "() => [...document.querySelectorAll('.el-message')].map(e => e.innerText.trim())"
        )
        print(f"[toast] {toasts}")
        print(f"[run_api] {json.dumps(run_resp, ensure_ascii=False)[:1000]}")

        tasks = http_json("GET", f"{API}/api/runner/tasks", token=access)
        task = next((t for t in tasks.get("tasks", []) if t.get("name") == task_name), None)
        print(f"[task1] {json.dumps(task, ensure_ascii=False)}")

        if task and (task.get("running") or task.get("status") == "running"):
            print("[wait] 12s")
            page.wait_for_timeout(12000)
            tasks = http_json("GET", f"{API}/api/runner/tasks", token=access)
            task = next((t for t in tasks.get("tasks", []) if t.get("name") == task_name), None)
            shot(page, "07_after_wait")

        bucket = classify(task or {})
        result = {
            "task_name": task_name,
            "task_id": (task or {}).get("id"),
            "taskType": (task or {}).get("taskType"),
            "status": (task or {}).get("status"),
            "outcome": (task or {}).get("outcome"),
            "running": (task or {}).get("running"),
            "bucket": bucket,
            "case_selected": case_pick.get("text"),
            "run_api": run_resp,
            "toasts": toasts,
            "create": create,
        }
        (OUT / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("=== RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()
        return 0 if task else 1


if __name__ == "__main__":
    raise SystemExit(main())
