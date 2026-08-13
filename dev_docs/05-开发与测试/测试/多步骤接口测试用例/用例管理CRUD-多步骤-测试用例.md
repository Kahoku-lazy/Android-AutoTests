# 用例管理 CRUD 全流程 — 多步骤链式 API 测试用例

> 格式：`case_info/steps/test_data/validation`（多接口多步骤）
> 端点文档：`dev_docs/02-PRD需求/API-00-认证.md` + `API-03-用例管理.md`
> 执行器：`apps/test_runner/executors/api/executor_v2.py` → `_execute_row()`

---

## 用例信息

| 字段 | 值 |
|------|-----|
| ID | `API-CRUD-FLOW-001` |
| 标题 | 用例管理 CRUD — 登录→建目录→建用例→查详情→删用例→删目录 |
| 描述 | 验证完整用例管理 CRUD 生命周期：登录获取 token → 创建目录 → 在目录下创建 API 测试用例 → 查询用例详情验证字段 → 清理删除用例 → 清理删除目录 |
| 前置条件 | 1. 平台 API 已启动 (localhost:8765)\n2. admin/admin123 用户已存在 |

---

## 步骤定义 (6 步)

```
Step 1: POST /api/ai/auth/login           → 登录获取 access_token
  │ extract: $.access_token → {{token}}
  ▼
Step 2: POST /api/cases/directories/create → 创建测试目录
  │ Authorization: Bearer {{token}}
  │ extract: $.directory.id → {{dir_id}}
  ▼
Step 3: POST /api/cases/api-testing/definitions → 创建 API 用例（属于该目录）
  │ Authorization: Bearer {{token}}
  │ body 含 directory_id: {{dir_id}} 和嵌套的 config_json
  │ extract: $.id → {{case_id}}
  ▼
Step 4: GET /api/cases/api-testing/definitions/{{case_id}} → 查询用例详情
  │ Authorization: Bearer {{token}}
  │ assert: definition 完整返回
  ▼
Step 5: DELETE /api/cases/api-testing/definitions/{{case_id}} → 删除用例（清理）
  │ Authorization: Bearer {{token}}
  ▼
Step 6: POST /api/cases/directories/{{dir_id}} → 删除目录（清理）
  │ Authorization: Bearer {{token}}
  │ body: { "action": "delete" }
```

---

## 变量流转表

| 变量名 | 来源 | 提取路径 | 消费步骤 |
|--------|------|----------|----------|
| `{{token}}` | Step 1 响应 | `$.access_token` | Step 2, 3, 4, 5, 6 (header) |
| `{{dir_id}}` | Step 2 响应 | `$.directory.id` | Step 3 (body), Step 6 (url) |
| `{{case_id}}` | Step 3 响应 | `$.id` | Step 4, 5 (url) |

---

## 测试数据 (1 行)

| # | `{{username}}` | `{{password}}` |
|:--:|----------------|----------------|
| 1 | `admin` | `admin123` |

> 只有 1 行 — 使用已存在的 admin 账号登录，避免创建新用户。如需测试不同用户，可增加行。

---

## 完整 config_json

