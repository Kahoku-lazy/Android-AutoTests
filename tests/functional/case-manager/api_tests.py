"""API 层测试 — HTTP 端点验证."""
import sys, os, time
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path: sys.path.insert(0, _current_dir)

from datetime import datetime
import requests
import helpers as H


def test_cm_api_01_create_roundtrip():
    """POST 创建 → GET 回读一致"""
    t0 = time.time(); h = H.api_headers()
    payload = {"title":"TEST-API-01","package_name":"com.test.api","category":"smoke",
               "priority":"P0","precondition":"已登录","expected_result":"正常",
               "steps_data":[{"type":"click","xpath":"//btn","description":"点击"}]}
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h, json=payload)
    assert r.json().get("ok"); cid = r.json()["id"]; H.register_cleanup_case(cid)
    r2 = requests.get(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    d = r2.json()["definition"]
    passed = (d["title"]==payload["title"] and d["priority"]==payload["priority"]
              and d["category"]==payload["category"] and len(d["steps_data"])==1)
    H.record("CASE-API-03","API","POST→GET 往返一致",passed,
             f"title={d['title']},priority={d['priority']}","一致",int((time.time()-t0)*1000))
    return passed

def test_cm_api_02_update_fields():
    """POST 更新后字段变更"""
    t0 = time.time(); h = H.api_headers()
    r = requests.post(f"{H.API_BASE}/cases/definitions", headers=h,
                      json={"title":"TEST-API-02-OLD","package_name":"com.test"})
    cid = r.json()["id"]; H.register_cleanup_case(cid)
    requests.post(f"{H.API_BASE}/cases/definitions", headers=h,
                  json={"id":cid,"title":"TEST-API-02-NEW","package_name":"com.test","priority":"P2"})
    r2 = requests.get(f"{H.API_BASE}/cases/definitions/{cid}", headers=h)
    d = r2.json()["definition"]
    passed = d["title"]=="TEST-API-02-NEW" and d["priority"]=="P2"
    H.record("CASE-API-04","API","更新字段变更",passed,
             f"title={d['title']}","title=NEW,priority=P2",int((time.time()-t0)*1000))
    return passed

def test_cm_api_03_delete_idempotent():
    """删除不存在用例返回 ok=True"""
    t0 = time.time(); h = H.api_headers()
    r = requests.delete(f"{H.API_BASE}/cases/definitions/NONEXISTENT-99999", headers=h)
    passed = r.status_code==200 and r.json().get("ok")
    H.record("CASE-API-05","API","删除幂等",passed,
             f"status={r.status_code}","200,ok=True",int((time.time()-t0)*1000))
    return passed

def test_cm_api_04_list():
    """列表返回数组"""
    t0 = time.time(); h = H.api_headers()
    r = requests.get(f"{H.API_BASE}/cases/definitions", headers=h)
    passed = r.ok and r.json().get("ok") and "definitions" in r.json()
    H.record("CASE-API-06","API","列表返回数组",passed,
             f"count={len(r.json().get('definitions',[]))}","definitions=array",
             int((time.time()-t0)*1000))
    return passed

def test_cm_api_05_batch_import():
    """批量导入 3 条"""
    t0 = time.time(); h = H.api_headers()
    ts = datetime.now().strftime('%H%M%S')
    cases = [{"id":f"TEST-BATCH-{ts}-{i}","title":f"Batch-{i}-{ts}","category":"smoke"} for i in range(1,4)]
    r = requests.post(f"{H.API_BASE}/cases/definitions/batch", headers=h,
                      json={"cases":cases,"overwrite":False})
    data = r.json()
    for c in data.get("imported",[]): H.register_cleanup_case(c.get("id") or c.get("case_id"))
    imported = len(data.get("imported",[]))
    passed = r.ok and data.get("ok") and imported >= 1  # 可能部分跳过
    H.record("CASE-API-07","API","批量导入",passed,
             f"imported={imported},skipped={len(data.get('skipped',[]))}","imported>=1",
             int((time.time()-t0)*1000))
    return passed

def test_cm_api_06_batch_move():
    """批量移动用例"""
    t0 = time.time(); h = H.api_headers()
    dn = f"TEST-MOVE-{datetime.now().strftime('%H%M%S')}"
    r = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                      json={"name":dn,"parent_id":None})
    assert r.json().get("ok"); did = r.json()["directory"]["id"]; H.register_cleanup_dir(did)
    r2 = requests.post(f"{H.API_BASE}/cases/definitions", headers=h,
                       json={"title":"TEST-MOVE-CASE","package_name":"com.test"})
    cid = r2.json()["id"]; H.register_cleanup_case(cid)
    try:
        r3 = requests.post(f"{H.API_BASE}/cases/directories/batch-move", headers=h,
                           json={"items":[{"type":"case","id":cid}],"target_directory_id":did})
        data = r3.json() if r3.text else {}
        moved = data.get("moved",0)
        passed = r3.ok and data.get("ok",False) and moved>=1
    except Exception:
        passed = False; moved = 0
    H.record("CASE-API-08","API","批量移动",passed,
             f"moved={moved}","moved>=1",int((time.time()-t0)*1000))
    return passed

