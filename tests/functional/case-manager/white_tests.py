"""白盒层测试 — 源码静态分析."""
import sys, os, time, re
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path: sys.path.insert(0, _current_dir)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path: sys.path.insert(0, _PROJECT_ROOT)

import requests
import helpers as H


def test_cm_white_01_no_hardcoded_password():
    """前端源码无硬编码密码"""
    t0 = time.time()
    d = os.path.join(_PROJECT_ROOT, "frontend/src/modules/case-manager")
    patterns = ["admin123", "autotests2026", r"password\s*=\s*'[^']+'"]
    violations = []
    for rt, _ds, files in os.walk(d):
        for fn in files:
            if fn.endswith((".vue",".js")):
                with open(os.path.join(rt,fn),"r",encoding="utf-8") as f: c = f.read()
                for p in patterns:
                    if re.search(p, c): violations.append(f"{fn}:{p}")
    passed = len(violations) == 0
    H.record("CASE-WHITE-01","WHITE","无硬编码凭据",passed,
             f"violations={len(violations)}","0",int((time.time()-t0)*1000))
    return passed

def test_cm_white_02_write_ops_report_error():
    """写操作 catch 含错误处理"""
    t0 = time.time()
    d = os.path.join(_PROJECT_ROOT, "frontend/src/modules/case-manager")
    key = ["components/DirectoryTree.vue","index.vue","CaseEditor.vue"]
    violations = []
    for fn in key:
        fp = os.path.join(d, fn)
        if not os.path.exists(fp): continue
        with open(fp,"r",encoding="utf-8") as f: c = f.read()
        if "deleteDirectory" in c or "deleteDefinition" in c:
            if "formatApiError" not in c and "ElMessage.error" not in c: violations.append(fn)
    passed = len(violations) == 0
    H.record("CASE-WHITE-02","WHITE","写操作错误处理",passed,
             f"violations={len(violations)}","0",int((time.time()-t0)*1000))
    return passed

def test_cm_white_03_no_api_key_in_response():
    """API 响应不含 api_key"""
    t0 = time.time(); h = H.api_headers()
    r = requests.get(f"{H.API_BASE}/cases/definitions", headers=h)
    passed = "api_key" not in r.text.lower()
    H.record("CASE-WHITE-03","WHITE","响应无 api_key",passed,
             "absent","absent",int((time.time()-t0)*1000))
    return passed

def test_cm_white_04_no_ref_hardcoded_data():
    """前端 ref 无硬编码假数据"""
    t0 = time.time()
    d = os.path.join(_PROJECT_ROOT, "frontend/src/modules/case-manager")
    pattern = r'ref\(\s*\[\s*\{'
    violations = []
    for rt, _ds, files in os.walk(d):
        for fn in files:
            if fn.endswith((".vue",".js")):
                with open(os.path.join(rt,fn),"r",encoding="utf-8") as f: c = f.read()
                if re.search(pattern, c): violations.append(fn)
    passed = len(violations) <= 1
    H.record("CASE-WHITE-04","WHITE","无硬编码假数据",passed,
             f"violations={len(violations)}","<=1",int((time.time()-t0)*1000))
    return passed


WHITE_TESTS = {
    "CASE-WHITE-01":("WHITE",test_cm_white_01_no_hardcoded_password,"无硬编码凭据"),
    "CASE-WHITE-02":("WHITE",test_cm_white_02_write_ops_report_error,"写操作错误处理"),
    "CASE-WHITE-03":("WHITE",test_cm_white_03_no_api_key_in_response,"响应无泄露"),
    "CASE-WHITE-04":("WHITE",test_cm_white_04_no_ref_hardcoded_data,"无假数据"),
}
H.ALL_TESTS.update(WHITE_TESTS)
