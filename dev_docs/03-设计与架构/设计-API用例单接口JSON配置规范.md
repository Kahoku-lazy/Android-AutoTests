# API 测试用例 JSON 配置规范 — 单接口数据驱动格式

## 概述

API 测试用例支持两种 `config_json` 格式：

| 格式 | 顶层 key | 适用场景 |
|------|----------|----------|
| **单接口** | `meta` / `request` / `cases` | 一个接口 + N 组测试数据，如登录、注册等 |
| **多接口** | `case_info` / `steps` / `test_data` / `validation` | 多步骤链式调用，如创建订单→支付→查询 |

前端和后端通过探测顶层 key 自动识别格式：有 `meta` 键 → 单接口格式。

---

## 单接口格式全字段定义

### 顶层结构

```json
{
  "meta": { ... },      // 用例元信息
  "request": { ... },   // 请求模板
  "cases": [ ... ]      // 测试用例列表（数据驱动）
}
```

---

### 1. `meta` — 用例元信息

| 字段 | 类型 | 必填 | 描述 |
|------|------|:--:|------|
| `title` | string | ✅ | 测试用例标题，如 `"登录接口测试"`。同步写入 DB 的 `title` 字段 |
| `description` | string | ❌ | 测试场景描述，概括全部测试点的覆盖范围 |
| `base_url` | string | ✅ | 接口的基础 URL，如 `"http://localhost:8765"`。执行时会与 `request.path` 拼接 |
| `auth` | object | ❌ | 全局鉴权配置，可被单条 case 的 `input.auth` 覆盖 |

#### `auth` 对象

| 字段 | 类型 | 必填 | 描述 |
|------|------|:--:|------|
| `type` | string | ✅ | 鉴权类型：`"none"` / `"bearer"` / `"basic"` / `"api_key"` |
| `token` | string | 条件 | `type=bearer` 时必填，JWT token |
| `username` | string | 条件 | `type=basic` 时必填 |
| `password` | string | 条件 | `type=basic` 时必填 |
| `key` | string | 条件 | `type=api_key` 时必填，header 键名 |
| `value` | string | 条件 | `type=api_key` 时必填，header 值 |

#### 示例

```json
{
  "meta": {
    "title": "登录接口测试",
    "description": "认证登录接口全场景覆盖：功能/校验/认证/安全 4 类共 20 个测试点",
    "base_url": "http://localhost:8765",
    "auth": { "type": "none" }
  }
}
```

---

### 2. `request` — 请求模板

所有 `cases` 中的每条用例都会基于此模板构造 HTTP 请求。单条 case 的 `input` 可以覆盖模板中的部分字段。

| 字段 | 类型 | 必填 | 描述 |
|------|------|:--:|------|
| `method` | string | ✅ | HTTP 方法：`GET` / `POST` / `PUT` / `DELETE` / `PATCH` / `HEAD` / `OPTIONS` |
| `path` | string | ✅ | 接口路径，如 `"/api/ai/auth/login"`。执行时拼接到 `base_url` 后 |
| `headers` | object | ❌ | 请求头键值对，如 `{"Content-Type": "application/json"}` |

#### 示例

```json
{
  "request": {
    "method": "POST",
    "path": "/api/ai/auth/login",
    "headers": { "Content-Type": "application/json" }
  }
}
```

---

### 3. `cases` — 测试用例列表（数据驱动）

每条 case 是一次独立的 HTTP 请求和断言验证。`cases[].input` 会与 `request` 模板合并（`input` 优先），然后发出请求；`cases[].expect` 定义了对响应的断言。

#### `case` 对象全字段

| 字段 | 类型 | 必填 | 描述 |
|------|------|:--:|------|
| `id` | string | ✅ | 用例唯一 ID，如 `"TC-LOGIN-001"` |
| `category` | string | ✅ | 分类标签，如 `"功能"` / `"校验"` / `"认证"` / `"安全"` |
| `scenario` | string | ✅ | 场景描述，如 `"正常登录"` / `"SQL注入 — username"` |
| `description` | string | ❌ | 场景详细说明 |
| `input` | object | ✅ | 本次请求的输入（headers / body / auth） |
| `expect` | object | ✅ | 期望的响应断言 |

---

#### 3.1 `input` — 请求输入

所有字段均为可选，有值时覆盖 `request` 模板的对应字段。

| 字段 | 类型 | 描述 |
|------|------|------|
| `headers` | object | 追加/覆盖的请求头 |
| `body` | object | 请求体，如 `{"username":"admin", "password":"admin123"}` |
| `auth` | object | 本条的鉴权配置，覆盖 `meta.auth`（结构同上） |

