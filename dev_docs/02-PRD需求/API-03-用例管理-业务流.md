# API-03 附录 — 业务流、参数溯源与状态机

> 关联：[API-03-用例管理](./API-03-用例管理.md) · [PRD-03](./PRD-03-用例管理.md)

---

## 一、参数来源标记说明

每个请求参数标注来源：

| 标记 | 含义 | 示例 |
|:--:|------|------|
| 🖊️ | 用户自定义（输入框、下拉） | title、category |
| 🔗 | 上一接口响应传递 | case_id ← POST /definitions 返回 |
| 🤖 | 后端自动生成，前端不传 | created_by、id（不传时） |
| 🔐 | JWT 自动注入，前端不传 | Authorization header |
| 📋 | 页面/路由参数 | URL 中的 case_id |
| 💾 | localStorage/sessionStorage | currentUser |

---

## 二、业务场景流（含参数溯源）

### 场景 1：创建 → 编辑 → 删除（完整生命周期）

```
┌─ 步骤 1: 查看目录树 ─────────────────────────────────────┐
│ GET /api/cases/directories                                 │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT (登录时存入 localStorage)    │
│ 请求体: 无                                                  │
│                                                             │
│ 响应: {ok, tree: [{id:1, name:"登录模块", ...}]}           │
│                                                             │
│ 产出参数: dir_id = 1  ← 🔗 供步骤2使用                     │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 2: 创建用例 ────────────────────────────────────────┐
│ POST /api/cases/definitions                                 │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT                              │
│ 请求体:                                                     │
│   title           ← 🖊️ 用户输入 "登录成功验证"              │
│   package_name    ← 🖊️ 用户输入 "com.example.app"           │
│   category        ← 🖊️ 用户输入 "login"                     │
│   priority        ← 🖊️ 用户选择 P0/P1/P2 (默认 P1)         │
│   description     ← 🖊️ 用户输入 (可选)                      │
│   steps_data      ← 🖊️ 用户在 StepEditor 拖拽编排          │
│   directory_id    ← 🔗 步骤1 的 tree[0].id                 │
│   enabled         ← 🖊️ 用户切换 (默认 true)                │
│   permission      ← 🖊️ 创建者选择 (默认 "edit")            │
│   visibility      ← 🖊️ 创建者选择 (默认 "public")          │
│   id              ← 不传 → 🤖 自动生成 TC-YYYYMMDD-...     │
│   created_by      ← 不传 → 🤖 JWT 用户名                   │
│   updated_by      ← 不传 → 🤖 JWT 用户名                   │
│                                                             │
│ 响应: {ok:true, id:"TC-20260717-150000-1234"}              │
│                                                             │
│ 产出参数: case_id = "TC-20260717-150000-1234" ← 🔗 后续用  │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 3: 列表刷新（自动）──────────────────────────────────┐
│ GET /api/cases/definitions?directory_id=1                   │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT                              │
│ 查询参数: directory_id ← 🔗 步骤1 产出 (可选，筛选目录)     │
│                                                             │
│ 响应: {ok, definitions: [{...卡片数据...}]}                 │
│ 卡片展示:                                                   │
│   "创建: admin · 07-17 15:00"  ← created_by(🤖)+created_at(🤖) │
│   "修改: admin · 07-17 15:00"  ← updated_by(🤖)+updated_at(🤖) │
│   🔒/🔓 锁定按钮              ← locked(🤖)                  │
│   👁️‍🗨️ 可见性图标             ← visibility(🖊️)              │
│   ✏️ 编辑状态                 ← editing_by(🤖)              │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 4: 打开编辑页 — 获取编辑锁 ─────────────────────────┐
│ POST /api/cases/definitions/{case_id}/lock                  │
│                                                             │
│ URL 参数: case_id ← 🔗 步骤2 产出 (或 📋 路由 params.id)   │
│ 请求体: 无                                                  │
│                                                             │
│ 响应: {ok:true, editing_by:"admin", editing_since:"..."}    │
│                                                             │
│ 产出参数: (无直接传递，但 editing_by 影响步骤3列表的显示)   │
│                                                             │
│ ⚠️ 若 permission=readonly 且非创建者 → 423 拒绝            │
│ ⚠️ 若 permission=restricted 且不在 permitted_editors → 423 │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 5: 编辑后保存 ──────────────────────────────────────┐
│ POST /api/cases/definitions                                 │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT                              │
│ 请求体:                                                     │
│   id              ← 🔗 步骤2 产出 case_id (必传，标识更新)  │
│   title           ← 🖊️ 用户修改 "登录成功验证(改)"          │
│   package_name    ← 🖊️ 保持不变                            │
│   steps_data      ← 🖊️ 在 StepEditor 中修改                │
│   directory_id    ← 🔗 步骤1 产出 (保持不变)                │
│   permission      ← 🖊️ 创建者可修改                        │
│   visibility      ← 🖊️ 创建者可修改                        │
│   updated_at      ← 🔗 步骤3 响应中的 updated_at (乐观锁)   │
│   priority        ← 🖊️ 用户可修改                          │
│   created_by      ← 不传 → 🤖 新建时已设，更新时不覆盖      │
│   updated_by      ← 不传 → 🤖 JWT 用户名 (自动更新)         │
│                                                             │
│ ⚠️ 若 updated_at 不匹配 → 409 冲突                         │
│                                                             │
│ 响应: {ok:true, id:"TC-..."}                                │
│                                                             │
│ 卡片更新: "修改: admin · 07-17 15:05" ← updated_by+时间    │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 6: 关闭编辑页 — 释放锁 ─────────────────────────────┐
│ POST /api/cases/definitions/{case_id}/unlock                │
│                                                             │
│ URL 参数: case_id ← 🔗 步骤2 产出                           │
│ 请求体: 无                                                  │
│                                                             │
│ 响应: {ok:true, released:true}                              │
│ editing_by → "" (🤖 自动清除)                               │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 7: 删除用例 ────────────────────────────────────────┐
│ DELETE /api/cases/definitions/{case_id}                     │
│                                                             │
│ URL 参数: case_id ← 🔗 步骤2 产出                           │
│ 请求体: 无                                                  │
│                                                             │
│ 响应: {ok:true}                                             │
└─────────────────────────────────────────────────────────────┘
```

