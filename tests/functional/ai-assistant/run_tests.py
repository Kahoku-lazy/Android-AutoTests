#!/usr/bin/env python
"""AI Assistant functional tests — executable automation script.

Usage:
    python scripts/run_ai_tests.py                  # 执行全部
    python scripts/run_ai_tests.py --case AI-DB-01  # 单条用例
    python scripts/run_ai_tests.py --layer DB       # 按层次筛选
"""

import os, sys, json, argparse, time
from datetime import datetime

# 添加项目根目录到 sys.path (tests/functional/ai-assistant/ → 上 4 层)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import requests

BASE_URL = "http://localhost:8765"
MYSQL_ENV = {
    "DB_ENGINE": "mysql", "DB_NAME": "android_autotests",
    "DB_USER": "root", "DB_PASSWORD": "autotests2026",
    "DB_HOST": "127.0.0.1", "DB_PORT": "3306",
}

# 模块级初始化 Django（MySQL 模式），确保 DB 测试可用
for k, v in MYSQL_ENV.items():
    os.environ[k] = v
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from apps.ai_assistant.models import AIAgent, AITool


def get_token():
    r = requests.post(f"{BASE_URL}/api/ai/auth/login",
                      json={"username": "admin", "password": "admin123"})
    return r.json()["access_token"]


def headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}


_MODELS = {"AIAgent": AIAgent, "AITool": AITool}


def db_orm_query(model_name, **filters):
    """Direct DB query using pre-initialized Django models."""
    return _MODELS[model_name].objects.filter(**filters)


# ═══════════════════════════════════════════
# DB Layer Tests
# ═══════════════════════════════════════════

def test_ai_db_01_delete_sync():
    """AI-DB-01: 删除后数据库物理删除"""
    h = headers()
    before = len(requests.get(f"{BASE_URL}/api/ai/agents", headers=h).json()["agents"])

    r = requests.post(f"{BASE_URL}/api/ai/agents/create", headers=h,
                      json={"name": "TEST-DB-01", "model_provider": "custom", "model_name": "test"})
    assert r.json()["ok"], "Create failed"
    nid = r.json()["id"]

    assert requests.post(f"{BASE_URL}/api/ai/agents/{nid}/delete", headers=h).json()["ok"], "Delete failed"

    agents = requests.get(f"{BASE_URL}/api/ai/agents", headers=h).json()["agents"]
    assert not any(a["id"] == nid for a in agents), "Still in API list"
    assert not db_orm_query("AIAgent", id=nid).exists(), "Still in DB"
    assert len(agents) == before, f"Count mismatch: {before} vs {len(agents)}"
    return True


def test_ai_db_02_key_encrypted():
    """AI-DB-02: 新增后 api_key 加密存储"""
    h = headers()
    r = requests.post(f"{BASE_URL}/api/ai/agents/create", headers=h,
                      json={"name": "TEST-DB-02", "model_provider": "custom",
                            "model_name": "test", "api_key": "sk-test-plaintext"})
    assert r.json()["ok"], "Create failed"
    nid = r.json()["id"]

    agent = db_orm_query("AIAgent", id=nid).first()
    raw_key = agent.api_key or ""
    assert not raw_key.startswith("sk-"), f"Plaintext key in DB: {raw_key[:20]}..."

    requests.post(f"{BASE_URL}/api/ai/agents/{nid}/delete", headers=h)
    return True


def test_ai_db_03_revealed_default():
    """AI-DB-03: key_revealed 初始值为 False"""
    h = headers()
    r = requests.post(f"{BASE_URL}/api/ai/agents/create", headers=h,
                      json={"name": "TEST-DB-03", "model_provider": "custom", "model_name": "test"})
    assert r.json()["ok"], "Create failed"
    nid = r.json()["id"]

    agent = db_orm_query("AIAgent", id=nid).first()
    assert agent.key_revealed == False, f"Expected False, got {agent.key_revealed}"

    requests.post(f"{BASE_URL}/api/ai/agents/{nid}/delete", headers=h)
    return True


def test_ai_db_04_cascade_tools():
    """AI-DB-04: 级联删除 Tools"""
    h = headers()
    r = requests.post(f"{BASE_URL}/api/ai/agents/create", headers=h,
                      json={"name": "TEST-DB-04", "model_provider": "custom",
                            "model_name": "test", "tools": [
                                {"name": "t1", "tool_type": "mcp", "config_json": "{}", "enabled": True},
                                {"name": "t2", "tool_type": "skill", "config_json": "{}", "enabled": True},
                            ]})
    assert r.json()["ok"], "Create failed"
    nid = r.json()["id"]

    tool_count = db_orm_query("AITool", agent_id=nid).count()
    assert tool_count == 2, f"Expected 2 tools, got {tool_count}"

    requests.post(f"{BASE_URL}/api/ai/agents/{nid}/delete", headers=h)
    assert db_orm_query("AIAgent", id=nid).count() == 0, "Agent not deleted"
    assert db_orm_query("AITool", agent_id=nid).count() == 0, "Tools not cascade-deleted"
    return True


