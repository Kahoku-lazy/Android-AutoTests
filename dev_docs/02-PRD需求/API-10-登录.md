# API-10 — 登录接口文档

> 模块：`apps/ai_assistant/views/auth_views.py` · 端点：5 个 · 基础路径：`/api/ai/auth`
> 版本：v1.0 · 日期：2026-08-06

---

## 通用约定

### 请求头

| Header | 值 | 必填 | 说明 |
|------|------|:--:|------|
| `Content-Type` | `application/json` | ✅ | login / register / refresh / logout |
| `Authorization` | `Bearer <JWT>` | — | 仅 `/me` 和 `/logout` 需要 |

### 认证方式

平台使用 **JWT Bearer Token** 鉴权。登录/注册成功后返回 `access_token`（短期）和 `refresh_token`（长期）。除 `/api/ai/auth/*`、`/admin/`、`/static/` 外，所有 API 请求必须携带 `Authorization: Bearer <access_token>`。

### 响应格式

```json
// 成功
{"status": true, ...}

// 失败
{"status": false, "message": "人类可读的中文描述"}
```

### 错误码速查

| HTTP 状态码 | 含义 | 触发场景 |
|:--:|------|------|
| `400` | 请求参数错误 | 缺少必填字段、JSON 格式非法、值不合法 |
| `401` | 认证失败 | 用户名或密码错误、Token 过期/无效 |
| `404` | 用户不存在 | `/me` 查不到对应用户 |
| `409` | 冲突 | 注册时用户名已存在 |
| `503` | 服务不可用 | 登出时 Redis 不可用，Token 无法加入黑名单 |

---

## 端点

### 1. 登录 — `POST /api/ai/auth/login`

验证用户名密码，返回 JWT Token 对。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `username` | string | ✅ | 用户名 |
| `password` | string | ✅ | 密码 |

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**成功响应 `200`：**

```json
{
  "status": true,
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| 用户名为空且密码为空 | `400` | `{"status": false, "message": "请输入用户名和密码"}` |
| 用户名为空 | `400` | `{"status": false, "message": "请输入用户名"}` |
| 密码为空 | `400` | `{"status": false, "message": "请输入密码"}` |
| 用户名为纯空白 | `400` | `{"status": false, "message": "用户名不能为空白"}` |
| 用户名超过 150 字符 | `400` | `{"status": false, "message": "用户名过长，最多150个字符"}` |
| 用户名或密码错误 | `401` | `{"status": false, "message": "用户名或密码错误"}` |
| JSON 格式非法 | `400` | `{"status": false, "message": "请求格式错误"}` |

> **安全设计**：认证失败统一返回 `"用户名或密码错误"`，不区分"用户不存在"和"密码错误"，防止用户名枚举攻击。

---

### 2. 注册 — `POST /api/ai/auth/register`

创建新用户并直接返回 JWT Token 对（注册即登录）。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `username` | string | ✅ | 用户名，3–20 字符 |
| `password` | string | ✅ | 密码，至少 6 位 |
| `password2` | string | ✅ | 确认密码，必须与 `password` 一致 |
| `email` | string | ✅ | 邮箱地址 |

```json
{
  "username": "newuser",
  "password": "pass123",
  "password2": "pass123",
  "email": "newuser@example.com"
}
```

**成功响应 `200`：**

```json
{
  "status": true,
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 3,
    "username": "newuser",
    "email": "newuser@example.com"
  }
}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| 用户名为空且密码为空 | `400` | `{"status": false, "message": "请输入用户名和密码"}` |
| 用户名为空 | `400` | `{"status": false, "message": "请输入用户名"}` |
| 密码为空 | `400` | `{"status": false, "message": "请输入密码"}` |
| 用户名少于 3 字符 | `400` | `{"status": false, "message": "用户名至少 3 个字符"}` |
| 用户名超过 20 字符 | `400` | `{"status": false, "message": "用户名最多 20 个字符"}` |
| 两次密码不一致 | `400` | `{"status": false, "message": "两次密码不一致"}` |
| 邮箱为空 | `400` | `{"status": false, "message": "请输入邮箱"}` |
| 邮箱格式不正确 | `400` | `{"status": false, "message": "邮箱格式不正确"}` |
| 用户名已存在 | `409` | `{"status": false, "message": "用户名已存在"}` |
| JSON 格式非法 | `400` | `{"status": false, "message": "请求格式错误"}` |

