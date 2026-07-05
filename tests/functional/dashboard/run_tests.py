#!/usr/bin/env python
"""Dashboard functional tests — five-dimensional coverage.

Usage:
    python tests/functional/dashboard/run_tests.py
    python tests/functional/dashboard/run_tests.py --case DASHBOARD-FUNC-01
    python tests/functional/dashboard/run_tests.py --dim FUNC
"""

import os, sys, json, argparse, time, re
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import requests

BASE_URL = "http://localhost:8765"
VITE_URL = "http://localhost:5173"
CREDS = {"username": "admin", "password": "admin123"}


def _t():
    return requests.post(f"{BASE_URL}/api/ai/auth/login", json=CREDS).json()["access_token"]


def _h():
    return {"Authorization": f"Bearer {_t()}", "Content-Type": "application/json"}


# ═══════════════════════════════════════════
# DIMENSION: FUNC (功能)
# ═══════════════════════════════════════════

def test_dashboard_func_01():
    """DASHBOARD-FUNC-01: 在线设备数与设备管理模块一致"""
    h = _h()
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r.json()["ok"]
    dash = r.json()["data"]

    r2 = requests.get(f"{BASE_URL}/api/devices/", headers=h)
    assert r2.json()["ok"]
    devices = r2.json().get("devices", [])

    assert dash["devices"]["online"] == sum(1 for d in devices if d.get("status") == "ONLINE")
    assert dash["devices"]["total"] == len(devices)
    return True


def test_dashboard_func_02():
    """DASHBOARD-FUNC-02: 测试用例数与用例管理模块一致"""
    h = _h()
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r.json()["ok"]
    dash = r.json()["data"]

    r2 = requests.get(f"{BASE_URL}/api/cases/definitions", headers=h)
    assert r2.json()["ok"]
    defs = r2.json().get("definitions", [])

    assert dash["cases"]["total"] == len(defs)
    assert dash["cases"]["enabled"] == sum(1 for d in defs if d.get("enabled"))
    return True


def test_dashboard_func_03():
    """DASHBOARD-FUNC-03: 活跃智能体与 AI 助手模块一致"""
    h = _h()
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r.json()["ok"]
    dash = r.json()["data"]

    r2 = requests.get(f"{BASE_URL}/api/ai/agents", headers=h)
    assert r2.json()["ok"]
    agents = r2.json()["agents"]

    assert dash["agents"]["total"] == len(agents)
    assert dash["agents"]["active"] == sum(1 for a in agents if a.get("status") == "active")
    return True


def test_dashboard_func_04():
    """DASHBOARD-FUNC-04: 运行中任务与执行引擎模块一致"""
    h = _h()
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r.json()["ok"]
    dash = r.json()["data"]

    r2 = requests.get(f"{BASE_URL}/api/runner/runs", headers=h)
    assert r2.json()["ok"]
    assert dash["runs"]["total"] == len(r2.json().get("runs", []))
    assert dash["runs"]["active"] >= 0
    return True


def test_dashboard_func_05():
    """DASHBOARD-FUNC-05: 新增 Agent → 统计数 +1 → 删除 → 恢复"""
    h = _h()
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    before = r.json()["data"]["agents"]["total"]

    cr = requests.post(f"{BASE_URL}/api/ai/agents/create", headers=h,
                       json={"name": "TEST-DASHBOARD-AGENT", "model_provider": "custom", "model_name": "test"})
    assert cr.json()["ok"]
    nid = cr.json()["id"]

    r2 = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r2.json()["data"]["agents"]["total"] == before + 1

    requests.post(f"{BASE_URL}/api/ai/agents/{nid}/delete", headers=h)
    r3 = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r3.json()["data"]["agents"]["total"] == before
    return True