**参数流转链**：
```
directories GET ──→ dir_id ──→ definitions POST ──→ case_id ──→ lock/unlock/delete
                                    │                            │
                                    └── definitions GET ←── updated_at (乐观锁)
```

---

### 场景 2：两人协作编辑

```
用户A: admin (创建者)                    用户B: tester (非创建者)
═══════════════════                     ═══════════════════════

A1. lock(用例X)
    case_id ← 🔗 之前创建的 case_id
    请求体: 无
    → 200 {editing_by:"admin"}

                                        B1. GET /definitions/{X}
                                            case_id ← 📋 路由 params.id
                                            → 200 {definition: {editing_by:"admin", ...}}
                                            卡片显示 "✏️ admin 正在编辑"

                                        B2. lock(用例X)
                                            case_id ← 📋 路由 params.id
                                            → 423 "用例正被 admin 编辑中"
                                            页面进入只读模式:
                                              editingBy ← 🔗 B1 的 editing_by
                                              isReadOnly ← true (前端本地状态)
                                              banner 显示 editingBy 的值

A2. 关闭页面
    unlock(用例X)
    case_id ← 🔗 A1 的 case_id
    → 200 {released:true}

                                        B3. 30s 自动刷新
                                            GET /definitions
                                            → editing_by:""
                                            卡片清除 "✏️" 标签

                                        B4. lock(用例X)
                                            case_id ← 📋 路由 params.id
                                            → 200 {editing_by:"tester"}
                                            正常编辑
```

**参数流转链（跨用户）**：
```
A: lock(id) → editing_by="admin" ──┐
                                    ├── B: GET → editing_by 显示在卡片
                                    ├── B: lock(id) → 423 (冲突参数来自 GET)
                                    │
A: unlock(id) → editing_by="" ──────┤
                                    │
                                    └── B: 30s刷新 GET → editing_by="" → lock 成功
```

---

### 场景 3：创建者强制踢出