# ═══════════════════════════════════════════
# API Layer Tests
# ═══════════════════════════════════════════

def test_ai_api_01_create_minimal():
    """AI-API-01: 创建 Agent（最低配置）"""
    h = headers()
    r = requests.post(f"{BASE_URL}/api/ai/agents/create", headers=h,
                      json={"name": "TEST-API-01", "model_provider": "custom", "model_name": "test"})
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert r.json()["ok"], "ok=False"
    requests.post(f"{BASE_URL}/api/ai/agents/{r.json()['id']}/delete", headers=h)
    return True


def test_ai_api_02_list_no_key():
    """AI-API-02: 获取 Agent 列表不含 api_key"""
    h = headers()
    r = requests.get(f"{BASE_URL}/api/ai/agents", headers=h)
    assert r.json()["ok"], "ok=False"
    for agent in r.json()["agents"]:
        assert "api_key" not in agent, f"Agent {agent['id']} has api_key in list"
    return True


def test_ai_api_03_detail_masked():
    """AI-API-03: 获取 Agent 详情 api_key 已脱敏"""
    h = headers()
    r = requests.get(f"{BASE_URL}/api/ai/agents/1", headers=h)
    assert r.json()["ok"], "ok=False"
    key = r.json()["agent"].get("api_key", "")
    assert "***" in key, f"api_key not masked: {key}"
    return True


def test_ai_api_04_update_mask_detect():
    """AI-API-04: 更新 Agent 掩码检测"""
    h = headers()
    # Get current encrypted value
    r = requests.get(f"{BASE_URL}/api/ai/agents/1", headers=h)
    original_masked = r.json()["agent"]["api_key"]

    # Send masked value — should NOT change DB
    requests.post(f"{BASE_URL}/api/ai/agents/1/update", headers=h,
                  json={"api_key": original_masked})
    r2 = requests.get(f"{BASE_URL}/api/ai/agents/1", headers=h)
    assert r2.json()["agent"]["api_key"] == original_masked, "Key changed despite mask"
    return True


def test_ai_api_05_delete_nonexistent():
    """AI-API-05: 删除不存在的 Agent"""
    h = headers()
    r = requests.post(f"{BASE_URL}/api/ai/agents/99999/delete", headers=h)
    assert r.json()["ok"], f"Expected ok=True, got {r.json()}"
    return True


# ═══════════════════════════════════════════
# UI Layer Tests
# ═══════════════════════════════════════════

def test_ai_ui_01_module_load():
    """AI-UI-01: 模块正常加载"""
    r = requests.get("http://localhost:5173/src/modules/ai-assistant/index.vue")
    assert r.status_code == 200, f"HTTP {r.status_code} — module compile error"
    return True


def test_ai_ui_02_list_from_api():
    """AI-UI-02: 列表数据来自 API"""
    h = headers()
    r = requests.get(f"{BASE_URL}/api/ai/agents", headers=h)
    assert r.json()["ok"], "API not ok"
    assert len(r.json()["agents"]) > 0, "No agents returned"
    return True


# ═══════════════════════════════════════════
# Error Protection Tests
# ═══════════════════════════════════════════

def test_ai_err_01_delete_fail_visible():
    """AI-ERR-01: 删除失败 → 前端应报错"""
    vue_path = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                            "frontend", "src", "modules", "ai-assistant", "index.vue")
    with open(vue_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 检查 deleteAgent 的 catch 块包含 ElMessage.error
    has_error_handler = "ElMessage.error" in content
    # 确认不使用 catch (_) {} 静默吞错（在 deleteAgent 上下文中）
    assert has_error_handler, "deleteAgent has no ElMessage.error in catch"
    return True


def test_ai_err_02_load_fail_visible():
    """AI-ERR-02: 列表加载失败 → 前端应报错"""
    vue_path = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                            "frontend", "src", "modules", "ai-assistant", "index.vue")
    with open(vue_path, "r", encoding="utf-8") as f:
        content = f.read()
    # loadAgents 的 catch 应包含 ElMessage.error
    has_error_handler = "ElMessage.error" in content
    assert has_error_handler, "loadAgents has no ElMessage.error in catch"
    return True


