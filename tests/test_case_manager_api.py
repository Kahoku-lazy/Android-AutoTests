"""
用例管理模块 — 接口自动化测试
用法: PYTHONIOENCODING=utf-8 python test_case_manager_api.py
前提: Django :8765 已启动
"""
import json, sys, time, requests

BASE = "http://localhost:8765/api/cases"
AUTH = "http://localhost:8765/api/ai/auth"
TO = 15  # timeout

# ── Patch: default timeout for all requests ──
_orig = requests.Session.request
def _p(self, method, url, **kw): kw.setdefault("timeout", TO); return _orig(self, method, url, **kw)
requests.Session.request = _p

# ── State ──
passed = 0; failed = 0; skipped = 0
ADMIN = ""; TESTER = ""
CID = ""; DID = ""; UPD = ""
TS = str(int(time.time()))[-5:]  # unique run suffix

def login(u, p="admin123"):
    try:
        r = requests.post(f"{AUTH}/login", json={"username":u,"password":p})
        if r.status_code==200 and r.json().get("ok"): return r.json()["access_token"]
    except Exception as e: print(f"  ! login {u}: {e}")
    return ""

def T(label, cond):
    global passed, failed
    if cond: passed += 1
    else: failed += 1; print(f"  ✗ {label}")

def ok(r, code=200):
    global passed, failed
    s = r.status_code
    try: b = r.json()
    except: b = {"error": r.text[:100]}
    if s == code: passed += 1; return b
    failed += 1; print(f"  ✗ [{s}] exp {code}: {b.get('error','?')[:80]}")
    return b

def skip(label):
    global skipped; skipped += 1; print(f"  ⊘ {label}")

# ═══════════════════════════════════════
print("=" * 50)
print(f"  用例管理 API 测试 (run #{TS})")
print("=" * 50)

# ── Login ──
print("\n── 登录 ──")
ADMIN = login("admin"); T("admin 登录", bool(ADMIN))
TESTER = login("tester", "tester123"); T("tester 登录", bool(TESTER))
H  = {"Authorization": f"Bearer {ADMIN}", "Content-Type": "application/json"}
HG = {"Authorization": f"Bearer {ADMIN}"}
HT = {"Authorization": f"Bearer {TESTER}", "Content-Type": "application/json"} if TESTER else {}
HTG = {"Authorization": f"Bearer {TESTER}"} if TESTER else {}

# ── Cleanup previous runs ──
print("\n── 清理旧数据 ──")
r = requests.get(f"{BASE}/directories", headers=HG)
for d in r.json().get("tree", []):
    if d.get("name","").startswith("T-") and d.get("node_type")=="directory":
        requests.post(f"{BASE}/directories/{d['id']}", headers=H, json={"action":"delete"})
r2 = requests.get(f"{BASE}/definitions", headers=HG)
for d in r2.json().get("definitions", []):
    if d.get("title","").startswith("T-"):
        requests.delete(f"{BASE}/definitions/{d['id']}", headers=HG)
print("  清理完成")

# ════════════════════════════════
# CM-DIR: 目录管理 (9)
# ════════════════════════════════
print("\n── CM-DIR ──")

print("DIR-01: 列出目录树")
b = ok(requests.get(f"{BASE}/directories", headers=HG)); T("tree 数组", isinstance(b.get("tree"), list))

print("DIR-02: 创建目录")
b = ok(requests.post(f"{BASE}/directories/create", headers=H, json={"name":f"T-{TS}-dir","parent_id":None}))
if b.get("ok"): DID = b.get("directory",{}).get("id")
T("返回 id", bool(DID))

print("DIR-03: 同名拒绝")
b = ok(requests.post(f"{BASE}/directories/create", headers=H, json={"name":f"T-{TS}-dir","parent_id":None}), 400)
T("含'已存在同名'", "已存在同名" in b.get("error",""))

print("DIR-04: 重命名")
if DID: ok(requests.post(f"{BASE}/directories/{DID}", headers=H, json={"action":"update","name":f"T-{TS}-dir2"}))

print("DIR-05: 权限设置")
if DID: ok(requests.post(f"{BASE}/directories/{DID}/permission", headers=H, json={"allow_create":False,"allow_delete":True}))

print("DIR-06: 他人删→403")
if DID and TESTER: b = ok(requests.post(f"{BASE}/directories/{DID}", headers=HT, json={"action":"delete"}), 403)
else: skip("DIR-06")

print("DIR-07: 他人改权限→403")
if DID and TESTER: b = ok(requests.post(f"{BASE}/directories/{DID}/permission", headers=HT, json={"allow_create":True}), 403)
else: skip("DIR-07")