---

### 3. 刷新 Token — `POST /api/ai/auth/refresh`

用 `refresh_token` 换取新的 `access_token`。适用于 `access_token` 过期时续期。

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `refresh_token` | string | ✅ | 登录/注册时获得的 refresh token |

```json
{
  "refresh_token": "eyJhbGciOi..."
}
```

**成功响应 `200`：**

```json
{
  "status": true,
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| Token 过期或无效 | `401` | `{"status": false, "message": "Token has expired"}` 或具体错误描述 |
| Token 类型不是 refresh | `401` | `{"status": false, "message": "Not a refresh token"}` |

---

### 4. 登出 — `POST /api/ai/auth/logout`

将当前 `access_token` 加入 Redis 黑名单，使其立即失效。

**请求头：**

| Header | 值 | 必填 |
|------|------|:--:|
| `Authorization` | `Bearer <access_token>` | ✅ |

**成功响应 `200`：**

```json
{"status": true}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| Redis 不可用（无法持久化黑名单） | `503` | `{"status": false, "message": "Redis 不可用，无法撤销令牌", "retry": true}` |

> **设计说明**：Token 黑名单存储在 Redis 中，服务重启不丢失。Redis 不可用时登出返回 503 并标记 `retry: true`，前端应提示用户稍后重试。

---

### 5. 当前用户 — `GET /api/ai/auth/me`

从 JWT 解析 `user_id`，返回当前登录用户信息。用于前端页面刷新后恢复登录态。

**请求头：**

| Header | 值 | 必填 |
|------|------|:--:|
| `Authorization` | `Bearer <access_token>` | ✅ |

**成功响应 `200`：**

```json
{
  "status": true,
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| 未认证（无 Token） | `401` | `{"status": false, "message": "Not authenticated"}` |
| Token 中 user_id 对应的用户不存在 | `404` | `{"status": false, "message": "User not found"}` |

---

## Token 生命周期

```
注册/登录 → 获得 access_token + refresh_token
                │                    │
                │ (短期, 1h)         │ (长期, 7d)
                ▼                    ▼
          每次请求携带            access_token 过期时
          Authorization          POST /auth/refresh
                │                    │
                ▼                    ▼
          POST /auth/logout     获得新 access_token
          Token 加入黑名单
          立即失效
```

## 前端调用

```typescript
// frontend/src/shared/api/auth.ts
import djangoClient from '@/shared/api-client'

// 登录
const { data } = await djangoClient.post('/ai/auth/login', { username, password })
// → { ok, access_token, refresh_token, user }

// 注册
const { data } = await djangoClient.post('/ai/auth/register', { username, password })
// → { ok, access_token, refresh_token, user }
```

## 相关文件

| 层 | 文件 | 说明 |
|------|------|------|
| 视图 | `apps/ai_assistant/views/auth_views.py` | 5 个端点实现 |
| 路由 | `apps/ai_assistant/urls.py` | `auth/login` 等路由注册 |
| JWT | `shared/auth/jwt_auth.py` | Token 生成/验证/黑名单 |
| 中间件 | `gateway/middleware.py` | JWT 自动解析 + `request.user_id` 注入 |
| 前端 API | `frontend/src/shared/api/auth.ts` | `login()` / `register()` |
| 前端类型 | `frontend/src/shared/types/auth.ts` | `AuthResponse` 等类型定义 |
