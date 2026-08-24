# API-10 — 登录接口文档

> 模块：`apps/accounts/` · 端点：5 个 · 基础路径：`/api/auth`
> 版本：v1.1 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.1 | 2026-08-21 | 以代码为真相源重写：路径 /api/ai/auth → /api/auth（auth 迁移至 apps/accounts）、模块 ai_assistant/views/auth_views.py → apps/accounts/views.py、成功响应改 {status,data} 信封、错误文案对齐代码中文文案、补登记密码≥6位校验与 /me 未消费偏差 |
| v1.0 | 2026-08-06 | 初始版本 |

---

## 通用约定

### 请求头

| Header | 值 | 必填 | 说明 |
|------|------|:--:|------|
| `Content-Type` | `application/json` | ✅ | login / register / refresh / logout |
| `Authorization` | `Bearer <JWT>` | — | 仅 `/me` 和 `/logout` 需要（二者不在公开白名单内） |

### 认证方式

平台使用 **JWT Bearer Token** 鉴权。登录/注册成功后返回 `access_token`（短期，1h）和 `refresh_token`（长期，7d）。

`gateway/middleware.py` 的 `PUBLIC_PREFIXES` 白名单免鉴权：`/api/auth/login`、`/api/auth/register`、`/api/auth/refresh`（另含 `/api/runner/step-screenshots/`、`/api/ai/tools/`、`/admin/`、`/static/`、`/media/`、`/api/docs`、`/api/schema/`、`/api/swagger/`）。`/api/auth/logout` 与 `/api/auth/me` **不在白名单内**，必须携带 `Authorization: Bearer <access_token>`。

> 说明：旧基础路径 `/api/ai/auth/*` 已废弃——`gateway/middleware.py:12-18` 的 `RETIRED_AUTH_PATHS` 标记了旧 5 条路径；auth 已迁至 `apps/accounts`（`config/urls.py:29` 挂载 `api/auth/`）。

### 响应格式

全局 `shared/renderers.py` 的 `EnvelopeJSONRenderer` 统一信封：**2xx** 包裹为 `{status, data}`；**4xx/5xx** 提取 DRF 的 `detail`（或字段级首条错误）转成 `{status, message}`，若响应含 `retry` 则透传 `retry` 布尔。

```json
// 成功（2xx）
{"status": true, "data": {...}}

// 失败（4xx/5xx）
{"status": false, "message": "人类可读的中文描述"}

// 部分失败附带 retry 标记（如登出 Redis 不可用）
{"status": false, "message": "Redis 不可用，无法撤销令牌", "retry": true}
```

### 错误码速查

| HTTP 状态码 | 含义 | 触发场景 |
|:--:|------|------|
| `400` | 请求参数错误 | 缺少必填字段、JSON 格式非法、值不合法 |
| `401` | 认证失败 | 用户名或密码错误、Token 缺失/过期/无效（中间件拦截） |
| `404` | 用户不存在 | `/me` 查不到对应用户 |
| `409` | 冲突 | 注册时用户名已存在 |
| `503` | 服务不可用 | 登出时 Redis 不可用，Token 无法加入黑名单 |

---

## 端点

### 1. 登录 — `POST /api/auth/login`

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
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "admin"
    }
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

### 2. 注册 — `POST /api/auth/register`

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
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 3,
      "username": "newuser",
      "email": "newuser@example.com"
    }
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
| 密码少于 6 位 | `400` | `{"status": false, "message": "密码至少 6 位"}` |
| 两次密码不一致 | `400` | `{"status": false, "message": "两次密码不一致"}` |
| 邮箱为空 | `400` | `{"status": false, "message": "请输入邮箱"}` |
| 邮箱格式不正确 | `400` | `{"status": false, "message": "邮箱格式不正确"}` |
| 用户名已存在 | `409` | `{"status": false, "message": "用户名已存在"}` |
| JSON 格式非法 | `400` | `{"status": false, "message": "请求格式错误"}` |

> 说明：密码≥6 位校验为本次补登记的字段规则（`apps/accounts/serializers.py:62-63`），前端 `useLoginForm.ts` 同步校验同文案「密码至少 6 位」。

---