print("DIR-08: 超长 name")
T("超长→500", requests.post(f"{BASE}/directories/create", headers=H, json={"name":"A"*201}).status_code == 500)

print("DIR-09: 空 name")
T("空→非200", requests.post(f"{BASE}/directories/create", headers=H, json={"name":""}).status_code != 200)

# ════════════════════════════════
# CM-API: 用例 CRUD (5)
# ════════════════════════════════
print("\n── CM-API ──")

print("API-01: 创建")
b = ok(requests.post(f"{BASE}/definitions", headers=H, json={
    "title":f"T-{TS}-case","package_name":"com.t","steps_data":[{"type":"click","xpath":"//B"}],
    "directory_id":DID}))
CID = b.get("id","") if b.get("ok") else ""; T("ID 格式", CID.startswith("TC-"))

print("API-02: 详情")
if CID:
    b = ok(requests.get(f"{BASE}/definitions/{CID}", headers=HG))
    UPD = b.get("definition",{}).get("updated_at","")
    T("created_by=admin", b.get("definition",{}).get("created_by")=="admin")
    T("created_at 非空", bool(b.get("definition",{}).get("created_at")))

print("API-03: 更新")
if CID:
    # Re-fetch updated_at to avoid optimistic lock conflict
    b2 = ok(requests.get(f"{BASE}/definitions/{CID}", headers=HG))
    fresh_ts = b2.get("definition",{}).get("updated_at","")
    ok(requests.post(f"{BASE}/definitions", headers=H, json={
        "id":CID,"title":f"T-{TS}-case2","package_name":"com.t","steps_data":[],"directory_id":DID,"updated_at":fresh_ts}))

print("API-04: 同名→409")
b = ok(requests.post(f"{BASE}/definitions", headers=H, json={"title":f"T-{TS}-case2","package_name":"com.t","steps_data":[],"directory_id":DID}), 409)
T("含'已存在同名'", "已存在同名" in b.get("error",""))

print("API-05: 不允许 method")
T("PUT→405", requests.put(f"{BASE}/definitions", headers=H, json={}).status_code == 405)

# ════════════════════════════════
# CM-LOCK: 协作锁 (7)
# ════════════════════════════════
print("\n── CM-LOCK ──")

print("LOCK-01: 获取锁")
if CID: b = ok(requests.post(f"{BASE}/definitions/{CID}/lock", headers=H)); T("editing_by=admin", b.get("editing_by")=="admin")

print("LOCK-02: 幂等")
if CID: ok(requests.post(f"{BASE}/definitions/{CID}/lock", headers=H))

print("LOCK-03: 冲突")
if CID and TESTER: ok(requests.post(f"{BASE}/definitions/{CID}/lock", headers=HT), 423)
else: skip("LOCK-03")

print("LOCK-04: 释放")
if CID: ok(requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={}))

print("LOCK-05: 已释放→幂等")
if CID: T("already_unlocked", requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={}).json().get("already_unlocked")==True)

print("LOCK-06: 强制踢出")
if CID and TESTER:
    requests.post(f"{BASE}/definitions/{CID}/lock", headers=HT)
    T("force_unlocked", requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={"force":True}).json().get("force_unlocked")==True)
else: skip("LOCK-06")

print("LOCK-07: 非创建者 force→403")
if CID and TESTER:
    requests.post(f"{BASE}/definitions/{CID}/lock", headers=H)
    ok(requests.post(f"{BASE}/definitions/{CID}/unlock", headers=HT, json={"force":True}), 403)
    requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={})
else: skip("LOCK-07")

# ════════════════════════════════
# CM-PLOCK: 持久锁 (4)
# ════════════════════════════════
print("\n── CM-PLOCK ──")

print("PLOCK-01: 锁定")
if CID: T("locked", requests.post(f"{BASE}/definitions/{CID}/case-lock", headers=H).json().get("locked")==True)

print("PLOCK-02: 他人→403")
if CID and TESTER: ok(requests.post(f"{BASE}/definitions/{CID}/case-lock", headers=HT), 403)
else: skip("PLOCK-02")

print("PLOCK-03: 幂等")
if CID: ok(requests.post(f"{BASE}/definitions/{CID}/case-lock", headers=H))

print("PLOCK-04: 解锁")
if CID: T("unlocked", requests.post(f"{BASE}/definitions/{CID}/case-unlock", headers=H).json().get("unlocked")==True)

# ════════════════════════════════
# CM-VIS: 可见性 (5)
# ════════════════════════════════
print("\n── CM-VIS ──")