```
用户A: admin (创建者)                    用户B: tester
═══════════════════                     ════════════════════

                                        B1. lock(用例X) → 200
                                            editing_by="tester"

A1. GET /definitions/{X}
    case_id ← 📋 路由
    → definition.created_by = "admin"  ← 🤖 创建时设定
    → definition.editing_by = "tester" ← 🤖 B1 设定

    前端判断: currentUser(💾 sessionStorage)
              === definition.created_by
              → 显示"强制编辑"按钮

A2. 强制踢出
    unlock(用例X, {force:true})
    case_id ← 📋 路由
    force   ← 🖊️ 用户点击按钮 (前端设为 true)
    → 200 {force_unlocked:true}

A3. lock(用例X)
    case_id ← 🔗 A2 的 case_id
    → 200 {editing_by:"admin"}

                                        B2. GET /definitions/{X}
                                            → editing_by="admin"
                                            只读模式
```

**关键参数溯源**：
```
created_by (A 身份标识)
  ← 🤖 definitions POST 时 JWT 自动写入
  ← 💾 CaseEditor: caseCreatedBy = d.created_by

force 参数
  ← 🖊️ 用户点击按钮触发 → forceEdit() → releaseEditLock(id, true)

currentUser 比较:
  ← 💾 sessionStorage.auth_active (登录时写入)
  ← 🔗 GET /definitions 的 definition.created_by
  匹配 → 显示"强制编辑"按钮
```

---

### 场景 4：权限控制 — 只读用例

```
用户A: admin (创建者)                    用户B: tester
═══════════════                     ════════════════════

A1. 创建用例（设为只读）
    POST /definitions
    title        ← 🖊️ "只读测试用例"
    permission   ← 🖊️ "readonly" (创建者从下拉选择)
    visibility   ← 🖊️ "public"
    其他字段     ← 🖊️ 用户输入
    → 200 {id:"TC-readonly-001"}

                                        B1. 列表查看
                                            GET /definitions
                                            → definitions 中包含该用例
                                            (visibility=public → 所有人可见)

                                        B2. 尝试编辑
                                            lock(TC-readonly-001)
                                            case_id ← 📋 路由
                                            → 423 "此用例为只读模式，仅创建者可编辑"

                                            后端检查:
                                              case.permission ← 🤖 A1 保存的值
                                              current_user   ← 🔐 JWT
                                              case.created_by≠current_user
                                              + permission="readonly"
                                              → 拒绝

A2. 修改权限为 restricted
    POST /definitions
    id                ← 🔗 A1 产出 case_id
    permission        ← 🖊️ "restricted"
    permitted_editors ← 🖊️ ["tester"] (输入框，逗号分隔)
    → 200

                                        B3. 再次尝试编辑
                                            lock(TC-readonly-001)
                                            → 200 (tester ∈ permitted_editors)

用户C: user3 (非授权)
                                        C1. lock(TC-readonly-001)
                                            → 423 "此用例仅限指定用户编辑"
                                            (user3 ∉ permitted_editors)
```

**权限检查参数溯源**：
```
permission 值:
  ← 🖊️ CaseEditor 下拉: edit / readonly / restricted
  ← 🔗 更新时传入 definitions POST

permitted_editors 值:
  ← 🖊️ CaseEditor 输入框 (逗号分隔 → JSON数组)
  ← 🔗 更新时传入 definitions POST

lock 端点权限检查:
  case.permission        ← 🤖 DB 存储值
  case.permitted_editors ← 🤖 DB 存储值
  current_user           ← 🔐 JWT → _resolve_username()
  case.created_by        ← 🤖 创建时存储
```

---

### 场景 5：目录权限