### 3. 刷新 Token — `POST /api/auth/refresh`

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
  "data": {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| Token 类型不是 refresh | `401` | `{"status": false, "message": "令牌类型错误，需要刷新令牌"}` |
| Token 无效 / 过期 / 已撤销 | `401` | `{"status": false, "message": "刷新令牌无效或已过期"}` |

> 说明：以上为 `apps/accounts/views.py` 的 `RefreshView` 实际返回的中文文案（视图层对 `jwt_auth.verify_token` 抛出的异常统一归类：类型不匹配 →「令牌类型错误，需要刷新令牌」，其余 →「刷新令牌无效或已过期」）。旧文档中的 `"Token has expired"` / `"Not a refresh token"` 是 PyJWT 库内部消息，不会直接返回给前端。

---

### 4. 登出 — `POST /api/auth/logout`

将当前 `access_token` 加入 Redis 黑名单，使其立即失效。

**请求头：**

| Header | 值 | 必填 |
|------|------|:--:|
| `Authorization` | `Bearer <access_token>` | ✅ |

**成功响应 `200`：**

```json
{"status": true, "data": {}}
```

> 说明：登出成功返回 `data: {}`（空对象，`apps/accounts/views.py:125` 的 `Response({})`），而非仅 `{"status": true}`。前端 `auth.ts` 的 `logout()` 解包后得到空对象，不消费任何字段。

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| 未携带 Token（非 Bearer） | `401` | `{"status": false, "message": "请先登录"}`（中间件） |
| Token 无效 / 过期 / 已撤销 | `401` | `{"status": false, "message": "登录已过期或令牌无效"}`（中间件） |
| Redis 不可用（无法持久化黑名单） | `503` | `{"status": false, "message": "Redis 不可用，无法撤销令牌", "retry": true}` |

> **设计说明**：Token 黑名单存储在 Redis 中，服务重启不丢失。Redis 不可用时登出返回 503 并标记 `retry: true`，前端应提示用户稍后重试（`AppSidebar.vue` 捕获 503 + `retry` 时保留本地登录态并提示）。

---

### 5. 当前用户 — `GET /api/auth/me`

从 JWT 解析 `user_id`，返回当前登录用户信息。

**请求头：**

| Header | 值 | 必填 |
|------|------|:--:|
| `Authorization` | `Bearer <access_token>` | ✅ |

**成功响应 `200`：**

```json
{
  "status": true,
  "data": {
    "user": {
      "id": 1,
      "username": "admin"
    }
  }
}
```

**错误响应：**

| 条件 | HTTP | 响应体 |
|------|:--:|------|
| 未携带 Token（非 Bearer） | `401` | `{"status": false, "message": "请先登录"}`（中间件） |
| Token 无效 / 过期 / 已撤销 | `401` | `{"status": false, "message": "登录已过期或令牌无效"}`（中间件） |
| Token 中 user_id 对应的用户不存在 | `404` | `{"status": false, "message": "用户不存在"}` |

> ⚠️ 偏差：`/me` 端点后端已就绪，但前端当前**未消费**。页面刷新恢复登录态实际走 `localStorage.auth_accounts` token 池（`frontend/src/shared/auth/token-storage.ts` 的 `getToken()`，由 `router.ts` 守卫读取），不调用 `/me`（已登记）。

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
// frontend/src/shared/api/auth.ts —— 登录/注册/登出（真实代码）
import djangoClient from "@/shared/api-client"
import type { AuthResponse } from "@/shared/types/auth"

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/login", { username, password })
  return data // → { status: true, data: { access_token, refresh_token, token_type, user } }
}

export async function register(
  username: string, password: string, password2: string, email: string,
): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/register", {
    username, password, password2, email,
  })
  return data
}

export async function logout(): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>("/auth/logout")
  return data // 成功 → { status: true, data: {} }
}
```

```typescript
// frontend/src/shared/api-client.ts —— 信封类型 + refresh 出口（真实代码）
export interface DjangoResponse<T = unknown> {
  status: boolean
  data?: T
  message?: string
}

// axios 实例 baseURL: "/api"；401 → refresh → 重放由拦截器驱动
refreshRequest: (body) => axios.post("/api/auth/refresh", body),
```

```typescript
// frontend/src/views/composables/useAuthFlow.ts —— 登录/注册消费方式
if (data.status && "refresh_token" in data.data) {
  auth.loginAccount(name, data.data.access_token, data.data.refresh_token)
  router.push("/dashboard")
}
```

> 说明：`/auth/login`、`/auth/register`、`/auth/logout` 均相对 `djangoClient` 的 `baseURL: "/api"`，实际请求 `/api/auth/*`；`/auth/refresh` 由 `api-client.ts` 的 `refreshRequest` 用绝对路径 `/api/auth/refresh` 直连（不经拦截器自身刷新，避免递归）。

## 相关文件

| 层 | 文件 | 说明 |
|------|------|------|
| 视图 | `apps/accounts/views.py` | 5 端点实现（Login / Register / Refresh / Logout / Me） |
| 校验 | `apps/accounts/serializers.py` | 登录/注册/刷新入参校验与错误文案 |
| 路由 | `apps/accounts/urls.py` | 5 路由（login / register / refresh / logout / me） |
| JWT | `shared/auth/jwt_auth.py` | Token 生成 / 验证 / 黑名单 |
| 中间件 | `gateway/middleware.py` | JWT 中间件 + `PUBLIC_PREFIXES` 白名单 + `RETIRED_AUTH_PATHS` |
| 挂载 | `config/urls.py` | `api/auth/` → `apps.accounts.urls` |
| 前端 API | `frontend/src/shared/api/auth.ts` | `login()` / `register()` / `logout()` |
| 前端客户端 | `frontend/src/shared/api-client.ts` | `baseURL: /api`、`DjangoResponse` 信封、`refreshRequest` |