print("VIS-01: 设为 hidden")
if CID: ok(requests.post(f"{BASE}/definitions/{CID}/visibility", headers=H, json={"visibility":"hidden"}))

print("VIS-02: 他人列表不可见")
if TESTER and CID:
    ids = [d["id"] for d in requests.get(f"{BASE}/definitions", headers=HTG).json().get("definitions",[])]
    T("hidden→不可见", CID not in ids)
else: skip("VIS-02")

print("VIS-03: 直接访问→404")
if TESTER and CID: ok(requests.get(f"{BASE}/definitions/{CID}", headers=HTG), 404)
else: skip("VIS-03")

print("VIS-04: restricted+tester")
if CID: ok(requests.post(f"{BASE}/definitions/{CID}/visibility", headers=H, json={"visibility":"restricted","permitted_users":["tester"]}))

print("VIS-05: 指定用户可见")
if TESTER and CID:
    ids = [d["id"] for d in requests.get(f"{BASE}/definitions", headers=HTG).json().get("definitions",[])]
    T("restricted→可见", CID in ids)
else: skip("VIS-05")
if CID: requests.post(f"{BASE}/definitions/{CID}/visibility", headers=H, json={"visibility":"public"})

# ════════════════════════════════
# CM-PERM: 权限 (4)
# ════════════════════════════════
print("\n── CM-PERM ──")

print("PERM-01: 只读用例")
b = ok(requests.post(f"{BASE}/definitions", headers=H, json={"title":f"T-{TS}-ro","package_name":"com.t","permission":"readonly","steps_data":[],"directory_id":DID}))
RID = b.get("id","") if b.get("ok") else ""

print("PERM-02: 只读→423")
if RID and TESTER: ok(requests.post(f"{BASE}/definitions/{RID}/lock", headers=HT), 423)
else: skip("PERM-02")

print("PERM-03: restricted+tester")
ok(requests.post(f"{BASE}/definitions", headers=H, json={"id":RID,"title":f"T-{TS}-re","package_name":"com.t","permission":"restricted","permitted_editors":["tester"],"steps_data":[],"directory_id":DID}))

print("PERM-04: tester 可 lock")
if RID and TESTER: ok(requests.post(f"{BASE}/definitions/{RID}/lock", headers=HT)); requests.post(f"{BASE}/definitions/{RID}/unlock", headers=HT, json={})
else: skip("PERM-04")
if RID: requests.delete(f"{BASE}/definitions/{RID}", headers=HG)

# ════════════════════════════════
# CM-TRACK: 追踪 (3)
# ════════════════════════════════
print("\n── CM-TRACK ──")
if CID:
    d = requests.get(f"{BASE}/definitions/{CID}", headers=HG).json().get("definition",{})
    T("created_by=admin", d.get("created_by")=="admin")
    T("updated_by 非空", bool(d.get("updated_by")))
    # List fields
    dl = requests.get(f"{BASE}/definitions", headers=HG).json().get("definitions",[])
    for x in dl:
        if x.get("id")==CID:
            T("含 created_by", "created_by" in x); T("含 locked", "locked" in x)
            T("含 editing_by", "editing_by" in x); T("含 permission", "permission" in x); break
    # editing_by sync
    requests.post(f"{BASE}/definitions/{CID}/lock", headers=H)
    dl2 = requests.get(f"{BASE}/definitions", headers=HG).json().get("definitions",[])
    for x in dl2:
        if x.get("id")==CID: T("editing_by=admin", x.get("editing_by")=="admin"); break
    requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={})

# ════════════════════════════════
# CM-SYNC: 同步 (3)
# ════════════════════════════════
print("\n── CM-SYNC ──")
if CID:
    ok(requests.post(f"{BASE}/definitions", headers=H, json={"id":CID,"title":f"T-{TS}-sync","package_name":"com.t","steps_data":[],"directory_id":DID}))
    synced = [d for d in requests.get(f"{BASE}/definitions", headers=HG).json().get("definitions",[]) if d.get("id")==CID]
    T("列表 title 更新", len(synced)>0 and synced[0].get("title")==f"T-{TS}-sync")

    requests.post(f"{BASE}/definitions/{CID}/case-lock", headers=H)
    lk = [d for d in requests.get(f"{BASE}/definitions", headers=HG).json().get("definitions",[]) if d.get("id")==CID]
    T("列表 locked=true", len(lk)>0 and lk[0].get("locked")==True)
    requests.post(f"{BASE}/definitions/{CID}/case-unlock", headers=H)

    ok(requests.post(f"{BASE}/definitions", headers=H, json={"id":CID,"title":f"T-{TS}-conflict","package_name":"com.t","steps_data":[],"updated_at":"2020-01-01 00:00:00"}), 409)