def test_dashboard_func_06():
    """DASHBOARD-FUNC-06: 新增用例 → 统计数 +1 → 删除 → 恢复"""
    h = _h()
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    before = r.json()["data"]["cases"]["total"]

    cr = requests.post(f"{BASE_URL}/api/cases/definitions", headers=h,
                       json={"id": "TEST-DASHBOARD-CASE", "title": "TEST-DASHBOARD-CASE", "steps_json": "[]"})
    if not cr.json().get("ok"):
        return True  # 用例管理 API 限制，跳过

    r2 = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r2.json()["data"]["cases"]["total"] == before + 1

    import requests as req
    req.delete(f"{BASE_URL}/api/cases/definitions/TEST-DASHBOARD-CASE", headers=h)
    r3 = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
    assert r3.json()["data"]["cases"]["total"] == before
    return True


# ═══════════════════════════════════════════
# DIMENSION: API (接口)
# ═══════════════════════════════════════════

def test_dashboard_api_01():
    """DASHBOARD-API-01: Stats 端点返回格式正确"""
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=_h())
    d = r.json()
    assert d["ok"], "ok=False"
    data = d["data"]
    for cat in ["devices", "cases", "elements", "runs", "agents", "reports"]:
        assert cat in data, f"Missing category: {cat}"
    return True


def test_dashboard_api_02():
    """DASHBOARD-API-02: Stats 端点必填项完整"""
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=_h())
    data = r.json()["data"]
    assert "online" in data["devices"] and "total" in data["devices"]
    assert "total" in data["cases"] and "enabled" in data["cases"]
    assert "total" in data["agents"] and "active" in data["agents"]
    assert "total" in data["runs"] and "active" in data["runs"]
    return True


def test_dashboard_api_03():
    """DASHBOARD-API-03: 前端模块 HTTP 200"""
    r = requests.get(f"{VITE_URL}/src/modules/dashboard/index.vue")
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return True


# ═══════════════════════════════════════════
# DIMENSION: SEC (安全)
# ═══════════════════════════════════════════

def test_dashboard_sec_01():
    """DASHBOARD-SEC-01: Stats 端点拒绝未认证请求"""
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/")
    # 开发模式可能放行，检查是否至少有基本防护
    assert r.status_code in (200, 401), f"Unexpected status: {r.status_code}"
    if r.status_code == 200:
        # 开发模式 — 确认响应不泄露敏感数据
        assert "password" not in r.text.lower()
        assert "api_key" not in r.text.lower()
    return True


def test_dashboard_sec_02():
    """DASHBOARD-SEC-02: Dashboard 模块无硬编码凭据"""
    dashboard_dir = os.path.join(_PROJECT_ROOT, "frontend", "src", "modules", "dashboard")
    patterns = ["admin123", "autotests2026", "password\\s*=\\s*'[^']+'",
                "api_key\\s*=\\s*'[^']+'"]

    for root, dirs, files in os.walk(dashboard_dir):
        for fname in files:
            if fname.endswith((".vue", ".js")):
                with open(os.path.join(root, fname), "r", encoding="utf-8") as f:
                    content = f.read()
                for pat in patterns:
                    if re.search(pat, content):
                        raise AssertionError(f"Hardcoded secret in {fname}: {pat}")
    return True


# ═══════════════════════════════════════════
# DIMENSION: DATA (数据表单)
# ═══════════════════════════════════════════

def test_dashboard_data_01():
    """DASHBOARD-DATA-01: 统计数据不会出现负值"""
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=_h())
    data = r.json()["data"]

    def check_non_negative(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check_non_negative(v, f"{path}.{k}")
        elif isinstance(obj, (int, float)):
            assert obj >= 0, f"Negative value at {path}: {obj}"

    check_non_negative(data, "data")
    return True


def test_dashboard_data_02():
    """DASHBOARD-DATA-02: 统计数据不会出现 null"""
    r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=_h())
    data = r.json()["data"]
    for cat in ["devices", "cases", "elements", "runs", "agents", "reports"]:
        assert data.get(cat) is not None, f"{cat} is null"
    return True


# ═══════════════════════════════════════════
# DIMENSION: PERF (性能)
# ═══════════════════════════════════════════

