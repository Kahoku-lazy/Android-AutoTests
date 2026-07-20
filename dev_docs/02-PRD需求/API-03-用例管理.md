# API-03 — 用例管理接口文档

> 模块：`apps/case_manager/` · 端点：16 个 · 基础路径：`/api/cases`
> 版本：v2.0 · 日期：2026-07-17

---

## 通用约定

### 请求头

| Header | 值 | 必填 | 说明 |
|------|------|:--:|------|
| `Content-Type` | `application/json` | ✅ | 所有 POST/PUT |
| `Authorization` | `Bearer <JWT>` | ✅ | 除 `/exports/{filename}` 外全部 |

### 响应格式

```json
// 成功
{"ok": true,  ...}

// 失败 — 统一格式
{"ok": false, "error": "人类可读的中文描述"}
```

### 错误码速查

| HTTP 状态码 | 含义 | 触发场景 |
|:--:|------|------|
| `400` | 请求参数错误 | 缺少必填字段、值不合法、设备离线 |
| `401` | 未登录 | 无 Authorization 头或 Token 过期 |
| `403` | 无权限 | 非创建者操作锁定/删除/可见性 |
| `404` | 资源不存在 | 用例/目录 ID 无效 |
| `405` | 方法不允许 | 用了 GET 访问 POST 端点 |
| `409` | 冲突 | 乐观锁冲突、同目录重名、设备已被锁定 |
| `423` | 资源锁定 | 编辑锁冲突、只读模式、指定用户限编辑 |
| `500` | 服务器内部错误 | 非预期异常（联系管理员） |

### 参数校验错误：传入非法值时的响应

以下错误**不区分端点**，由 Django / JSON 解析层统一返回。

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| JSON 格式非法（如缺少引号、括号） | `400` | `{"ok": false, "error": "无效的 JSON"}` |
| 必填字段为空（title=""） | `400` | `{"ok": false, "error": "user_id 不能为空"}` 或通过前端校验拦截 |
| 布尔字段传字符串（"true"而非 true） | `400` | JSON 解析失败 → `"无效的 JSON"` |
| int 字段传字符串（"abc"而非数字） | `400` | JSON 解析失败 → `"无效的 JSON"` |
| 枚举值非法（priority="P99"） | `400` | **静默降级为默认值 P1**（Django choices 特性） |
| 枚举值非法（visibility="deleted"） | `400` | 同上（静默降级） |
| 字段超长（title=500字符+1） | `500` | 数据库报错 → `{"ok": false, "error": "服务器内部错误"}` |
| URL 路径参数非法（dir_id="abc"） | `404` | Django 路由不匹配 → 或返回 Not Found |

### 自动生成字段

以下字段由后端自动填充，前端**传了也会被忽略**：

| 字段 | 生成时机 | 生成值 |
|------|------|------|
| `id` | 新建时（若不传） | `TC-YYYYMMDD-HHMMSS-NNNN`（随机4位数字） |
| `created_at` | 新建时 | Django `auto_now_add` |
| `updated_at` | 每次保存 | Django `auto_now` |
| `created_by` | 新建时 | JWT 当前用户名 |
| `updated_by` | 每次保存 | JWT 当前用户名 |
| `editing_by` | 获取编辑锁时 | JWT 当前用户名 |
| `editing_since` | 获取编辑锁时 | 服务器当前时间 |

---

## 1. 目录管理

### 1.1 列出目录树

```
GET /api/cases/directories
```

无请求体、无查询参数。

**响应** `200`：
```json
{
  "ok": true,
  "tree": [
    {
      "id": 1,                          // int, 自增, 自动生成
      "name": "登录模块",                // string, ≤200, 必填
      "parent_id": null,                // int|null, null=根级
      "sort_order": 0,                  // int, 默认0
      "node_type": "directory",         // string, 固定值
      "case_count": 5,                  // int, 自动计算
      "created_by": "admin",            // string, 自动生成
      "allow_create": true,             // bool, 默认true
      "allow_delete": false,            // bool, 默认false
      "children": [...]                 // 子目录+用例节点
    }
  ]
}
```

---

### 1.2 创建目录

```
POST /api/cases/directories/create
```

**请求体参数**：

| 参数 | 类型 | 必填 | 长度 | 默认值 | 约束 |
|------|:--:|:--:|:--:|------|------|
| `name` | string | ✅ | 1-200 | — | 同级唯一（父级+名称） |
| `parent_id` | int|null | — | — | null | null=根目录；最多2级 |
| `sort_order` | int | — | — | 0 | |