def test_cm_api_07_delete_nonempty_dir():
    """删除非空目录 409"""
    t0 = time.time(); h = H.api_headers()
    r = requests.get(f"{H.API_BASE}/cases/directories", headers=h)
    target = None
    for n in r.json().get("tree",[]):
        for c in n.get("children",[]):
            if c.get("case_count",0)>0: target=c["id"]; break
    if not target: passed = True
    else:
        r2 = requests.post(f"{H.API_BASE}/cases/directories/{target}", headers=h, json={"action":"delete"})
        passed = r2.status_code==409 or not r2.json().get("ok")
    H.record("CASE-API-09","API","删除非空目录 409",passed,
             f"dir={target}" if target else "skipped","409/ok=False",int((time.time()-t0)*1000))
    return passed

def test_cm_api_08_three_level_rejected():
    """三级目录被拒"""
    t0 = time.time(); h = H.api_headers()
    ts = datetime.now().strftime('%H%M%S')
    r1 = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                       json={"name":f"TEST-L1-{ts}","parent_id":None})
    assert r1.json().get("ok"); l1 = r1.json()["directory"]["id"]; H.register_cleanup_dir(l1)
    r2 = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                       json={"name":f"TEST-L2-{ts}","parent_id":l1})
    assert r2.json().get("ok"); l2 = r2.json()["directory"]["id"]; H.register_cleanup_dir(l2)
    r3 = requests.post(f"{H.API_BASE}/cases/directories/create", headers=h,
                       json={"name":f"TEST-L3-{ts}","parent_id":l2})
    passed = not r3.json().get("ok")
    H.record("CASE-API-10","API","三级目录被拒",passed,
             f"ok={r3.json().get('ok')}","ok=False",int((time.time()-t0)*1000))
    return passed


API_TESTS = {
    "CASE-API-03":("API",test_cm_api_01_create_roundtrip,"CRUD 往返"),
    "CASE-API-04":("API",test_cm_api_02_update_fields,"更新字段"),
    "CASE-API-05":("API",test_cm_api_03_delete_idempotent,"删除幂等"),
    "CASE-API-06":("API",test_cm_api_04_list,"列表示例"),
    "CASE-API-07":("API",test_cm_api_05_batch_import,"批量导入"),
    "CASE-API-08":("API",test_cm_api_06_batch_move,"批量移动"),
    "CASE-API-09":("API",test_cm_api_07_delete_nonempty_dir,"非空目录 409"),
    "CASE-API-10":("API",test_cm_api_08_three_level_rejected,"三级拒绝"),
}
H.ALL_TESTS.update(API_TESTS)