#### 示例

```json
{
  "input": {
    "body": {
      "username": "admin",
      "password": "admin123"
    }
  }
}
```

---

#### 3.2 `expect` — 期望响应断言

执行器在收到 HTTP 响应后，依次执行以下断言：

1. **状态码断言**：检查 `response.status_code == expect.status`
2. **响应头 Schema 断言**：用 `headers_schema` 校验响应头（可选）
3. **响应体 Schema 断言**：用 `body_schema` 校验 JSON 响应体（可选，最常用）

| 字段 | 类型 | 必填 | 描述 |
|------|------|:--:|------|
| `status` | integer | ✅ | 期望的 HTTP 状态码，如 `200` / `400` / `401` |
| `headers_schema` | object | ❌ | JSON Schema 校验响应头（目前可填 `null`） |
| `body_schema` | object | ❌ | JSON Schema 校验响应体，**核心校验字段** |

#### `body_schema` 详解

完全符合 [JSON Schema Draft-7](https://json-schema.org/draft-07/json-schema-release-notes.html) 规范。最常用的关键字：

| 关键字 | 类型 | 描述 |
|--------|------|------|
| `type` | string | 期望数据类型，通常为 `"object"` |
| `required` | array[string] | **必须出现**的字段名列表 |
| `properties` | object | 字段级别校验规则 |
| `properties.<name>.type` | string | 字段类型：`"string"` / `"integer"` / `"boolean"` / `"object"` / `"array"` |
| `properties.<name>.const` | any | **精确相等**校验，值必须完全匹配。如期望返回 `status: true` 可写 `{"const": true}` |
| `properties.<name>.enum` | array | 枚举校验，值必须是列表中的一项 |

#### 成功登录示例（期望 `access_token`）

```json
{
  "expect": {
    "status": 200,
    "body_schema": {
      "type": "object",
      "required": ["status", "access_token", "refresh_token", "user"],
      "properties": {
        "status": { "const": true },
        "access_token": { "type": "string" },
        "refresh_token": { "type": "string" },
        "user": { "type": "object" }
      }
    }
  }
}
```

#### 校验失败示例（期望特定报错消息）

```json
{
  "expect": {
    "status": 400,
    "body_schema": {
      "type": "object",
      "required": ["status", "message"],
      "properties": {
        "status": { "const": false },
        "message": { "const": "请输入用户名和密码" }
      }
    }
  }
}
```

#### 无 schema（不对响应体做结构校验）

```json
{
  "expect": {
    "status": 200,
    "body_schema": null
  }
}
```

> **提示**：即使 `body_schema` 为 `null`，执行器仍会检查 HTTP 状态码是否等于 `expect.status`。

---

### 完整示例

下面是一个完整的单接口登录用例配置（精简为 4 条）：

```json
{
  "meta": {
    "title": "登录接口测试",
    "description": "认证登录全场景覆盖",
    "base_url": "http://localhost:8765",
    "auth": { "type": "none" }
  },
  "request": {
    "method": "POST",
    "path": "/api/ai/auth/login",
    "headers": { "Content-Type": "application/json" }
  },
  "cases": [
    {
      "id": "TC-LOGIN-001",
      "category": "功能",
      "scenario": "正常登录",
      "description": "提供正确的用户名和密码，期望登录成功获取 token",
      "input": {
        "body": {
          "username": "admin",
          "password": "admin123"
        }
      },
      "expect": {
        "status": 200,
        "body_schema": {
          "type": "object",
          "required": ["status", "access_token", "refresh_token", "user"],
          "properties": {
            "status": { "const": true },
            "access_token": { "type": "string" },
            "refresh_token": { "type": "string" },
            "user": { "type": "object" }
          }
        }
      }
    },
    {
      "id": "TC-LOGIN-004",
      "category": "校验",
      "scenario": "用户名为空",
      "description": "用户名留空但提供密码，期望提示请输入用户名",
      "input": {
        "body": {
          "username": "",
          "password": "admin123"
        }
      },
      "expect": {
        "status": 400,
        "body_schema": {
          "type": "object",
          "required": ["status", "message"],
          "properties": {
            "status": { "const": false },
            "message": { "const": "请输入用户名" }
          }
        }
      }
    },
    {
      "id": "TC-LOGIN-013",
      "category": "认证",
      "scenario": "密码错误",
      "description": "用户名正确但密码错误，期望提示凭证错误",
      "input": {
        "body": {
          "username": "admin",
          "password": "wrong"
        }
      },
      "expect": {
        "status": 401,
        "body_schema": {
          "type": "object",
          "required": ["status", "message"],
          "properties": {
            "status": { "const": false },
            "message": { "const": "用户名或密码错误" }
          }
        }
      }
    },
    {
      "id": "TC-LOGIN-016",
      "category": "安全",
      "scenario": "SQL注入 — username",
      "description": "用户名注入 SQL 片段，验证后端参数化查询防护",
      "input": {
        "body": {
          "username": "admin' OR '1'='1",
          "password": "admin123"
        }
      },
      "expect": {
        "status": 401,
        "body_schema": {
          "type": "object",
          "required": ["status", "message"],
          "properties": {
            "status": { "const": false },
            "message": { "const": "用户名或密码错误" }
          }
        }
      }
    }
  ]
}
```

---

## 执行流程

执行器 `apps/test_runner/executors/api/executor_v2.py` 在识别到 `config_json` 中有 `meta` 键后，进入 `_execute_single()` 方法：

```
1. 对于每一条 case：
   a. 合并 request 模板 + case.input 的 headers/body/auth
   b. 解析鉴权（token → Authorization 头等）
   c. 构造 HTTP 请求：{base_url}{path} + method + headers + body
   d. 发出请求，记录 elapsed 和 response
   e. 状态码断言：response.status_code == expect.status
   f. 若 body_schema 不为 null：jsonschema.validate(response.json(), body_schema)
   g. 若 headers_schema 不为 null：jsonschema.validate(response.headers, headers_schema)
2. 汇总所有 case 的结果，生成测试报告
```

---

## 如何通过 API 创建用例

### 方式一：通过 AI 助手（AgentScope Tool）

调用 `save_api_test_case` 工具，传入 case_id 和完整 config_json：

```
Tool: save_api_test_case
参数:
  - case_id: "API-20260811-120000-ABCD"
  - config_json: { ... }  (上面定义的完整 JSON)
```

后端自动探测格式（`meta` → 单接口，`case_info` → 多接口），执行对应的 JSON Schema 校验后写入 `cm_api_testcases` 表。

### 方式二：通过 REST API

`POST /api/cases/api-testing/definitions`

```json
{
  "id": "API-YYYYMMDD-HHMMSS-XXXX",
  "config_json": { ... },
  "title": "登录接口测试",
  "directory_id": 118
}
```

---

## 字段对照速查

| 层级 | 字段 | 类型 | 必填 | 示例值 |
|------|------|------|:--:|--------|
| meta | title | string | ✅ | `"登录接口测试"` |
| meta | description | string | ❌ | `"全场景覆盖"` |
| meta | base_url | string | ✅ | `"http://localhost:8765"` |
| meta.auth | type | string | ❌ | `"bearer"` |
| request | method | string | ✅ | `"POST"` |
| request | path | string | ✅ | `"/api/ai/auth/login"` |
| request | headers | object | ❌ | `{"Content-Type":"application/json"}` |
| cases[n] | id | string | ✅ | `"TC-LOGIN-001"` |
| cases[n] | category | string | ✅ | `"功能"` |
| cases[n] | scenario | string | ✅ | `"正常登录"` |
| cases[n] | description | string | ❌ | `"验证正常登录流程"` |
| cases[n].input | headers | object | ❌ | 追加请求头 |
| cases[n].input | body | object | ❌ | `{"username":"admin"}` |
| cases[n].input | auth | object | ❌ | 单条鉴权覆盖 |
| cases[n].expect | status | integer | ✅ | `200` |
| cases[n].expect | body_schema | object | ❌ | JSON Schema 或 null |
| cases[n].expect | headers_schema | object | ❌ | JSON Schema 或 null |

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `apps/case_manager/schema_config.py` | 后端 JSON Schema 定义（`SINGLE_API_SCHEMA`） |
| `apps/test_runner/executors/api/executor_v2.py` | 执行器（`_execute_single` 方法） |
| `frontend/src/modules/case-manager/types/api-config.ts` | 前端 TypeScript 类型定义 |
| `frontend/src/modules/case-manager/composables/useApiConfigJson.ts` | 前端状态管理 |
| `frontend/src/modules/case-manager/components/api/ApiCaseEditor.vue` | 前端编辑器组件 |
| `frontend/src/modules/case-manager/components/api/ApiCaseList.vue` | 前端列表组件 |
