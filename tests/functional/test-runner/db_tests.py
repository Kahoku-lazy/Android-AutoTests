"""
Test-Runner DB 层测试 — 数据持久化验证.
"""
import sys, os, time
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path: sys.path.insert(0, _current_dir)
import helpers as H

# ═══════════════════════════════════════════════════════
#  TaskCard 持久化
# ═══════════════════════════════════════════════════════

def test_db_01_taskcard_created():
    """API create → DB 中有记录"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    import requests
    r = requests.post(f"{H.API_BASE}/runner/tasks/save", headers=h, json={
        "id": "TEST-DB-01", "name": "DB测试任务", "creator": "admin",
        "deviceSerial": "test", "caseIds": ["TC-001"], "loopCount": 2, "status": "idle",
    })
    H.register_cleanup("TEST-DB-01")
    TC = H.get_model("TaskCard")
    exists = TC.objects.filter(task_id="TEST-DB-01").exists() if TC else False
    passed = exists
    H.record("TR-DB-01", "DB", "TaskCard持久化创建", passed, f"exists={exists}", "exists=True", int((time.time()-t0)*1000))
    return passed

def test_db_02_taskcard_update():
    """API update → DB 字段已变更"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    import requests
    requests.post(f"{H.API_BASE}/runner/tasks/save", headers=h, json={
        "id": "TEST-DB-01", "name": "DB测试-已更新", "loopCount": 10, "status": "idle",
    })
    TC = H.get_model("TaskCard")
    tc = TC.objects.get(task_id="TEST-DB-01") if TC else None
    passed = tc and tc.name == "DB测试-已更新" and tc.loop_count == 10
    H.record("TR-DB-02", "DB", "TaskCard持久化更新", passed, f"name={tc.name if tc else 'N/A'}", "name=DB测试-已更新", int((time.time()-t0)*1000))
    return passed

def test_db_03_taskcard_status_transitions():
    """TaskCard status 字段变更"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    import requests
    TC = H.get_model("TaskCard")
    if not TC: return None
    # Create
    requests.post(f"{H.API_BASE}/runner/tasks/save", headers=h, json={
        "id": "TEST-DB-03", "name": "状态测试", "status": "idle", "creator": "admin",
    })
    H.register_cleanup("TEST-DB-03")
    # idle → queued → running → done
    for status in ["queued", "running", "done"]:
        requests.post(f"{H.API_BASE}/runner/tasks/save", headers=h, json={
            "id": "TEST-DB-03", "status": status,
        })
        tc = TC.objects.get(task_id="TEST-DB-03")
        if tc.status != status:
            H.record("TR-DB-03", "DB", f"status {status}", False, tc.status, status, int((time.time()-t0)*1000))
            return False
    passed = True
    H.record("TR-DB-03", "DB", "TaskCard状态转换 idle→queued→running→done", passed, "ok", "全部转换成功", int((time.time()-t0)*1000))
    return passed

def test_db_04_taskcard_delete():
    """API delete → DB 中已删除"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    import requests
    requests.post(f"{H.API_BASE}/runner/tasks/save", headers=h, json={
        "id": "TEST-DB-DEL", "name": "待删", "creator": "admin", "status": "idle",
    })
    requests.delete(f"{H.API_BASE}/runner/tasks/TEST-DB-DEL", headers=h)
    TC = H.get_model("TaskCard")
    exists = TC.objects.filter(task_id="TEST-DB-DEL").exists() if TC else True
    passed = not exists
    H.record("TR-DB-04", "DB", "TaskCard持久化删除", passed, f"exists={exists}", "exists=False", int((time.time()-t0)*1000))
    return passed

def test_db_05_testrunrecord_exists():
    """TestRunRecord 表存在"""
    if not H._django_ready: return None
    t0 = time.time()
    TRR = H.get_model("TestRunRecord")
    passed = TRR is not None
    H.record("TR-DB-05", "DB", "TestRunRecord 表存在", passed, f"model={'OK' if TRR else 'None'}", "存在", int((time.time()-t0)*1000))
    return passed

def test_db_06_testresult_model():
    """TestResult model FK to TestDefinition"""
    if not H._django_ready: return None
    t0 = time.time()
    TR = H.get_model("TestResult")
    passed = TR is not None
    H.record("TR-DB-06", "DB", "TestResult 模型存在", passed, f"model={'OK' if TR else 'None'}", "存在", int((time.time()-t0)*1000))
    return passed


ALL_DB_TESTS = [
    ("TR-DB-01", "DB", test_db_01_taskcard_created, "TaskCard创建"),
    ("TR-DB-02", "DB", test_db_02_taskcard_update, "TaskCard更新"),
    ("TR-DB-03", "DB", test_db_03_taskcard_status_transitions, "TaskCard状态转换"),
    ("TR-DB-04", "DB", test_db_04_taskcard_delete, "TaskCard删除"),
    ("TR-DB-05", "DB", test_db_05_testrunrecord_exists, "TestRunRecord存在"),
    ("TR-DB-06", "DB", test_db_06_testresult_model, "TestResult存在"),
]
for tid, layer, fn, desc in ALL_DB_TESTS:
    H.ALL_TESTS[tid] = (layer, fn, desc)