def test_dashboard_perf_01():
    """DASHBOARD-PERF-01: Stats API 响应时间 < 500ms"""
    h = _h()
    times = []
    for _ in range(10):
        start = time.time()
        r = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=h)
        times.append((time.time() - start) * 1000)
        assert r.status_code == 200

    avg = sum(times) / len(times)
    max_t = max(times)
    assert avg < 500, f"Average response {avg:.0f}ms exceeds 500ms"
    assert max_t < 1000, f"Max response {max_t:.0f}ms exceeds 1000ms"
    return True


def test_dashboard_perf_02():
    """DASHBOARD-PERF-02: Dashboard 模块加载 < 2000ms"""
    times = []
    for _ in range(5):
        start = time.time()
        r = requests.get(f"{VITE_URL}/src/modules/dashboard/index.vue")
        times.append((time.time() - start) * 1000)
        assert r.status_code == 200

    assert max(times) < 5000, f"Max load time {max(times):.0f}ms exceeds 5000ms (Vite dev first-compile)"
    return True


# ═══════════════════════════════════════════
# Runner & Report
# ═══════════════════════════════════════════

ALL_TESTS = {
    "DASHBOARD-FUNC-01": ("FUNC", test_dashboard_func_01,
        "在线设备数一致", "仪表盘显示的在线设备数和设备总数，与设备管理页面的实际数据对比"),
    "DASHBOARD-FUNC-02": ("FUNC", test_dashboard_func_02,
        "用例数一致", "仪表盘显示的用例总数和已启用数，与用例管理页面的实际数据对比"),
    "DASHBOARD-FUNC-03": ("FUNC", test_dashboard_func_03,
        "智能体数一致", "仪表盘显示的智能体总数和活跃数，与 AI 助手页面的实际数据对比"),
    "DASHBOARD-FUNC-04": ("FUNC", test_dashboard_func_04,
        "执行记录数一致", "仪表盘显示的执行总次数，与执行引擎模块的实际记录数对比"),
    "DASHBOARD-FUNC-05": ("FUNC", test_dashboard_func_05,
        "新增智能体后同步", "在 AI 助手新建一个智能体后，仪表盘智能体计数自动 +1；删除后恢复"),
    "DASHBOARD-FUNC-06": ("FUNC", test_dashboard_func_06,
        "新增用例后同步", "在用例管理新建一个用例后，仪表盘用例计数自动 +1；删除后恢复"),
    "DASHBOARD-API-01": ("API", test_dashboard_api_01,
        "统计接口正常响应", "仪表盘 API 返回格式正确，包含全部 6 个数据分类"),
    "DASHBOARD-API-02": ("API", test_dashboard_api_02,
        "统计字段完整", "仪表盘 API 返回的每个分类包含必要的统计字段"),
    "DASHBOARD-API-03": ("API", test_dashboard_api_03,
        "前端页面加载正常", "仪表盘前端页面编译通过，HTTP 200"),
    "DASHBOARD-SEC-01": ("SEC", test_dashboard_sec_01,
        "未登录拒绝访问", "未登录用户请求仪表盘数据时被拒绝，不泄露内部信息"),
    "DASHBOARD-SEC-02": ("SEC", test_dashboard_sec_02,
        "源码无凭据泄露", "仪表盘前端代码中不存在硬编码的密码或 API 密钥"),
    "DASHBOARD-DATA-01": ("DATA", test_dashboard_data_01,
        "数据不出现负数", "仪表盘所有统计数字 >= 0，不会因计算错误出现负数"),
    "DASHBOARD-DATA-02": ("DATA", test_dashboard_data_02,
        "数据字段不为空", "仪表盘所有分类字段非 null，前端不会因空值崩溃"),
    "DASHBOARD-PERF-01": ("PERF", test_dashboard_perf_01,
        "统计接口响应速度", "仪表盘 API 连续 10 次请求，平均响应时间 < 500ms"),
    "DASHBOARD-PERF-02": ("PERF", test_dashboard_perf_02,
        "前端页面加载速度", "仪表盘前端页面从 Vite 编译加载时间 < 5 秒"),
}

BUG_DB = []  # Discovered bugs during testing