```
用户A: admin (创建目录)                  用户B: tester
═══════════════════                     ════════════════════

A1. 创建目录
    POST /directories/create
    name       ← 🖊️ "核心用例"
    parent_id  ← 🔗 上一级目录的 id (或 null=根)
    sort_order ← 🖊️ 0
    created_by ← 不传 → 🤖 JWT 用户名
    → 200 {directory:{id:10, name:"核心用例", created_by:"admin"}}

A2. 查看目录权限
    GET /directories
    → tree[0]: {id:10, created_by:"admin",
                allow_create:true, allow_delete:false}
    前端判断:
      currentUser(💾) === created_by → 显示"权限设置"菜单

A3. 设置目录权限
    POST /directories/10/permission
    dir_id        ← 🔗 A1 产出 10 (URL 参数)
    allow_create  ← 🖊️ false (创建者切换开关)
    allow_delete  ← 🖊️ false (默认)
    → 200

                                        B1. 查看目录
                                            GET /directories
                                            → tree[0]: {allow_create:false, ...}

                                            前端判断:
                                              currentUser(💾) !== created_by
                                              + allow_create=false
                                              → 右键菜单隐藏"新建子目录"
                                              → 右键菜单隐藏"新建用例"

                                              currentUser(💾) !== created_by
                                              + allow_delete=false
                                              → 右键菜单隐藏"删除"

A4. 删除自己的目录
    POST /directories/10
    action ← 🖊️ "delete"
    → 200 (创建者)

                                        B2. 尝试删除
                                            POST /directories/10
                                            action ← 🖊️ "delete"
                                            → 403 "只有目录创建者（admin）可以删除"

                                            后端检查:
                                              dir.created_by ← 🤖 A1 存储
                                              deleted_by     ← 🔐 JWT
                                              dir.allow_delete = false
                                              created_by ≠ deleted_by
                                              → 403
```

**目录权限参数溯源**：
```
allow_create / allow_delete:
  ← 🖊️ 目录创建者在权限设置面板切换
  ← 🔗 POST /directories/{id}/permission 传入

删除权限检查:
  dir.created_by  ← 🤖 A1 create_directory 时写入
  deleted_by      ← 🔐 JWT → _resolve_username()
  dir.allow_delete ← 🤖 DB (默认 false，创建者可改为 true)

前端菜单过滤:
  currentUser     ← 💾 sessionStorage.auth_active
  tree[].created_by ← 🔗 GET /directories 返回
  比较 → 决定是否显示"权限设置"菜单
  tree[].allow_create/allow_delete → 决定是否显示创建/删除菜单项
```

---

### 场景 6：YAML 导出

```
┌─ 步骤 1: 勾选与导出 ──────────────────────────────────────┐
│ POST /api/cases/export/yaml                                │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT                              │
│ 请求体:                                                     │
│   test_case_name ← 🖊️ 用户输入 (可选, 默认 "auto_test")    │
│   page_ids       ← 🖊️ 勾选页面 ID 列表 (可选, 不传=全部)   │
│                                                             │
│ 响应: {ok:true, filename:"回归测试_20260717.yaml",          │
│         yaml:"test_case:\n  name:..."}                      │
│                                                             │
│ 产出参数: filename ← 🔗 供步骤2下载                          │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 2: 下载文件 ────────────────────────────────────────┐
│ GET /api/cases/exports/{filename}                           │
│                                                             │
│ URL 参数: filename ← 🔗 步骤1 响应中的 filename             │
│ 请求头: 无（下载链接无需鉴权）                               │
│                                                             │
│ 响应: YAML 文件流 (Content-Type: application/x-yaml)        │
│                                                             │
│ ⚠️ 文件不存在 → 404                                         │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 3: 查看历史导出列表 ─────────────────────────────────┐
│ GET /api/cases/exports                                      │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT                              │
│                                                             │
│ 响应: {ok:true, files:[{name,size,time},...]}               │
└─────────────────────────────────────────────────────────────┘
```

**参数流转链**：
```
export/yaml POST → filename → exports/{filename} GET (下载)
                           → exports GET (列表展示)
```

---

### 场景 7：批量导入

