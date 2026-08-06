"""
Smoke-test driver for Android-AutoTests platform.

Usage:
    python .claude/skills/run-android-autotests/driver.py [--verbose]

Verifies all 4 services are healthy, auth works, and key API endpoints respond.
Returns exit code 0 on success, non-zero on failure.
"""

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

SERVICES = {
    "redis": 6379,
    "backend": 8766,
    "frontend": 5173,
}

AUTH_URL = "http://127.0.0.1:8766/api/ai/auth/login"
API_BASE = "http://127.0.0.1:8766"
FRONTEND_URL = "http://127.0.0.1:5173"

CREDS = {"username": "admin", "password": "admin123"}

VERBOSE = False


def log(msg):
    print(f"  {msg}")


def vlog(msg):
    if VERBOSE:
        log(msg)


def port_open(port):
    """Check if a TCP port is listening."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except OSError:
        return False


def http_get(url, headers=None, timeout=5):
    """GET and return (status, body)."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def http_post(url, data, headers=None, timeout=5):
    """POST JSON and return (status, body)."""
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def check_services():
    """Step 1: verify all 3 services are listening."""
    print("[1/4] Checking services...")
    ok = True
    for name, port in SERVICES.items():
        if port_open(port):
            log(f"{name:15s} :{port}  ONLINE")
        else:
            log(f"{name:15s} :{port}  OFFLINE")
            ok = False
    return ok


def check_auth():
    """Step 2: login and get JWT token."""
    print("[2/4] Testing auth...")
    status, body = http_post(AUTH_URL, CREDS)
    if status != 200:
        log(f"Login failed: HTTP {status}")
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        log(f"Login returned non-JSON: {body[:100]}")
        return None
    if not data.get("status"):
        log(f"Login error: {data.get('message')}")
        return None
    token = data.get("access_token")
    if not token:
        log("No access_token in response")
        return None
    log(f"Logged in as: {data['user']['username']}")
    return token


def check_api(token):
    """Step 3: call authenticated API endpoints."""
    print("[3/4] Testing API endpoints...")
    ok = True
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        ("GET", "/api/dashboard/stats/", None),
        ("GET", "/api/devices", None),
        ("GET", "/api/cases/definitions", None),
        ("GET", "/api/elements/pages", None),
    ]

    for method, path, _ in endpoints:
        status, body = http_get(f"{API_BASE}{path}", headers=headers)
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {"status": False, "message": "invalid JSON"}
        emoji = "OK" if status == 200 and data.get("status") else "FAIL"
        if emoji == "FAIL":
            ok = False
        log(f"  {emoji}  {method} {path}  -> {status}")

    return ok


def check_frontend():
    """Step 4: verify frontend serves HTML."""
    print("[4/4] Testing frontend...")
    status, body = http_get(FRONTEND_URL)
    if status == 200 and "<!DOCTYPE html>" in body:
        log(f"Frontend serves HTML ({len(body)} bytes)")
        return True
    else:
        log(f"Frontend not serving HTML: HTTP {status}")
        return False


def main():
    global VERBOSE
    parser = argparse.ArgumentParser(description="Android-AutoTests smoke test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    VERBOSE = args.verbose

    print("=== Android-AutoTests Smoke Test ===\n")

    fails = 0

    if not check_services():
        fails += 1
        print("\n  Some services are down. Try: python run.py start")
        sys.exit(1)

    print()
    token = check_auth()
    if not token:
        fails += 1
        print("\n  Auth failed. Check credentials in .env")
        sys.exit(1)

    print()
    if not check_api(token):
        fails += 1

    print()
    if not check_frontend():
        fails += 1

    print()
    if fails == 0:
        print("All checks passed. Platform is healthy.")
        sys.exit(0)
    else:
        print(f"{fails} check(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
