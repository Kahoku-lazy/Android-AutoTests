"""
Case-Manager 测试共享基础设施 — auth / record / cleanup / 截图 / ALL_TESTS.
"""
import sys, os, json, time, re, base64
from datetime import datetime
from pathlib import Path

# ── 确保同目录可 import ──
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# 项目根
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import requests

BASE_URL = "http://localhost:5173"
API_BASE = "http://localhost:8765/api"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Django ORM ──
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
_django_ready = False
_models = {}
try:
    import django; django.setup()
    from apps.case_manager.models import TestDefinition, CaseDirectory, TestCaseCache
    _models = {"TestDefinition": TestDefinition, "CaseDirectory": CaseDirectory, "TestCaseCache": TestCaseCache}
    _django_ready = True
except Exception:
    pass

def get_model(name):
    return _models.get(name)

# ── Playwright ──
_playwright_ready = False
sync_playwright = None
try:
    from playwright.sync_api import sync_playwright as _sp
    sync_playwright = _sp
    _playwright_ready = True
except ImportError:
    pass

# ── Auth ──
_token_cache = None

def get_token():
    global _token_cache
    if _token_cache: return _token_cache
    try:
        r = requests.post(f"{API_BASE}/ai/auth/login",
                          json={"username": "admin", "password": "admin123"}, timeout=5)
        if r.ok and r.json().get("ok"):
            _token_cache = r.json()["access_token"]
            return _token_cache
    except Exception: pass
    return None

def api_headers():
    t = get_token()
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"} if t else {}

# ── 修复日志（全程追踪）──
fix_log = []

def log_fix(case_id, problem, solution, auto_fixed=False):
    """记录修复痕迹。即使自动修复也要留下记录。"""
    entry = {
        "case": case_id, "problem": problem, "solution": solution,
        "auto_fixed": auto_fixed, "time": datetime.now().strftime("%H:%M:%S"),
    }
    fix_log.append(entry)
    return entry

# ── 截图 ──
def capture_screenshot(page, case_id):
    """失败时截取全页截图，返回 base64 data URI 和文件路径。"""
    ts = datetime.now().strftime("%H%M%S")
    filename = f"{case_id}_{ts}.png"
    filepath = SCREENSHOTS_DIR / filename
    try:
        page.screenshot(path=str(filepath), full_page=True)
        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{b64}", str(filepath)
    except Exception as e:
        return "", f"截图失败: {e}"

# ── Results ──
results = []

def record(case_id, layer, description, passed, actual, expected, duration_ms,
           screenshot=None, fix_note=None, root_cause=None, repro_steps=None, fix_suggestion=None):
    """记录测试结果。root_cause=问题原因, repro_steps=复现步骤, fix_suggestion=解决方案."""
    results.append({
        "case": case_id, "dim": layer, "description": description,
        "status": "PASS" if passed else "FAIL",
        "actual": str(actual)[:300], "expected": str(expected)[:300],
        "duration_ms": duration_ms,
        "evidence": {"actual": str(actual)[:300], "expected": str(expected)[:300]},
        "screenshot": screenshot or "",
        "fix_note": fix_note or "",
        "root_cause": root_cause or "",
        "repro_steps": repro_steps or "",
        "fix_suggestion": fix_suggestion or "",
    })

# ── Cleanup ──
_created_dirs = []; _created_cases = []

def register_cleanup_dir(did): _created_dirs.append(did)
def register_cleanup_case(cid): _created_cases.append(cid)

def cleanup_all():
    h = api_headers()
    for cid in reversed(_created_cases):
        try: requests.delete(f"{API_BASE}/cases/definitions/{cid}", headers=h, timeout=10)
        except Exception: pass
    for did in reversed(_created_dirs):
        try: requests.post(f"{API_BASE}/cases/directories/{did}", json={"action": "delete"}, headers=h, timeout=10)
        except Exception: pass

# ── Playwright login ──
def playwright_login(page):
    page.goto(f"{BASE_URL}/login", wait_until="networkidle"); page.wait_for_timeout(1000)
    try:
        u = page.locator('input[type="text"]').first
        p = page.locator('input[type="password"]').first
        if u.count(): u.fill("admin")
        if p.count(): p.fill("admin123")
        btn = page.locator('button').filter(has_text="开始使用")
        if btn.count() == 0: btn = page.locator("button").last
        btn.click(); page.wait_for_timeout(2000)
    except Exception: pass

# ── ALL_TESTS ──
ALL_TESTS = {}