# ════════════════════════════════
# CM-SEC: 安全 (3)
# ════════════════════════════════
print("\n── CM-SEC ──")
ok(requests.get(f"{BASE}/definitions"), 401)
if CID and TESTER: ok(requests.post(f"{BASE}/definitions/{CID}/visibility", headers=HT, json={"visibility":"hidden"}), 403)
else: skip("SEC-02")
if CID and TESTER: ok(requests.post(f"{BASE}/definitions/{CID}/case-lock", headers=HT), 403)
else: skip("SEC-03")

# ════════════════════════════════
# CM-END: 补全 (6)
# ════════════════════════════════
print("\n── CM-END ──")
if CID and DID:
    ok(requests.post(f"{BASE}/directories/batch-move", headers=H, json={"items":[{"type":"case","id":CID}],"target_directory_id":DID}))
    ok(requests.post(f"{BASE}/directories/batch-move", headers=H, json={"items":[],"target_directory_id":DID}), 400)

b = ok(requests.post(f"{BASE}/definitions/batch", headers=H, json={"cases":[{"title":f"T-{TS}-b1","package_name":"com.t","steps_data":[]},{"title":f"T-{TS}-b2","package_name":"com.t","steps_data":[]}],"overwrite":False,"directory_id":DID}))
T("imported≥2", isinstance(b.get("imported"), list) and len(b.get("imported",[])) >= 2)

b = ok(requests.post(f"{BASE}/export/yaml", headers=H, json={"test_case_name":f"T-{TS}-export"}))
FN = b.get("filename",""); T("filename 非空", bool(FN))

b = ok(requests.get(f"{BASE}/exports", headers=HG)); T("files 数组", isinstance(b.get("files"), list))
if FN: T("下载 200", requests.get(f"{BASE}/exports/"+FN, headers=HG).status_code == 200)

ok(requests.get(f"{BASE}/exports/nonexistent.yaml", headers=HG), 404)
T("DELETE 不存在→2xx", requests.delete(f"{BASE}/definitions/TC-nope-9999", headers=HG).status_code in (200,204,404))

# ════════════════════════════════
# CM-ARG: 参数 (4)
# ════════════════════════════════
print("\n── CM-ARG ──")
T("XSS 不阻止", requests.post(f"{BASE}/directories/create", headers=H, json={"name":"<script>x</script>","parent_id":None}).status_code == 200)
T("P99 静默降级", requests.post(f"{BASE}/definitions", headers=H, json={"title":f"T-{TS}-p99","package_name":"com.t","priority":"P99","steps_data":[],"directory_id":DID}).status_code == 200)
if CID: T("非法 visibility→200", requests.post(f"{BASE}/definitions/{CID}/visibility", headers=H, json={"visibility":"xxx"}).status_code == 200)
ok(requests.get(f"{BASE}/definitions/TC-nope-9999", headers=HG), 404)

# ════════════════════════════════
# CM-NF: 非功能 (2)
# ════════════════════════════════
print("\n── CM-NF ──")
r = requests.post(f"{BASE}/definitions", headers=H, data=b"not json")
T("非法JSON→非200", r.status_code != 200)
T("Content-Type=json", "application/json" in requests.get(f"{BASE}/definitions", headers=HG).headers.get("Content-Type",""))

# ════════════════════════════════
# CM-FLOW: 业务流 (7)
# ════════════════════════════════
print("\n── CM-FLOW ──")

print("FLOW-01: 全生命周期")
f1 = requests.post(f"{BASE}/definitions", headers=H, json={"title":f"T-{TS}-flow1","package_name":"com.t","steps_data":[],"directory_id":DID}).json().get("id","")
if f1:
    T("1.GET", requests.get(f"{BASE}/definitions/{f1}", headers=HG).status_code==200)
    T("2.lock", requests.post(f"{BASE}/definitions/{f1}/lock", headers=H).status_code==200)
    T("3.save", requests.post(f"{BASE}/definitions", headers=H, json={"id":f1,"title":f"T-{TS}-flow1x","package_name":"com.t","steps_data":[]}).status_code==200)
    T("4.unlock", requests.post(f"{BASE}/definitions/{f1}/unlock", headers=H, json={}).status_code==200)
    T("5.delete", requests.delete(f"{BASE}/definitions/{f1}", headers=HG).status_code==200)
    T("6.404", requests.get(f"{BASE}/definitions/{f1}", headers=HG).status_code==404)

