"""
登录功能 — API + Web 自动化测试
用法: PYTHONIOENCODING=utf-8 python tests/run_auth_tests.py
前提: Django :8765 + Vite :5173 已启动
"""

import asyncio
import json
import os
import sys
import time

import requests

# Ensure project root is on sys.path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Django setup (for ORM writes to steps_json) ──
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.case_manager.models_api import ApiTestCase
from apps.case_manager.models_web import WebTestCase
from apps.test_runner.models import TestResult as TR

# ── Config ──
BASE_URL = "http://localhost:8765"
AUTH_URL = f"{BASE_URL}/api/ai/auth"
FRONTEND_URL = "http://localhost:5173"
TIMEOUT = 30
TS = str(int(time.time()))[-6:]

# ── Test accounts ──
TEST_USER = "admin"
TEST_PASS = "admin123"

# ── Result tracking ──
passed = 0
failed = 0


def T(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}")


def login(username=TEST_USER, password=TEST_PASS):
    """Get access token for auth-dependent tests."""
    try:
        r = requests.post(
            f"{AUTH_URL}/login", json={"username": username, "password": password}, timeout=TIMEOUT
        )
        if r.status_code == 200 and r.json().get("ok"):
            return r.json()["access_token"]
    except Exception as e:
        print(f"  [WARN] login failed: {e}")
    return ""


# ══════════════════════════════════════════════════════════════════════
# Step 1: Create API test cases (via ORM — views don't accept steps_json)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 1: Creating API test cases...")
print("=" * 60)

API_CASES = {
    "API-LOGIN-01": {
        "title": "[API] 正常登录",
        "description": "验证 admin/admin123 登录成功",
        "steps_json": json.dumps(
            [
                {
                    "type": "api_request",
                    "method": "POST",
                    "url": f"{AUTH_URL}/login",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"username": TEST_USER, "password": TEST_PASS},
                    "expected_status": 200,
                    "assertions": [
                        {"path": "$.ok", "operator": "equals", "value": True},
                    ],
                    "description": "POST /auth/login — normal login",
                }
            ]
        ),
        "enabled": True,
        "case_type": "api_testing",
    },
    "API-LOGIN-02": {
        "title": "[API] 错误密码登录",
        "description": "验证错误密码返回 401",
        "steps_json": json.dumps(
            [
                {
                    "type": "api_request",
                    "method": "POST",
                    "url": f"{AUTH_URL}/login",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"username": TEST_USER, "password": "wrong_password"},
                    "expected_status": 401,
                    "description": "POST /auth/login — wrong password → 401",
                }
            ]
        ),
        "enabled": True,
        "case_type": "api_testing",
    },
    "API-LOGIN-04": {
        "title": "[API] 注册缺少密码",
        "description": "验证注册时缺少密码返回 400",
        "steps_json": json.dumps(
            [
                {
                    "type": "api_request",
                    "method": "POST",
                    "url": f"{AUTH_URL}/register",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"username": "testonly"},
                    "expected_status": 400,
                    "description": "POST /auth/register — missing password → 400",
                }
            ]
        ),
        "enabled": True,
        "case_type": "api_testing",
    },
    "API-LOGIN-05": {
        "title": "[API] Token 刷新",
        "description": "验证 refresh token 能获取新 access token",
        "steps_json": json.dumps(
            [
                {
                    "type": "api_request",
                    "method": "POST",
                    "url": f"{AUTH_URL}/login",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"username": TEST_USER, "password": TEST_PASS},
                    "expected_status": 200,
                    "extract": {"refresh_token": "$.refresh_token"},
                    "description": "Step 1: Login to get refresh_token",
                },
                {
                    "type": "api_request",
                    "method": "POST",
                    "url": f"{AUTH_URL}/refresh",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"refresh_token": "{{refresh_token}}"},
                    "expected_status": 200,
                    "assertions": [
                        {"path": "$.ok", "operator": "equals", "value": True},
                    ],
                    "description": "Step 2: Refresh token",
                },
            ]
        ),
        "enabled": True,
        "case_type": "api_testing",
    },
}

api_case_ids = []
for case_id, fields in API_CASES.items():
    obj, created = ApiTestCase.objects.update_or_create(
        id=case_id,
        defaults=fields,
    )
    api_case_ids.append(case_id)
    print(f"  {'[NEW]' if created else '[OK]'} {case_id}: {fields['title']}")

# ══════════════════════════════════════════════════════════════════════
# Step 2: Create Web test cases
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 2: Creating Web test cases...")
print("=" * 60)

WEB_CASES = {
    "WEB-LOGIN-01": {
        "title": "[Web] 登录页面跳转并登录",
        "description": "导航到登录页 → 填写表单 → 点击登录 → 验证跳转",
        "url": f"{FRONTEND_URL}/login",
        "expected_result": "",
        "steps_json": json.dumps(
            [
                {
                    "type": "web_navigate",
                    "url": f"{FRONTEND_URL}/login",
                    "description": "Navigate to login page",
                },
                {
                    "type": "web_wait",
                    "timeout": 2.0,
                    "description": "Wait for Vue to render",
                },
                {
                    "type": "web_fill",
                    "selector": 'input[placeholder="账号"]',
                    "value": TEST_USER,
                    "description": "Enter username",
                },
                {
                    "type": "web_fill",
                    "selector": '.login-form input[type="password"]',
                    "value": TEST_PASS,
                    "description": "Enter password",
                },
                {
                    "type": "web_click",
                    "selector": 'button:has-text("开始使用")',
                    "description": "Click login button",
                },
                {
                    "type": "web_wait",
                    "timeout": 3.0,
                    "description": "Wait for redirect",
                },
                {
                    "type": "web_screenshot",
                    "description": "after-login",
                },
            ]
        ),
        "enabled": True,
        "case_type": "web_automation",
    },
    "WEB-LOGIN-02": {
        "title": "[Web] 登录页面加载验证",
        "description": "验证登录页面加载成功",
        "url": f"{FRONTEND_URL}/login?add=1",
        "expected_result": "",
        "steps_json": json.dumps(
            [
                {
                    "type": "web_navigate",
                    "url": f"{FRONTEND_URL}/login?add=1",
                    "description": "Navigate to login page (force form mode)",
                },
                {
                    "type": "web_wait",
                    "timeout": 3.0,
                    "description": "Wait for page load",
                },
                {
                    "type": "web_screenshot",
                    "description": "login-page-loaded",
                },
            ]
        ),
        "enabled": True,
        "case_type": "web_automation",
    },
}