**请求体**：
```json
{"name": "登录模块", "parent_id": null, "sort_order": 0}
```

**响应** `200`：
```json
{"ok": true, "directory": {"id": 1, "name": "登录模块", "parent_id": null}}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| `name` 为空或纯空格 | `400` | `{"ok": false, "error": "该层级下已存在同名目录: "}` 或前端拦截 |
| 同级重复 `name` | `400` | `{"ok": false, "error": "该层级下已存在同名目录: 登录模块"}` |
| `parent_id` 指向自身 | `500` | `{"ok": false, "error": "服务器内部错误"}` |
| `name` 超 200 字符 | `500` | `{"ok": false, "error": "服务器内部错误"}` |

---

### 1.3 目录更新/删除

```
POST /api/cases/directories/{dir_id}
```

| URL 参数 | 类型 | 必填 | 说明 |
|------|:--:|:--:|------|
| `dir_id` | int | ✅ | 目录ID（路径参数） |

**更新请求体**：

| 参数 | 类型 | 必填 | 长度 | 约束 |
|------|:--:|:--:|:--:|------|
| `action` | string | — | — | 默认"update"；也可"delete" |
| `name` | string | — | 1-200 | 同级唯一 |
| `parent_id` | int|null | — | — | null=根级 |
| `sort_order` | int | — | — | |

```json
{"action": "update", "name": "新名称", "parent_id": null, "sort_order": 1}
```

**删除请求体**：
```json
{"action": "delete"}
```

**错误** `403`：
```json
{"ok": false, "error": "只有目录创建者（admin）可以删除此目录"}
```

**错误** `400`：
```json
{"ok": false, "error": "目录下存在子目录或用例，请先清空后再删除"}
```

---

### 1.4 目录权限设置 🆕

```
POST /api/cases/directories/{dir_id}/permission
```

**权限**：仅目录创建者

**请求体参数**：

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|:--:|:--:|------|------|
| `allow_create` | bool | — | true | 他人是否可创建子目录/用例 |
| `allow_delete` | bool | — | false | 他人是否可删除此目录 |

**请求体**：
```json
{"allow_create": false, "allow_delete": true}
```

**响应** `200`：`{"ok": true}`

**错误** `403`：`{"ok": false, "error": "只有目录创建者可以修改权限"}`

---

### 1.5 批量移动

```
POST /api/cases/directories/batch-move
```

**请求体参数**：

| 参数 | 类型 | 必填 | 约束 |
|------|:--:|:--:|------|
| `items` | array | ✅ | 非空数组；每项 `{type:"case"|"directory", id:string|int}` |
| `target_directory_id` | int | ✅ | 目标目录ID |

```json
{
  "items": [{"type": "case", "id": "TC-xxx"}, {"type": "directory", "id": 2}],
  "target_directory_id": 1
}
```

**响应** `200`：`{"ok": true, "moved": 2}`

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| `items` 为空数组 | `400` | `{"ok": false, "error": "items 必须是非空数组"}` |
| `target_directory_id` 缺失 | `400` | `{"ok": false, "error": "target_directory_id 是必填项"}` |
| `items` 中 id 不存在 | `500` | `{"ok": false, "error": "服务器内部错误"}` |
| 目标目录不存在 | `500` | 同上（外键约束失败） |

---

## 2. 用例管理

### 2.1 列出用例

```
GET /api/cases/definitions?directory_id=1
```

| 查询参数 | 类型 | 必填 | 说明 |
|------|:--:|:--:|------|
| `directory_id` | int | — | 筛选目录（含子目录）；不传=全部 |

**响应字段说明**：

| 字段 | 类型 | 来源 | 说明 |
|------|:--:|------|------|
| `id` | string ≤200 | 手动/自动 | PK，格式 `TC-YYYYMMDD-HHMMSS-NNNN` |
| `title` | string ≤500 | 手动 | 同目录唯一 |
| `category` | string ≤200 | 手动 | 分类标签 |
| `description` | text | 手动 | |
| `steps` | text | **自动** | 从 steps_data 自动生成摘要 |
| `steps_data` | array | 手动 | 步骤 JSON，最少 1 项 |
| `enabled` | bool | 手动 | 默认 true；false=停用 |
| `package_name` | string ≤200 | 手动 | App 包名 |
| `directory_id` | int|null | 手动 | |
| `directory_name` | string | **自动** | 从关联表读取 |
| `priority` | string ≤4 | 手动 | P0/P1/P2，默认 P1 |
| `design_method` | string ≤100 | 手动 | |
| `precondition` | text | 手动 | |
| `expected_result` | text | 手动 | |
| `metrics` | text | 手动 | |
| `created_at` | datetime | **自动** | `YYYY-MM-DD HH:MM:SS` |
| `updated_at` | datetime | **自动** | 每次保存更新 |
| `created_by` | string ≤200 | **自动** | JWT 用户名 |
| `updated_by` | string ≤200 | **自动** | JWT 用户名 |
| `editing_by` | string ≤200 | **自动** | 空=无人编辑 |
| `editing_since` | datetime|null | **自动** | 锁获取时间 |
| `locked` | bool | 手动 | 默认 false；仅创建者可改 |
| `visibility` | string ≤20 | 手动 | public(默认)/hidden/restricted |
| `permitted_users` | [string] | 手动 | JSON 数组，restricted 时生效 |
| `permission` | string ≤20 | 手动 | edit(默认)/readonly/restricted |
| `permitted_editors` | [string] | 手动 | JSON 数组，restricted 时生效 |

---

### 2.2 创建/更新用例

```
POST /api/cases/definitions
```

**请求体参数**：

| 参数 | 类型 | 必填 | 长度/值 | 默认值 | 约束 |
|------|:--:|:--:|------|------|------|
| `id` | string | — | ≤200 | 自动生成 | 全局唯一；更新时必传 |
| `title` | string | ✅ | 1-500 | — | 同目录唯一 |
| `category` | string | — | ≤200 | `""` | |
| `package_name` | string | — | ≤200 | `""` | App 包名 |
| `description` | text | — | — | `""` | |
| `enabled` | bool | — | — | true | |
| `steps_data` | array | — | ≥1 项 | `[]` | 每项含 type+参数 |
| `directory_id` | int|null | — | — | null | |
| `priority` | string | — | P0/P1/P2 | `"P1"` | |
| `design_method` | string | — | ≤100 | `""` | |
| `precondition` | text | — | — | `""` | |
| `expected_result` | text | — | — | `""` | |
| `metrics` | text | — | — | `""` | |
| `updated_at` | string | — | — | — | 乐观锁：更新时传入，不匹配→409 |
| `visibility` | string | — | public/hidden/restricted | `"public"` | 仅创建者可改 |
| `permitted_users` | [string] | — | JSON数组 | `[]` | restricted 时生效 |
| `permission` | string | — | edit/readonly/restricted | `"edit"` | 仅创建者可改 |
| `permitted_editors` | [string] | — | JSON数组 | `[]` | restricted 时生效 |

**自动设置**（创建者无需传入）：
- `created_by` ← JWT 用户名
- `updated_by` ← JWT 用户名

**新建请求体**：
```json
{
  "title": "登录成功验证",
  "package_name": "com.example.app",
  "steps_data": [{"type": "click", "xpath": "//Button[@text='登录']"}],
  "directory_id": 1
}
```

**更新请求体（带乐观锁）**：
```json
{
  "id": "TC-20260717-143022-1234",
  "title": "登录成功验证(已修改)",
  "package_name": "com.example.app",
  "steps_data": [],
  "updated_at": "2026-07-17 14:30:22"
}
```

**响应** `200`：`{"ok": true, "id": "TC-20260717-143022-1234"}`

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| `title` 为空 | `400` | `{"ok": false, "error": "invalid JSON"}` 或前端拦截 |
| `id` 已存在（重复创建） | `409` | `{"ok": false, "error": "目录「登录模块」下已存在同名用例「xxx」（ID: TC-xxx）"}` |
| `updated_at` 不匹配 | `409` | `{"ok": false, "error": "用例「xxx」已被他人修改，请刷新后重试"}` |
| `steps_data` 缺 `type` 字段 | `200` | 保存成功但步骤不完整（后端不校验步骤结构） |
| `directory_id` 指向不存在的目录 | `200` | 静默设为 null |
| `design_method` 超过 100 字符 | `500` | `{"ok": false, "error": "服务器内部错误"}` |
| JSON 格式非法 | `400` | `{"ok": false, "error": "无效的 JSON"}` |


---

### 2.3 获取用例详情

```
GET /api/cases/definitions/{case_id}
```

| URL 参数 | 类型 | 必填 | 说明 |
|------|:--:|:--:|------|
| `case_id` | string | ✅ | 用例 ID（路径参数） |

**响应** `200`：`{"ok": true, "definition": {...}}`（字段同 2.1）

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| `case_id` 不存在 | `404` | `{"ok": false, "error": "not found"}` |
| 用例 visibility=hidden + 非创建者 | `404` | `{"ok": false, "error": "not found"}`（隐藏用例不可见） |
| 用例 visibility=restricted + 不在 permitted_users | `404` | `{"ok": false, "error": "not found"}`（同上） |

---

### 2.4 删除用例

```
DELETE /api/cases/definitions/{case_id}
```

无请求体。

**响应** `200`：`{"ok": true}`

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| `case_id` 不存在 | `404` | `{"ok": false, "error": "not found"}` |

---

### 2.5 批量导入用例

```
POST /api/cases/definitions/batch
```

**请求体参数**：

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|:--:|:--:|------|------|
| `cases` | array | ✅ | — | 非空，≤500 项 |
| `overwrite` | bool | — | false | 是否覆盖已存在的 ID |
| `directory_id` | int|null | — | null | 目标目录 |
| `package_name` | string | — | `""` | 默认包名 |

```json
{
  "cases": [
    {"id": "TC-001", "title": "用例1", "steps_data": [], "enabled": true}
  ],
  "overwrite": false,
  "directory_id": 1
}
```

**响应** `200`：
```json
{"ok": true, "imported": ["TC-001"], "skipped": [], "failed": []}
```

**错误** `400`：`{"ok": false, "error": "单次批量导入最多 500 条用例"}`

---

## 3. 编辑锁 🆕

### 3.1 获取编辑锁

```
POST /api/cases/definitions/{case_id}/lock
```

**权限检查**：登录即可；permission=readonly 拒非创建者；permission=restricted 仅允许 permitted_editors

无请求体。

**响应** `200`：
```json
{
  "ok": true,
  "editing_by": "admin",
  "editing_since": "2026-07-17T15:30:00",
  "created_by": "admin"
}
```

**错误** `423`（已被他人锁定）：
```json
{"ok": false, "error": "用例正被 tester 编辑中", "editing_by": "tester", "editing_since": "2026-07-17 15:28:00"}
```

**错误** `423`（只读模式）：
```json
{"ok": false, "error": "此用例为只读模式，仅创建者可编辑"}
```

**错误** `423`（指定用户）：
```json
{"ok": false, "error": "此用例仅限指定用户编辑"}
```

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| 未登录 | `401` | `{"ok": false, "error": "未登录"}` |
| 用例不存在 | `404` | `{"ok": false, "error": "用例不存在"}` |
| 已被他人锁定（30min内） | `423` | `{"ok": false, "error": "用例正被 tester 编辑中", "editing_by": "tester", ...}` |
| permission=readonly + 非创建者 | `423` | `{"ok": false, "error": "此用例为只读模式，仅创建者可编辑"}` |
| permission=restricted + 不在 permitted_editors | `423` | `{"ok": false, "error": "此用例仅限指定用户编辑"}` |
| 锁超时（30min）→ 自动释放，重新获取成功 | `200` | `{"ok": true, ...}` |

---

### 3.2 释放编辑锁

```
POST /api/cases/definitions/{case_id}/unlock
```

**权限**：锁持有者、或创建者

**请求体参数**：

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|:--:|:--:|------|------|
| `force` | bool | — | false | 仅创建者可 force=true |

**普通释放**：`{}`

**强制释放（创建者）**：`{"force": true}`

**响应** `200`：`{"ok": true, "released": true}` 或 `{"ok": true, "already_unlocked": true}`

**错误** `403`：
```json
{"ok": false, "error": "只有用例创建者可以强制解除编辑锁"}
```

---

## 4. 持久锁 🆕

### 4.1 锁定用例

```
POST /api/cases/definitions/{case_id}/case-lock
```

**权限**：仅创建者。无请求体。

**响应** `200`：`{"ok": true, "locked": true}`

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| 未登录 | `401` | `{"ok": false, "error": "未登录"}` |
| 用例不存在 | `404` | `{"ok": false, "error": "用例不存在"}` |
| 非创建者 | `403` | `{"ok": false, "error": "只有创建者可以锁定用例"}` |
| 已锁定再锁 | `200` | 正常返回（幂等） |

---

### 4.2 解除锁定

```
POST /api/cases/definitions/{case_id}/case-unlock
```

**权限**：仅创建者。无请求体。

**响应** `200`：`{"ok": true, "unlocked": true}` 或 `{"ok": true, "already_unlocked": true}`

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| 未登录 | `401` | `{"ok": false, "error": "未登录"}` |
| 用例不存在 | `404` | `{"ok": false, "error": "用例不存在"}` |
| 非创建者 | `403` | `{"ok": false, "error": "只有创建者可以解除锁定"}` |
| 未锁定时解除 | `200` | `{"ok": true, "already_unlocked": true}`（幂等） |

---

## 5. 可见性控制 🆕

### 5.1 设置可见性

```
POST /api/cases/definitions/{case_id}/visibility
```

**权限**：仅创建者。

**请求体参数**：

| 参数 | 类型 | 必填 | 值 | 说明 |
|------|:--:|:--:|------|------|
| `visibility` | string | ✅ | public / hidden / restricted | |
| `permitted_users` | [string] | — | JSON 数组 | restricted 时指定可见用户 |

**请求体**：
```json
// 所有人可见
{"visibility": "public"}