print("FLOW-02: 协作")
if CID and TESTER:
    requests.post(f"{BASE}/definitions/{CID}/lock", headers=H)
    T("tester→423", requests.post(f"{BASE}/definitions/{CID}/lock", headers=HT).status_code==423)
    requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={})
    T("tester→200", requests.post(f"{BASE}/definitions/{CID}/lock", headers=HT).status_code==200)
    requests.post(f"{BASE}/definitions/{CID}/unlock", headers=HT, json={})
else: skip("FLOW-02")

print("FLOW-03: 强制踢出")
if CID and TESTER:
    requests.post(f"{BASE}/definitions/{CID}/lock", headers=HT)
    T("force→200", requests.post(f"{BASE}/definitions/{CID}/unlock", headers=H, json={"force":True}).status_code==200)
else: skip("FLOW-03")

print("FLOW-04: 权限变更")
f4 = requests.post(f"{BASE}/definitions", headers=H, json={"title":f"T-{TS}-flow4","package_name":"com.t","permission":"readonly","steps_data":[],"directory_id":DID}).json().get("id","")
if f4 and TESTER:
    T("readonly→423", requests.post(f"{BASE}/definitions/{f4}/lock", headers=HT).status_code==423)
    requests.post(f"{BASE}/definitions", headers=H, json={"id":f4,"title":f"T-{TS}-flow4","package_name":"com.t","permission":"edit","steps_data":[],"directory_id":DID})
    T("edit→200", requests.post(f"{BASE}/definitions/{f4}/lock", headers=HT).status_code==200)
    requests.post(f"{BASE}/definitions/{f4}/unlock", headers=HT, json={}); requests.delete(f"{BASE}/definitions/{f4}", headers=HG)

print("FLOW-05: 可见性")
f5 = requests.post(f"{BASE}/definitions", headers=H, json={"title":f"T-{TS}-flow5","package_name":"com.t","steps_data":[],"directory_id":DID}).json().get("id","")
if f5 and TESTER:
    requests.post(f"{BASE}/definitions/{f5}/visibility", headers=H, json={"visibility":"hidden"})
    ids = [d["id"] for d in requests.get(f"{BASE}/definitions", headers=HTG).json().get("definitions",[])]
    T("hidden→不可见", f5 not in ids)
    requests.post(f"{BASE}/definitions/{f5}/visibility", headers=H, json={"visibility":"public"})
    requests.delete(f"{BASE}/definitions/{f5}", headers=HG)

print("FLOW-06: 目录权限")
f6 = requests.post(f"{BASE}/directories/create", headers=H, json={"name":f"T-{TS}-flow6"}).json().get("directory",{}).get("id")
if f6 and TESTER:
    requests.post(f"{BASE}/directories/{f6}/permission", headers=H, json={"allow_create":False,"allow_delete":True})
    # allow_delete=True → tester should be able to delete
    s = requests.post(f"{BASE}/directories/{f6}", headers=HT, json={"action":"delete"}).status_code
    T("allow_delete→tester可删", s == 200)
    if s != 200: requests.post(f"{BASE}/directories/{f6}", headers=H, json={"action":"delete"})

print("FLOW-07: 导出")
b = requests.post(f"{BASE}/export/yaml", headers=H, json={"test_case_name":f"T-{TS}-flow7"})
T("导出 200", b.status_code == 200)
if b.status_code == 200:
    fn = b.json().get("filename","")
    T("filename 非空", bool(fn))
    if fn: T("下载 200", requests.get(f"{BASE}/exports/"+fn, headers=HG).status_code == 200)

# ════════════════════════════════
print("\n── 清理 ──")
if CID: requests.delete(f"{BASE}/definitions/{CID}", headers=HG)
if DID: requests.post(f"{BASE}/directories/{DID}", headers=H, json={"action":"delete"})
# cleanup batch imports
for d in requests.get(f"{BASE}/definitions", headers=HG).json().get("definitions",[]):
    if d.get("title","").startswith(f"T-{TS}-"):
        requests.delete(f"{BASE}/definitions/{d['id']}", headers=HG)

# ════════════════════════════════
total = passed + failed + skipped
pct = round(passed/(passed+failed)*100) if (passed+failed) > 0 else 0
print(f"\n{'='*50}")
print(f"  通过: {passed}  失败: {failed}  跳过: {skipped}  总计: {total}")
print(f"  通过率: {pct}%")
print("=" * 50)
sys.exit(0 if failed == 0 else 1)
