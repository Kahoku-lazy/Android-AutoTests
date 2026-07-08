"""
Test-Runner 测试共享基础设施.
"""
import sys, os, json, time
from datetime import datetime
from pathlib import Path

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import requests

BASE_URL = "http://localhost:5173"
API_BASE = "http://localhost:8765/api"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Django ORM ──
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
_django_ready = False
_models = {}
try:
    import django; django.setup()
    from apps.test_runner.models import TaskCard, TestRunRecord, TestResult, TestSOP
    from apps.case_manager.models import TestDefinition, CaseDirectory
    _models = {
        "TaskCard": TaskCard, "TestRunRecord": TestRunRecord,
        "TestResult": TestResult, "TestSOP": TestSOP,
        "TestDefinition": TestDefinition, "CaseDirectory": CaseDirectory,
    }
    _django_ready = True
except Exception as e:
    print(f"[helpers] Django setup skipped: {e}")

# ── Playwright ──
_playwright_ready = False
sync_playwright = None
try:
    from playwright.sync_api import sync_playwright as _sp
    sync_playwright = _sp
    _playwright_ready = True
except ImportError:
    pass

def get_model(name):
    return _models.get(name)

# ── Auth ──
_token = None
def api_headers():
    global _token
    if not _token:
        r = requests.post(f"{API_BASE}/ai/auth/login",
            json={"username": "admin", "password": "admin123"}, timeout=5)
        if r.status_code == 200 and r.json().get("ok"):
            _token = r.json()["access_token"]
    return {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"} if _token else {}

# ── Cleanup ──
_cleanup_tasks = []

def register_cleanup(task_id):
    _cleanup_tasks.append(task_id)

def cleanup_all():
    h = api_headers()
    for tid in _cleanup_tasks:
        try: requests.delete(f"{API_BASE}/runner/tasks/{tid}", headers=h, timeout=5)
        except: pass
    _cleanup_tasks.clear()

# ── Test records ──
ALL_TESTS = {}
_results = []

def record(cid, layer, desc, passed, got, expected, duration_ms=0):
    _results.append({
        "id": cid, "layer": layer, "desc": desc,
        "passed": passed, "got": str(got)[:200], "expected": str(expected)[:200],
        "duration_ms": duration_ms,
    })
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {cid} — {desc}")

def summary():
    p = sum(1 for r in _results if r["passed"])
    f = len(_results) - p
    print(f"\n{'='*50}")
    print(f"  Results: {p} PASS, {f} FAIL, {len(_results)} total")
    return p, f