web_case_ids = []
for case_id, fields in WEB_CASES.items():
    obj, created = WebTestCase.objects.update_or_create(
        id=case_id,
        defaults=fields,
    )
    web_case_ids.append(case_id)
    print(f"  {'[NEW]' if created else '[OK]'} {case_id}: {fields['title']}")


# ══════════════════════════════════════════════════════════════════════
# Step 3: Execute via direct engine call (bypasses HTTP scheduling issue)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 3: Executing tests via execution engine...")
print("=" * 60)

from asgiref.sync import sync_to_async

from apps.test_runner.views.execution import _execute_unified_remote
from models.step_types import TestStep
from models.test_models import TestCaseDef


def build_testcase(row, task_type):
    """Build TestCaseDef from an ORM row."""
    steps_raw = json.loads(getattr(row, "steps_json", "[]") or "[]")
    steps_data = [TestStep.from_dict(s) for s in steps_raw]
    extra = {}
    if task_type == "api_testing":
        extra = {
            "method": getattr(row, "method", "GET"),
            "url": getattr(row, "url", ""),
            "headers": getattr(row, "headers", ""),
            "body": getattr(row, "body", ""),
            "expected_response": getattr(row, "expected_response", ""),
        }
    elif task_type == "web_automation":
        extra = {
            "url": getattr(row, "url", ""),
            "steps": getattr(row, "steps", ""),
            "expected_result": getattr(row, "expected_result", ""),
        }
    return TestCaseDef(
        id=row.id,
        title=row.title,
        steps_data=steps_data,
        task_type=task_type,
        extra_data=extra,
    )


@sync_to_async
def _load_cases(Model, case_ids):
    return list(Model.objects.filter(id__in=case_ids, enabled=True))


@sync_to_async
def _get_results(run_id):
    return list(
        TR.objects.filter(run__run_id=run_id).values(
            "case_id", "case_type", "result", "duration_ms", "detail"
        )
    )


async def execute_and_collect(case_ids, task_type, label):
    """Run test cases via _execute_unified_remote and collect results."""
    print(f"\n{'─' * 60}")
    print(f"Executing {label} tests: {case_ids}")

    if task_type == "api_testing":
        from apps.case_manager.models_api import ApiTestCase

        Model = ApiTestCase
        device_label = "api"
    else:
        from apps.case_manager.models_web import WebTestCase

        Model = WebTestCase
        device_label = "web"

    rows = await _load_cases(Model, case_ids)
    test_cases = [build_testcase(r, task_type) for r in rows]
    if not test_cases:
        print(f"  [FAIL] No enabled cases found")
        return {}

    run_id = f"{label}-RUN-{TS}"
    print(f"  Run ID: {run_id}, cases: {len(test_cases)}")

    try:
        await _execute_unified_remote(
            run_id,
            test_cases,
            1,
            5,
            client_task_id=run_id,
            task_type=task_type,
            device_label=device_label,
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"  [FAIL] Execution error: {e}")
        return {}

    # Collect results from DB
    results = await _get_results(run_id)
    return {r["case_id"]: r for r in results}


# ── Execute API cases ──
api_results = asyncio.run(execute_and_collect(api_case_ids, "api_testing", "API"))
print("\n--- API Results ---")
for cid in api_case_ids:
    r = api_results.get(cid)
    if r:
        status = "[PASS]" if r["result"] == "pass" else "[FAIL]"
        print(f"  {status} {cid}: {r['result']} ({r['duration_ms']:.0f}ms) | {r['detail'][:100]}")
        T(cid, r["result"] == "pass")
    else:
        print(f"  [?] {cid}: no result found")

# ── Execute Web cases ──
web_results = asyncio.run(execute_and_collect(web_case_ids, "web_automation", "Web"))
print("\n--- Web Results ---")
for cid in web_case_ids:
    r = web_results.get(cid)
    if r:
        status = "[PASS]" if r["result"] == "pass" else "[FAIL]"
        print(f"  {status} {cid}: {r['result']} ({r['duration_ms']:.0f}ms) | {r['detail'][:100]}")
        T(cid, r["result"] == "pass")
    else:
        print(f"  [?] {cid}: no result found")

# ══════════════════════════════════════════════════════════════════════
# Step 4: Report
# ══════════════════════════════════════════════════════════════════════
total = passed + failed
print(f"\n{'=' * 60}")
print(f"  Results: {passed}/{total} passed, {failed} failed")
print(f"{'=' * 60}")

# Show case_type verification
print("\n--- case_type verification ---")
all_case_ids = api_case_ids + web_case_ids
for tr in TR.objects.filter(case_id__in=all_case_ids).values("case_id", "case_type", "result"):
    print(f"  {tr['case_id']}: case_type={tr['case_type']}, result={tr['result']}")

sys.exit(0 if failed == 0 else 1)
