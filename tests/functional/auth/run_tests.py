#!/usr/bin/env python
"""Auth functional tests — executable automation script.

Usage:
    python scripts/run_auth_tests.py
    python scripts/run_auth_tests.py --case AUTH-API-01
"""

import os, sys, json, argparse, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import requests

BASE_URL = "http://localhost:8765"
CREDENTIALS = {"username": "admin", "password": "admin123"}


def test_auth_api_01_login_ok():
    """AUTH-API-01: 正常登录"""
    r = requests.post(f"{BASE_URL}/api/ai/auth/login", json=CREDENTIALS)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    assert d["ok"], "ok=False"
    assert d.get("access_token"), "No access_token"
    assert d.get("refresh_token"), "No refresh_token"
    return True


def test_auth_api_02_wrong_password():
    """AUTH-API-02: 错误密码"""
    r = requests.post(f"{BASE_URL}/api/ai/auth/login",
                      json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    return True


def test_auth_api_03_refresh_token():
    """AUTH-API-03: Token 刷新"""
    r = requests.post(f"{BASE_URL}/api/ai/auth/login", json=CREDENTIALS)
    refresh = r.json()["refresh_token"]
    r2 = requests.post(f"{BASE_URL}/api/ai/auth/refresh",
                       json={"refresh_token": refresh})
    assert r2.status_code == 200, f"HTTP {r2.status_code}"
    assert r2.json().get("access_token"), "No new access_token"
    return True


def test_auth_api_04_logout():
    """AUTH-API-04: 登出"""
    r = requests.post(f"{BASE_URL}/api/ai/auth/login", json=CREDENTIALS)
    token = r.json()["access_token"]
    r2 = requests.post(f"{BASE_URL}/api/ai/auth/logout",
                       headers={"Authorization": f"Bearer {token}"})
    assert r2.json()["ok"], "ok=False"
    return True


def test_auth_api_05_me():
    """AUTH-API-05: 获取当前用户"""
    r = requests.post(f"{BASE_URL}/api/ai/auth/login", json=CREDENTIALS)
    token = r.json()["access_token"]
    r2 = requests.get(f"{BASE_URL}/api/ai/auth/me",
                      headers={"Authorization": f"Bearer {token}"})
    assert r2.json()["ok"], "ok=False"
    assert r2.json()["user"]["username"] == "admin", "Wrong username"
    return True


def test_auth_ui_01_login_page():
    """AUTH-UI-01: 登录页加载"""
    r = requests.get("http://localhost:5173/src/views/LoginView.vue")
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return True


def test_auth_ui_02_no_hardcoded_password():
    """AUTH-UI-02: 无硬编码密码"""
    vue_path = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                            "frontend", "src", "views", "LoginView.vue")
    with open(vue_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 检查无硬编码 admin123 作为默认值
    assert "ref('admin123')" not in content, \
        "LoginView.vue contains hardcoded password ref('admin123')"
    return True


ALL_TESTS = {
    "AUTH-API-01": test_auth_api_01_login_ok,
    "AUTH-API-02": test_auth_api_02_wrong_password,
    "AUTH-API-03": test_auth_api_03_refresh_token,
    "AUTH-API-04": test_auth_api_04_logout,
    "AUTH-API-05": test_auth_api_05_me,
    "AUTH-UI-01": test_auth_ui_01_login_page,
    "AUTH-UI-02": test_auth_ui_02_no_hardcoded_password,
}


def run_tests(case_ids=None):
    results = []
    tests = {k: v for k, v in ALL_TESTS.items() if not case_ids or k in case_ids}

    for case_id, test_fn in tests.items():
        start = time.time()
        try:
            test_fn()
            results.append({"case": case_id, "status": "PASS",
                           "duration_ms": round((time.time() - start) * 1000),
                           "error": None})
        except Exception as e:
            results.append({"case": case_id, "status": "FAIL",
                           "duration_ms": round((time.time() - start) * 1000),
                           "error": str(e)})
    return results


def print_report(results):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    pct = round(passed / total * 100) if total else 0

    print(f"\n{'='*50}")
    print(f"  Auth Test Report — {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Total: {total} | Pass: {passed} | Fail: {failed} | Rate: {pct}%")
    if failed:
        print(f"\n  Failed:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    {r['case']}: {r['error'][:100]}")
    print(f"  Conclusion: {'可以提交' if failed == 0 else '需修复'}")
    print(f"{'='*50}\n")
    return pct == 100


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="Run specific test case")
    args = parser.parse_args()
    case_ids = [args.case] if args.case else None
    results = run_tests(case_ids=case_ids)
    sys.exit(0 if print_report(results) else 1)