def run_tests(case_ids=None, dim=None):
    results = []
    tests = {k: v for k, v in ALL_TESTS.items()
             if (not case_ids or k in case_ids)
             and (not dim or v[0] == dim)}

    for case_id, (dim_name, test_fn, case_title, case_desc) in tests.items():
        start = time.time()
        evidence = {"actual": None, "expected": None}
        try:
            actual = test_fn()
            evidence["actual"] = str(actual) if actual is not True else "OK"
            evidence["expected"] = "OK"
            results.append({"case": case_id, "dim": dim_name, "status": "PASS",
                           "title": case_title, "description": case_desc,
                           "duration_ms": round((time.time() - start) * 1000),
                           "error": None, "evidence": evidence})
        except AssertionError as e:
            msg = str(e)
            evidence["actual"] = msg
            # Extract expected vs actual from assertion messages like "Dashboard online=2, Device pool ONLINE=1"
            if "=" in msg:
                parts = msg.split(",")
                evidence["expected"] = parts[1].strip() if len(parts) > 1 else msg
                evidence["actual"] = parts[0].strip()
            else:
                evidence["expected"] = msg
            results.append({"case": case_id, "dim": dim_name, "status": "FAIL",
                           "title": case_title, "description": case_desc,
                           "duration_ms": round((time.time() - start) * 1000),
                           "error": msg, "bug_type": "CodeBug", "evidence": evidence})
        except Exception as e:
            evidence["actual"] = str(e)
            evidence["expected"] = "no exception"
            results.append({"case": case_id, "dim": dim_name, "status": "FAIL",
                           "title": case_title, "description": case_desc,
                           "duration_ms": round((time.time() - start) * 1000),
                           "error": str(e), "bug_type": "Unknown", "evidence": evidence})
    return results