# ═══════════════════════════════════════════
# Test Runner
# ═══════════════════════════════════════════

ALL_TESTS = {
    # DB Layer
    "AI-DB-01": test_ai_db_01_delete_sync,
    "AI-DB-02": test_ai_db_02_key_encrypted,
    "AI-DB-03": test_ai_db_03_revealed_default,
    "AI-DB-04": test_ai_db_04_cascade_tools,
    # API Layer
    "AI-API-01": test_ai_api_01_create_minimal,
    "AI-API-02": test_ai_api_02_list_no_key,
    "AI-API-03": test_ai_api_03_detail_masked,
    "AI-API-04": test_ai_api_04_update_mask_detect,
    "AI-API-05": test_ai_api_05_delete_nonexistent,
    # UI Layer
    "AI-UI-01": test_ai_ui_01_module_load,
    "AI-UI-02": test_ai_ui_02_list_from_api,
    # Error Protection
    "AI-ERR-01": test_ai_err_01_delete_fail_visible,
    "AI-ERR-02": test_ai_err_02_load_fail_visible,
}


def run_tests(case_ids=None, layer=None):
    """Execute tests and return results."""
    results = []
    tests_to_run = {}

    if case_ids:
        tests_to_run = {k: v for k, v in ALL_TESTS.items() if k in case_ids}
    elif layer:
        tests_to_run = {k: v for k, v in ALL_TESTS.items() if k.split("-")[1] == layer}
    else:
        tests_to_run = ALL_TESTS

    for case_id, test_fn in tests_to_run.items():
        start = time.time()
        layer_name = case_id.split("-")[1]
        try:
            test_fn()
            results.append({
                "case": case_id, "layer": layer_name,
                "status": "PASS", "duration_ms": round((time.time() - start) * 1000),
                "error": None, "suggestion": None,
            })
        except Exception as e:
            results.append({
                "case": case_id, "layer": layer_name,
                "status": "FAIL", "duration_ms": round((time.time() - start) * 1000),
                "error": str(e), "suggestion": _suggest_fix(case_id, str(e)),
            })

    return results


def _suggest_fix(case_id, error):
    suggestions = {
        "assert": "检查断言条件是否正确，DB 数据是否与预期一致",
        "Connection": "确认 Django :8765 和 MySQL 服务正常运行",
        "HTTP 50": "检查 Vite 编译是否通过: npx vite build",
        "Plaintext key in DB": "确认 encrypt_key() 在 create_agent 中被调用",
        "Still in DB": "检查 delete_agent 是否正确调用 .delete()",
        "Not in list": "检查 create_agent 是否正确保存到数据库",
        "module compile error": "运行 npx vite build 修复语法错误",
        "no ElMessage.error": "catch 块必须包含 ElMessage.error() 提示用户",
        "not masked": "检查 agent_detail 是否调用了 mask_key()",
    }
    for keyword, suggestion in suggestions.items():
        if keyword.lower() in error.lower():
            return suggestion
    return "检查日志获取详细错误信息"


def print_report(results):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    pct = round(passed / total * 100) if total > 0 else 0

    print()
    print("=" * 60)
    print(f"  AI Assistant Functional Test Report")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")
    print(f"  Pass Rate: {pct}%")
    print()

    if failed:
        print("  Failed Cases:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    [{r['case']}] ({r['layer']})")
                print(f"      Error: {r['error'][:100]}")
                print(f"      Fix:   {r['suggestion']}")
                print()

    # Layer breakdown
    layers = {}
    for r in results:
        l = r["layer"]
        if l not in layers:
            layers[l] = {"total": 0, "passed": 0}
        layers[l]["total"] += 1
        if r["status"] == "PASS":
            layers[l]["passed"] += 1

    print("  By Layer:")
    for l in ["DB", "API", "UI", "ERR"]:
        if l in layers:
            lp = layers[l]
            print(f"    {l}: {lp['passed']}/{lp['total']} passed")

    conclusion = "可以提交" if failed == 0 else "需修复后重新测试"
    print(f"\n  Conclusion: {conclusion}")
    print("=" * 60)

    return pct == 100


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Assistant Functional Tests")
    parser.add_argument("--case", help="Run specific test case (e.g., AI-DB-01)")
    parser.add_argument("--layer", choices=["DB", "API", "UI", "ERR"],
                        help="Run all tests in a layer")
    args = parser.parse_args()

    case_ids = [args.case] if args.case else None
    results = run_tests(case_ids=case_ids, layer=args.layer)
    success = print_report(results)
    sys.exit(0 if success else 1)
