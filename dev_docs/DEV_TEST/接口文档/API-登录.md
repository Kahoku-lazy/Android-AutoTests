# API-登录与认证 — /api/auth/*

> 认证域全集 5 个端点：登录 / 注册 / 刷新 / 登出 / me。登录页（LoginView）直接调用登录与注册两个。
> 真相源：`apps/accounts/urls.py` + `views.py` + `serializers.py` + `shared/renderers.py`。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 登录接口 | POST /api/auth/login/ | 公开 | 登录，签发访问/刷新令牌对 |
| 注册接口 | POST /api/auth/register/ | 公开 | 注册，签发访问/刷新令牌对 |
| 刷新令牌接口 | POST /api/auth/refresh/ | 公开 | 用 refresh_token 换新 access_token |
| 登出接口 | POST /api/auth/logout/ | 需登录 | 按会话 `sid` 作废本次登录的**全部**令牌（access + refresh） |
| 当前用户接口 | GET /api/auth/me/ | 需登录 | 当前登录用户信息 |

## 2. 通用约定

- 路径**必须带尾斜杠**，缺失即 404（`APPEND_SLASH=False`，容错中间件已删除，见 `openspec/specs/api-path-convention`）。
- 响应信封：成功 `{status: true, data}`，失败 `{status: false, message}`（`EnvelopeJSONRenderer` 统一包裹）。
- 需登录端点携带：`Authorization: Bearer <access_token>`。
- **鉴权发生在网关**：`logout` / `me` 的 401 由 `gateway/middleware.py` 直接返回 —— 不经过 DRF，也不经过 `EnvelopeJSONRenderer`；响应体形状与信封一致，文案见 §6、§7。
- 请求体为 JSON。后端**未强制校验** `Content-Type`，DRF 默认也接受表单编码；各节表格里的 `Content-Type` 描述的是既有调用方的实际用法。
- Token：HS256；access TTL 3600s，refresh TTL 604800s。

---

## 3. 登录接口：POST /api/auth/login/

| 项 | 值 |
|---|---|
| 鉴权 | 公开（AllowAny） |
| Content-Type | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| username | string | 否 | 用户名；不 trim（trim_whitespace=False） |
| password | string | 否 | 密码 |

### 成功响应（200）

```json
{
  "status": true,                        # 请求是否成功，恒为 true
  "data": {
    "access_token": "<JWT>",             # 访问令牌（HS256，有效期 1 小时）
    "refresh_token": "<JWT>",            # 刷新令牌（HS256，有效期 7 天）
    "token_type": "bearer",              # 令牌类型，固定 bearer
    "user": {                            # 登录用户信息
      "id": 1,                           # 用户 ID
      "username": "admin"                # 用户名
    }
  }
}
```

### 失败响应

```json
{
  "status": false,                       # 请求是否成功，恒为 false
  "message": "用户名或密码错误"           # 错误文案（无技术术语）
}
```

### 错误码与文案（校验顺序即优先级）

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 请输入用户名和密码 | 用户名与密码均空 |
| 400 | 请输入用户名 | 用户名为空 |
| 400 | 请输入密码 | 密码为空 |
| 400 | 用户名不能为空白 | 用户名纯空白 |
| 400 | 用户名过长，最多150个字符 | 用户名长度 > 150 |
| 401 | 用户名或密码错误 | 用户不存在 / 密码错误（统一口径，防枚举） |
| 400 | 请求格式错误 | 请求体非合法 JSON |

---

## 4. 注册接口：POST /api/auth/register/

| 项 | 值 |
|---|---|
| 鉴权 | 公开（AllowAny） |
| Content-Type | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| username | string | 否 | 用户名（后端 strip），3~20 字符 |
| password | string | 否 | 密码（后端 strip），>=6 位 |
| password2 | string | 否 | 确认密码，须与 password 一致 |
| email | string | 否 | 邮箱，须含 @ |

### 成功响应（200）

```json
{
  "status": true,                        # 请求是否成功，恒为 true
  "data": {
    "access_token": "<JWT>",             # 访问令牌（HS256，1 小时）
    "refresh_token": "<JWT>",            # 刷新令牌（HS256，7 天）
    "token_type": "bearer",              # 令牌类型，固定 bearer
    "user": {                            # 注册用户信息
      "id": 2,                           # 用户 ID
      "username": "tester01",            # 用户名
      "email": "tester01@test.local"     # 邮箱
    }
  }
}
```