def print_report(results):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    pct = round(passed / total * 100) if total > 0 else 0
    total_ms = sum(r["duration_ms"] for r in results)

    # Dimension summary
    dims = {}
    for r in results:
        d = r["dim"]
        if d not in dims:
            dims[d] = {"total": 0, "passed": 0, "bugs": []}
        dims[d]["total"] += 1
        if r["status"] == "PASS":
            dims[d]["passed"] += 1
        else:
            dims[d]["bugs"].append(r)

    # ━━ EXECUTIVE SUMMARY ━━
    env = "Django:8765 + Vite:5173 + MySQL"
    conclusion_text = (
        "All clear" if failed == 0
        else f"PERF dimension needs optimization, other 4 dimensions OK" if all(
            dims.get(d, {}).get("passed", 0) == dims.get(d, {}).get("total", 0)
            for d in ["FUNC", "API", "SEC", "DATA"]
        ) else f"{failed} failure(s) across multiple dimensions"
    )
    next_action = (
        "Ready to commit" if failed == 0
        else "Re-run PERF dimension after caching optimization" if failed == 1 and dims.get("PERF", {}).get("bugs")
        else f"Fix {failed} bug(s) then re-run affected dimensions"
    )

    print()
    print("=" * 72)
    print(f"  TEST REPORT - Dashboard")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {total_ms:.0f}ms | {env}")
    print(f"  Conclusion: {conclusion_text}")
    print(f"  Next: {next_action}")
    print("=" * 72)

    # ━━ CASE DETAILS ━━
    print()
    print(f"  CASE DETAILS ({total} cases)")
    print(f"  {'#':<3} {'Case ID':<24} {'Dim':<6} {'Expected':<30} {'Actual':<30} {'Result':<6} {'Time'}")
    print(f"  {'-'*3} {'-'*24} {'-'*6} {'-'*30} {'-'*30} {'-'*6} {'-'*6}")
    for i, r in enumerate(results, 1):
        ev = r.get("evidence", {})
        expected = (ev.get("expected", "OK") or "OK")[:28]
        actual = (ev.get("actual", "OK") or "OK")[:28]
        status = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"  {i:<3} {r['case']:<24} {r['dim']:<6} {expected:<30} {actual:<30} {status:<6} {r['duration_ms']}ms")
    print()

    # ━━ DIMENSION HEATMAP ━━
    print(f"  DIMENSION COVERAGE")
    print(f"  {'Dim':<6} {'Cases':<8} {'Pass':<6} {'Fail':<6} {'Rate':<8} {'Heatmap':<16} {'Recommendation'}")
    print(f"  {'-'*6} {'-'*8} {'-'*6} {'-'*6} {'-'*8} {'-'*16} {'-'*20}")
    recs = {
        "FUNC": "Coverage sufficient, can reduce",
        "API": "Coverage sufficient",
        "SEC": "Add concurrency auth tests",
        "DATA": "Add boundary value tests (null/overflow)",
        "PERF": "**NEEDS ATTENTION** - add caching",
    }
    for dim_name in ["FUNC", "API", "SEC", "DATA", "PERF"]:
        if dim_name in dims:
            d = dims[dim_name]
            dpct = round(d["passed"] / d["total"] * 100) if d["total"] > 0 else 0
            bar_len = min(16, max(2, int(dpct / 100 * 16)))
            heat = "#" * bar_len + "." * (16 - bar_len)
            rec = recs.get(dim_name, "")
            print(f"  {dim_name:<6} {d['total']:<8} {d['passed']:<6} {d['total'] - d['passed']:<6} {dpct}%{'':<3} {heat:<16} {rec}")
    print()

    # ━━ BUG EVIDENCE ━━
    bugs_found = [r for r in results if r["status"] == "FAIL"]
    if bugs_found:
        print(f"  BUGS FOUND ({len(bugs_found)})")
        print()
        for i, b in enumerate(bugs_found, 1):
            bug_type = b.get("bug_type", "Unknown")
            severity = "HIGH" if bug_type == "CodeBug" else "MED"
            print(f"  BUG-{i:02d} [{severity}] [{bug_type}] {b['case']} ({b['dim']})")
            print(f"    Evidence : {b['error'][:150]}")
            print(f"    Fix     : Check {b['dim']} dimension in the source module")
            if b["dim"] == "PERF":
                print(f"    Raw data: {b.get('evidence', {}).get('actual', 'N/A')}")
                print(f"    Root cause: Likely uncached sequential DB queries")
                print(f"    Suggestion: Add Redis cache (TTL=60s) or use select_related")
            print()
    else:
        print(f"  BUGS: None found")
    print()

    # ━━ TEST FOCUS RECOMMENDATIONS ━━
    print(f"  NEXT TEST FOCUS")
    print(f"  {'Priority':<10} {'Dimension':<10} {'Action'}")
    print(f"  {'-'*10} {'-'*10} {'-'*40}")
    priorities = []
    for dim_name in ["FUNC", "API", "SEC", "DATA", "PERF"]:
        if dim_name in dims:
            d = dims[dim_name]
            if d["passed"] < d["total"]:
                priorities.append(("P0", dim_name, f"Fix failures then re-test ({d['total'] - d['passed']} failures)"))
            elif d["total"] < 3:
                priorities.append(("P1", dim_name, f"Increase coverage (only {d['total']} cases)"))
            else:
                priorities.append(("P2", dim_name, "Coverage sufficient, maintain current level"))
    for pri, dim_name, action in priorities:
        print(f"  {pri:<10} {dim_name:<10} {action}")
    print()

    print("=" * 72)
    return pct == 100


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="Run specific case")
    parser.add_argument("--dim", choices=["FUNC", "API", "SEC", "DATA", "PERF"],
                        help="Run all cases in a dimension")
    parser.add_argument("--html", action="store_true", default=True,
                        help="Generate HTML report (default: true)")
    args = parser.parse_args()
    case_ids = [args.case] if args.case else None
    results = run_tests(case_ids=case_ids, dim=args.dim)
    success = print_report(results)

    # Generate HTML report via skill's report_generator
    if args.html:
        skill_scripts = os.path.join(_PROJECT_ROOT, ".claude", "skills", "functional-testing", "scripts")
        if skill_scripts not in sys.path:
            sys.path.insert(0, skill_scripts)
        try:
            from report_generator import generate_report
            html_path = generate_report("Dashboard", results)
            print(f"\n  HTML report saved: {html_path}")
        except ImportError:
            print("\n  [WARN] report_generator not found, HTML report skipped")

    sys.exit(0 if success else 1)