```json
{
  "case_info": {
    "id": "API-CRUD-FLOW-001",
    "title": "用例管理 CRUD — 登录→建目录→建用例→查详情→删用例→删目录",
    "description": "验证完整用例管理 CRUD 生命周期：登录获取token → 创建目录 → 在目录下创建API测试用例 → 查询用例详情验证 → 删除用例 → 删除目录。变量跨6个步骤传递。",
    "precondition": "1. 平台 API 已启动 (localhost:8765)\n2. admin / admin123 用户已存在\n3. 测试目录名不可与已有目录重名"
  },
  "steps": [
    {
      "name": "1. 登录获取 Token",
      "domain": "http://localhost:8765",
      "url": "/api/ai/auth/login",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "username": "{{username}}",
        "password": "{{password}}"
      },
      "request_schema": null,
      "response_schema": {
        "type": "object",
        "required": ["status", "access_token", "refresh_token", "user"],
        "properties": {
          "status": { "const": true },
          "access_token": { "type": "string" },
          "refresh_token": { "type": "string" },
          "token_type": { "const": "bearer" },
          "user": {
            "type": "object",
            "required": ["id", "username"],
            "properties": {
              "id": { "type": "integer" },
              "username": { "type": "string" }
            }
          }
        }
      },
      "extract": [
        { "name": "token", "path": "$.access_token" }
      ],
      "assert": true
    },
    {
      "name": "2. 创建测试目录",
      "domain": "http://localhost:8765",
      "url": "/api/cases/directories/create",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{token}}"
      },
      "body": {
        "name": "CRUD自动测试目录",
        "parent_id": null,
        "sort_order": 0
      },
      "request_schema": null,
      "response_schema": {
        "type": "object",
        "required": ["status", "directory"],
        "properties": {
          "status": { "const": true },
          "directory": {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
              "id": { "type": "integer" },
              "name": { "type": "string" },
              "parent_id": {}
            }
          }
        }
      },
      "extract": [
        { "name": "dir_id", "path": "$.directory.id" }
      ],
      "assert": true
    },
    {
      "name": "3. 创建 API 测试用例",
      "domain": "http://localhost:8765",
      "url": "/api/cases/api-testing/definitions",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{token}}"
      },
      "body": {
        "id": "API-CRUD-TEMP-{{dir_id}}",
        "config_json": {
          "meta": {
            "title": "CRUD自动创建的临时用例",
            "description": "由多步骤CRUD测试自动创建，验证创建流程后立即删除",
            "base_url": "http://localhost:8765",
            "auth": { "type": "none" }
          },
          "request": {
            "method": "GET",
            "path": "/api/ai/auth/me",
            "headers": {}
          },
          "cases": [
            {
              "id": "TC-CRUD-TEMP-001",
              "category": "功能",
              "scenario": "临时用例 — 验证 CRUD 创建流程",
              "description": "此用例由多步骤测试自动创建，执行后被删除",
              "input": { "body": {} },
              "expect": {
                "status": 200,
                "body_schema": null
              }
            }
          ]
        },
        "directory_id": "{{dir_id}}"
      },
      "request_schema": null,
      "response_schema": {
        "type": "object",
        "required": ["status", "id"],
        "properties": {
          "status": { "const": true },
          "id": { "type": "string" }
        }
      },
      "extract": [
        { "name": "case_id", "path": "$.id" }
      ],
      "assert": true
    },
    {
      "name": "4. 查询用例详情",
      "domain": "http://localhost:8765",
      "url": "/api/cases/api-testing/definitions/{{case_id}}",
      "method": "GET",
      "headers": {
        "Authorization": "Bearer {{token}}"
      },
      "body": {},
      "request_schema": null,
      "response_schema": {
        "type": "object",
        "required": ["status", "definition"],
        "properties": {
          "status": { "const": true },
          "definition": { "type": "object" }
        }
      },
      "extract": [],
      "assert": true
    },
    {
      "name": "5. 删除用例（清理）",
      "domain": "http://localhost:8765",
      "url": "/api/cases/api-testing/definitions/{{case_id}}",
      "method": "DELETE",
      "headers": {
        "Authorization": "Bearer {{token}}"
      },
      "body": {},
      "request_schema": null,
      "response_schema": {
        "type": "object",
        "required": ["status"],
        "properties": {
          "status": { "const": true }
        }
      },
      "extract": [],
      "assert": true
    },
    {
      "name": "6. 删除目录（清理）",
      "domain": "http://localhost:8765",
      "url": "/api/cases/directories/{{dir_id}}",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{token}}"
      },
      "body": {
        "action": "delete"
      },
      "request_schema": null,
      "response_schema": {
        "type": "object",
        "required": ["status"],
        "properties": {
          "status": { "const": true }
        }
      },
      "extract": [],
      "assert": true
    }
  ],
  "test_data": [
    {
      "input": {
        "username": "admin",
        "password": "admin123"
      },
      "output_schema": null
    }
  ],
  "validation": []
}
```

---

## 执行流程

```
ExecutorV2.execute_case()
  ├── 检测 config_json 有 "case_info" + "steps" → 多步骤格式
  ├── test_data 有 1 行 → 单行执行（非数据驱动模式）
  │
  └── Row 1: {username: "admin", password: "admin123"}
      ├── Step 1: POST /login                → 200 ✓ → extract token
      ├── Step 2: POST /directories/create   → 200 ✓ → extract dir_id
      ├── Step 3: POST /api-testing/defs     → 200 ✓ → extract case_id
      ├── Step 4: GET /api-testing/defs/{{}} → 200 ✓
      ├── Step 5: DELETE /api-testing/defs/{{}} → 200 ✓
      └── Step 6: POST /directories/{{dir_id}}  → 200 ✓
      
      6/6 pass → 返回 "pass"
```

---

## 清理策略

Step 5 (删除用例) 和 Step 6 (删除目录) 作为清理步骤：

| 场景 | 行为 |
|------|------|
| 全部成功 | 用例和目录均被删除，不留残留 |
| Step 3 之前失败 | 目录未被删除（目录为空，可手动清理） |
| Step 5 失败 | 用例残留 → 需手动删除后，才能删目录 |
| Step 6 失败 | 目录残留（已空，可手动删除） |

> **建议**：执行后检查 `GET /api/cases/directories` 确认无名为 "CRUD自动测试目录" 的残留目录。

---

## 断言覆盖

| 步骤 | 方法 | 状态码 | body_schema 关键断言 |
|------|:--:|:--:|------|
| 登录 | POST | 200 | `status=true`, `access_token` 为 string, `user` 含 id+username |
| 建目录 | POST | 200 | `status=true`, `directory.id` 为 integer, `directory.name` 为 string |
| 建用例 | POST | 200 | `status=true`, `id` 为 string（返回创建的 case_id） |
| 查详情 | GET | 200 | `status=true`, `definition` 为 object |
| 删用例 | DELETE | 200 | `status=true` |
| 删目录 | POST | 200 | `status=true` |

---

## 注意事项

1. **目录名冲突**：Step 2 创建名为 "CRUD自动测试目录" 的目录。该目录名可能与其他测试用例冲突，如已存在同名目录，Step 2 返回 400 失败。可修改 `body.name` 添加时间戳后缀避免。
2. **case_id 唯一性**：Step 3 创建的用例 ID 为 `API-CRUD-TEMP-{{dir_id}}`，其中 `{{dir_id}}` 是 Step 2 返回的整数。每次执行生成不同的 ID，避免冲突。
3. **`directory_id` 类型**：Step 3 body 中 `directory_id` 使用 `"{{dir_id}}"` 字符串值。后端 Django ORM 在 FK 赋值时会自动将字符串转换为 int。
4. **Token 有效期**：6 步链式调用在几秒内完成，access_token 有效期 1 小时，无需刷新。
5. **目录为空才能删除**：目录下有子目录或用例时，删除操作返回 400。Step 5 先删用例可确保 Step 6 时目录为空。