### 错误码与文案（校验顺序即优先级）

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 请输入用户名和密码 | 用户名与密码均空 |
| 400 | 请输入用户名 | 用户名为空 |
| 400 | 请输入密码 | 密码为空 |
| 400 | 用户名至少 3 个字符 | 用户名长度 < 3 |
| 400 | 用户名最多 20 个字符 | 用户名长度 > 20 |
| 400 | 密码至少 6 位 | 密码长度 < 6 |
| 400 | 两次密码不一致 | password != password2 |
| 400 | 请输入邮箱 | 邮箱为空 |
| 400 | 邮箱格式不正确 | 邮箱不含 @ |
| 409 | 用户名已存在 | 用户名已注册 |

---

## 5. 刷新令牌接口：POST /api/auth/refresh/

| 项 | 值 |
|---|---|
| 鉴权 | 公开（AllowAny） |
| Content-Type | application/json |

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| refresh_token | string | 是（业务上必需） | 刷新令牌。接口层声明为 `required=False` / `allow_blank=True`：**缺字段不会得到 400 的字段必填错误**，而是走 401「刷新令牌无效或已过期」 |

### 成功响应（200）

```json
{
  "status": true,                        # 请求是否成功，恒为 true
  "data": {
    "access_token": "<new JWT>",         # 新访问令牌（HS256，1 小时）
    "token_type": "bearer"               # 令牌类型，固定 bearer
  }
}
```

> 仅签发新 access_token，**不**返回新 refresh_token。

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 令牌类型错误，需要刷新令牌 | 传入的是 access_token / 类型不符 |
| 401 | 刷新令牌无效或已过期 | 令牌无效、过期，或已被吊销（`jti` 单令牌 或 `sid` 整会话，见 §6） |

---

## 6. 登出接口：POST /api/auth/logout/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（IsAuthenticated，Bearer Token） |

### 请求

无请求体；access_token 经 `Authorization: Bearer <access_token>` 传入。

### 成功响应（200）

```json
{
  "status": true,                        # 请求是否成功，恒为 true
  "data": {}                             # 空对象，无业务数据
}
```

### 失败响应（503）

```json
{
  "status": false,                        # 请求是否成功，恒为 false
  "message": "Redis 不可用，无法撤销令牌", # 错误文案
  "retry": true                           # 是否可重试
}
```

### 失败响应（401）

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未带 `Authorization: Bearer` 头 —— 由网关中间件拦下，请求到不了视图 |
| 401 | 登录已过期或令牌无效 | 令牌无效、过期，或已被登出吊销（同上，网关拦下） |

> 登出按**会话**作废：以 `sid` 为粒度写 `jwt:session_revoked:<sid>`（TTL = `JWT_REFRESH_TTL`，7 天），本次登录的 access 与 refresh **一起失效**。签发时没有 `sid` 的历史令牌按 `jti` 兜底写 `jwt:blacklist:<jti>`（TTL = 令牌剩余寿命，最少 60 秒）。见 `openspec/specs/auth-session`。

---

## 7. 当前用户接口：GET /api/auth/me/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录（IsAuthenticated，Bearer Token） |

### 请求

无请求体；`Authorization: Bearer <access_token>`。

### 成功响应（200）

```json
{
  "status": true,                        # 请求是否成功，恒为 true
  "data": {
    "user": {                            # 当前用户信息
      "id": 1,                           # 用户 ID
      "username": "admin",               # 用户名
      "is_superuser": true               # 是否超级管理员
    }
  }
}
```

### 错误码与文案

| HTTP | message | 触发条件 |
|---|---|---|
| 401 | 请先登录 | 未带 `Authorization: Bearer` 头 —— 由 `gateway/middleware.py` 拦下，不经视图 |
| 401 | 登录已过期或令牌无效 | 令牌无效、过期，或已被登出吊销（同上，网关拦下） |
| 401 | 用户不存在或已删除 | 令牌有效，但 `sub` 指向的用户已被删除 —— DRF 鉴权类在进入视图前拦下 |
| 404 | 用户不存在 | 视图内的兜底分支。**当前链路不可达**：用户已删的情况由上一行的 401 抢先返回 |