```
┌─ 步骤 1: 选择目录 ────────────────────────────────────────┐
│ GET /api/cases/directories                                  │
│                                                             │
│ 响应: tree[n].id → 🔗 目标目录 ID                           │
│   ← 🖊️ 用户在导入界面选择                                   │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 2: 解析 YAML + 导入 ─────────────────────────────────┐
│ POST /api/cases/definitions/batch                           │
│                                                             │
│ 请求头: Authorization ← 🔐 JWT                              │
│ 请求体:                                                     │
│   cases         ← 🖊️ 前端从 YAML 文件解析出的用例数组       │
│   overwrite     ← 🖊️ 用户勾选 "覆盖已存在" (默认 false)    │
│   directory_id  ← 🔗 步骤1 选择的目标目录 ID                │
│   package_name  ← 🖊️ 用户输入 或 YAML 中提取               │
│                                                             │
│ 约束: cases ≤ 500 项                                        │
│                                                             │
│ 响应: {ok:true, imported:["TC-001","TC-002"],              │
│         skipped:["TC-003"], failed:[]}                      │
│                                                             │
│ 产出参数: imported ← 🔗 成功导入的 ID 列表                  │
│                                                             │
│ ⚠️ cases 超 500 → 400                                      │
│ ⚠️ overwrite=false + ID 已存在 → 记入 skipped（不报错）     │
│ ⚠️ YAML 格式错误 → 前端解析时拦截（不发请求）               │
└─────────────────────────────────────────────────────────────┘

┌─ 步骤 3: 刷新列表 ────────────────────────────────────────┐
│ GET /api/cases/definitions?directory_id={dir_id}            │
│                                                             │
│ 新导入用例出现在卡片列表中                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、参数来源汇总

### 前端参数获取方式一览

| 参数 | 来源 | 获取方式 | 示例值 |
|------|:--:|------|------|
| `Authorization` | 🔐 JWT | 登录时写入 localStorage → axios 拦截器自动附加 | `Bearer eyJ...` |
| `currentUser` | 💾 | `sessionStorage.auth_active` → fallback `localStorage.auth_accounts` | `"admin"` |
| `case_id` (编辑页) | 📋 | `route.params.id` | `"TC-20260717-..."` |
| `case_id` (新建后) | 🔗 | `POST /definitions` 响应 `data.id` → `form.value.id` | 同上 |
| `dir_id` | 🔗 | `GET /directories` 响应 `tree[].id` → `form.directory_id` | `1` |
| `updated_at` | 🔗 | `GET /definitions` 响应 `definition.updated_at` → `form.updated_at` | `"2026-07-17 15:00:00"` |
| `created_by` | 🤖 | `GET /definitions` 响应 `definition.created_by` → 展示 + 权限比较 | `"admin"` |
| `editing_by` | 🤖 | `GET /definitions` 响应 → CaseCard 状态标签 | `"tester"` |
| `title/category/...` | 🖊️ | 表单输入框/下拉/开关 | 用户自定义 |
| `steps_data` | 🖊️ | StepEditor 组件拖拽编排 | `[{type:"click",...}]` |
| `permission` | 🖊️ | CaseEditor 下拉选择 → form.permission | `"readonly"` |
| `permitted_editors` | 🖊️ | CaseEditor 输入框 → 逗号分隔 → JSON数组 | `["tester"]` |
| `visibility` | 🖊️ | CaseEditor 下拉选择 → form.visibility | `"hidden"` |
| `permitted_users` | 🖊️ | CaseEditor 输入框 → 逗号分隔 → JSON数组 | `["tester"]` |
| `force` (unlock) | 🖊️ | 前端 forceEdit() 方法硬编码 `true` | `true` |
| `allow_create` | 🖊️ | 目录权限面板开关 | `false` |
| `allow_delete` | 🖊️ | 目录权限面板开关 | `true` |

### 后端自动生成参数

| 参数 | 生成方式 | 时机 |
|------|------|------|
| `id` | `TC-{date}-{time}-{4位随机数字}` | 新建时不传 id |
| `created_at` | Django `auto_now_add` | 首次 INSERT |
| `updated_at` | Django `auto_now` | 每次 SAVE |
| `created_by` | `_resolve_username(request.user_id)` | 首次创建 |
| `updated_by` | `_resolve_username(request.user_id)` | 每次保存 |
| `editing_by` | `_resolve_username(request.user_id)` | lock 端点 |
| `editing_since` | `datetime.now()` | lock 端点 |
| `steps` | 从 steps_data 自动生成文本摘要 | 保存时 |
| `directory_name` | 关联查询 CaseDirectory.name | 序列化时 |