// 仅创建者
{"visibility": "hidden"}

// 指定用户可见（tester 和 dev1）
{"visibility": "restricted", "permitted_users": ["tester", "dev1"]}
```

**响应** `200`：`{"ok": true, "visibility": "restricted"}`

**错误** `403`：`{"ok": false, "error": "只有创建者可以修改可见性"}`

---

## 6. 导入导出

### 6.1 导出 YAML

```
POST /api/cases/export/yaml
```

**请求体参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|:--:|:--:|------|------|
| `test_case_name` | string | — | `"auto_test"` | 导出文件名 |
| `page_ids` | [int] | — | — | 筛选页面；不传=全部 |

```json
{"test_case_name": "回归测试套件", "page_ids": [1, 2]}
```

**响应** `200`：`{"ok": true, "filename": "回归测试套件_20260717_153000.yaml", "yaml": "..."}`

**所有错误场景**：

| 传值错误 | HTTP | 响应体 |
|------|:--:|------|
| JSON 格式非法 | `400` | `{"ok": false, "error": "无效的 JSON"}` |
| 无测试点元素 | `200` | 导出文件为空（仅含框架） |
| 文件写入失败 | `500` | `{"ok": false, "error": "服务器内部错误"}` |

### 6.2 导出文件列表

```
GET /api/cases/exports
```

无参数。

**响应** `200`：
```json
{"ok": true, "files": [{"name": "test_20260717.yaml", "size": 2048, "time": "2026-07-17T15:30:00"}]}
```

### 6.3 下载导出文件

```
GET /api/cases/exports/{filename}
```

| URL 参数 | 类型 | 必填 | 说明 |
|------|:--:|:--:|------|
| `filename` | string | ✅ | 文件名（含 `.yaml` 后缀） |

**响应** `200`：直接返回 YAML 文件流（`Content-Type: application/x-yaml`）

**错误** `404`：`{"ok": false, "error": "not found"}`

---

## 汇总

| # | 方法 | 路径 | 新增 | 权限 |
|:--:|:--:|------|:--:|------|
| 1 | GET | `/directories` | | 登录 |
| 2 | POST | `/directories/create` | | 登录 |
| 3 | POST | `/directories/{id}` | | 目录创建者可删除 |
| 4 | POST | `/directories/{id}/permission` | 🆕 | 仅目录创建者 |
| 5 | POST | `/directories/batch-move` | | 登录 |
| 6 | GET | `/definitions` | | 登录（可见性过滤） |
| 7 | POST | `/definitions` | | 登录 |
| 8 | GET | `/definitions/{id}` | | 登录（可见性过滤） |
| 9 | DELETE | `/definitions/{id}` | | 登录 |
| 10 | POST | `/definitions/batch` | | 登录 |
| 11 | POST | `/definitions/{id}/lock` | 🆕 | 登录 + permission 检查 |
| 12 | POST | `/definitions/{id}/unlock` | 🆕 | 锁持有者/创建者 |
| 13 | POST | `/definitions/{id}/case-lock` | 🆕 | 仅创建者 |
| 14 | POST | `/definitions/{id}/case-unlock` | 🆕 | 仅创建者 |
| 15 | POST | `/definitions/{id}/visibility` | 🆕 | 仅创建者 |
| 16 | POST | `/export/yaml` | | 登录 |
| 17 | GET | `/exports` | | 登录 |
| 18 | GET | `/exports/{filename}` | | 无鉴权 |
