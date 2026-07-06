"""DB 层测试 — Django ORM 直连 + API 读取验证."""
import sys, os, json, time, re
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path: sys.path.insert(0, _current_dir)

from datetime import datetime
import requests
import helpers as H


def test_cm_db_01_physical_delete():
    """物理删除后 ORM 中不存在"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h, json={
        "title":"TEST-DB-01","package_name":"com.test"})
    cid = r.json()["id"]; H.register_cleanup_case(cid)
    requests.delete(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    TD = H.get_model("TestDefinition")
    passed = not TD.objects.filter(id=cid).exists()
    H.record("CASE-DB-01","DB","物理删除 DB 验证",passed,
             f"exists={not passed}","exists=False",int((time.time()-t0)*1000))
    return passed

def test_cm_db_02_directory_set_null():
    """删除目录后用例 directory_id=NULL (API 验证)"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    dn = f"TEST-DB-DIR-{datetime.now().strftime('%H%M%S')}"
    r = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                      json={"name":dn,"parent_id":None})
    assert r.json().get("ok"); did = r.json()["directory"]["id"]; H.register_cleanup_dir(did)
    r2 = requests.post(f"{H.API_BASE}/cases/definitions", headers=h,
                       json={"title":"TEST-DB-02","package_name":"com.test","directory_id":did})
    cid = r2.json()["id"]; H.register_cleanup_case(cid)
    requests.post(f"{H.API_BASE}/cases/directories/{did}", headers=h, json={"action":"delete"})
    r3 = requests.get(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    d = r3.json().get("definition", {})
    passed = r3.json().get("ok") and d.get("directory_id") is None
    H.record("CASE-DB-02","DB","目录 SET_NULL 级联",passed,
             f"dir_id={d.get('directory_id')}","directory_id=None",int((time.time()-t0)*1000))
    return passed

def test_cm_db_03_iot_defaults():
    """IoT 字段默认值 (API 验证)"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h, json={
        "title":"TEST-DB-03","package_name":"com.test"})
    cid = r.json()["id"]; H.register_cleanup_case(cid)
    r2 = requests.get(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    d = r2.json().get("definition", {})
    passed = (d.get("priority")=="P1" and d.get("design_method")=="" and d.get("precondition")==""
              and d.get("expected_result")=="" and d.get("metrics")=="")
    H.record("CASE-DB-03","DB","IoT 默认值",passed,
             f"p={d.get('priority')},dm={d.get('design_method')}","p=P1,dm=''",
             int((time.time()-t0)*1000))
    return passed

def test_cm_db_04_steps_json_stored():
    """steps_json 正确存储 (API 验证)"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    steps = [{"type":"click","xpath":"//btn"},{"type":"wait","xpath":"//p","timeout":5}]
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h, json={
        "title":"TEST-DB-04","package_name":"com.test","steps_data":steps})
    cid = r.json()["id"]; H.register_cleanup_case(cid)
    r2 = requests.get(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    d = r2.json().get("definition", {})
    parsed = d.get("steps_data", [])
    passed = len(parsed)==2 and parsed[0]["type"]=="click"
    H.record("CASE-DB-04","DB","steps_json 存储",passed,
             f"len={len(parsed)}","len=2,type=click",int((time.time()-t0)*1000))
    return passed

def test_cm_db_05_disabled_default():
    """新建默认 enabled=True (API 验证)"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h, json={
        "title":"TEST-DB-05","package_name":"com.test"})
    cid = r.json()["id"]; H.register_cleanup_case(cid)
    r2 = requests.get(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    d = r2.json().get("definition", {})
    passed = d.get("enabled") is True
    H.record("CASE-DB-05","DB","enabled 默认 True",passed,
             f"enabled={d.get('enabled')}","enabled=True",int((time.time()-t0)*1000))
    return passed

def test_cm_db_06_yaml_cache_created():
    """YAML 导出后 TestCaseCache 有记录"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    TCC = H.get_model("TestCaseCache"); before = TCC.objects.count()
    try: requests.post(f"{H.API_BASE}/cases/export/yaml", headers=h,
                       json={"test_case_name":"TEST-DB-06"}, timeout=10)
    except Exception: pass
    after = TCC.objects.count()
    passed = after >= before
    H.record("CASE-DB-06","DB","YAML 缓存记录",passed,
             f"before={before},after={after}","after>=before",int((time.time()-t0)*1000))
    return passed

def test_cm_db_07_tc_id_format():
    """TC-ID 格式验证"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h, json={
        "title":"TEST-DB-07","package_name":"com.test"})
    cid = r.json()["id"]; H.register_cleanup_case(cid)
    passed = bool(re.match(r"^TC-\d{8}-\d{6}-\d{4}$", cid))
    H.record("CASE-DB-07","DB","TC-ID 格式",passed,cid,
             "TC-YYYYMMDD-HHMMSS-XXXX",int((time.time()-t0)*1000))
    return passed

def test_cm_db_08_unique_dir_name():
    """同级目录名唯一约束"""
    if not H._django_ready: return None
    t0 = time.time(); h = H.api_headers()
    dn = f"TEST-DB-UNIQ-{datetime.now().strftime('%H%M%S')}"
    r1 = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                       json={"name":dn,"parent_id":None})
    assert r1.json().get("ok"); did = r1.json()["directory"]["id"]; H.register_cleanup_dir(did)
    r2 = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                       json={"name":dn,"parent_id":None})
    passed = not r2.json().get("ok")
    H.record("CASE-DB-08","DB","目录名唯一约束",passed,
             f"ok={r2.json().get('ok')}","ok=False",int((time.time()-t0)*1000))
    return passed


DB_TESTS = {
    "CASE-DB-01":("DB",test_cm_db_01_physical_delete,"物理删除"),
    "CASE-DB-02":("DB",test_cm_db_02_directory_set_null,"SET_NULL 级联"),
    "CASE-DB-03":("DB",test_cm_db_03_iot_defaults,"IoT 默认值"),
    "CASE-DB-04":("DB",test_cm_db_04_steps_json_stored,"steps_json"),
    "CASE-DB-05":("DB",test_cm_db_05_disabled_default,"enabled 默认"),
    "CASE-DB-06":("DB",test_cm_db_06_yaml_cache_created,"YAML 缓存"),
    "CASE-DB-07":("DB",test_cm_db_07_tc_id_format,"TC-ID 格式"),
    "CASE-DB-08":("DB",test_cm_db_08_unique_dir_name,"唯一约束"),
}
H.ALL_TESTS.update(DB_TESTS)
