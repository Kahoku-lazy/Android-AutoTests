# 设计：登录模块 Vue → Django DRF → ORM（apps.accounts）

> 状态：待用户审阅（自检已修 logout 503/`retry` 歧义）  
> 日期：2026-08-12  
> 相关：`dev_docs/设计-DRF迁移方案-evaluator试点.md`、现有 `apps/ai_assistant/views/auth_views.py`

## 1. 目标

将平台登录从「Vue → Django 函数视图 → ORM」升级为：

**Vue → Django DRF（Serializer + APIView）→ Django ORM**

认证成为平台级能力，不再挂在 `ai_assistant` 下。

## 2. 已确认决策

| 项 | 选择 |
|---|---|
| 分层 | Vue → DRF → ORM |
| URL | `/api/auth/*`；**不**兼容旧 `/api/ai/auth/*` |
| 代码归属 | 独立 App：`apps.accounts` |
| 响应格式 | 信封：成功 `{ status: true, data }`；失败 `{ status: false, message }` |
| 实现形态 | 五个 `APIView` + Serializer（非 ViewSet、非自定义 User） |
| 用户模型 | 继续使用 `django.contrib.auth.models.User` |
| JWT | 复用 `shared.auth.jwt_auth` / `shared.auth.drf_auth.JWTAuthentication` |

## 3. 架构

```
Vue (LoginView / api-client / auth interceptors)
        │  HTTP JSON
        ▼
apps.accounts (DRF APIView + Serializer)
        │  authenticate / User.objects / create_token_pair
        ▼
Django ORM (auth.User)
        +
shared.auth.jwt_auth          # 发牌 / 验牌 / 黑名单
shared.auth.drf_auth          # 受保护接口鉴权
shared.renderers.EnvelopeJSONRenderer
```

### 边界

| 模块 | 职责 |
|------|------|
| `apps.accounts` | 登录域 HTTP：login / register / refresh / logout / me |
| `shared.auth` | JWT 工具与 DRF Authentication；不写业务 View |
| `apps.ai_assistant` | 删除平台登录实现与路由；只保留 AI 业务 |

### 挂载

- `config/urls.py`：`path("api/auth/", include("apps.accounts.urls"))`
- 旧路径 `/api/ai/auth/*`：**直接移除**（404）

## 4. 端点契约

| 方法 | 路径 | 权限 | 作用 |
|------|------|------|------|
| POST | `/api/auth/login` | AllowAny | 登录，返回 JWT 对 |
| POST | `/api/auth/register` | AllowAny | 注册并自动登录 |
| POST | `/api/auth/refresh` | AllowAny | refresh → 新 access |
| POST | `/api/auth/logout` | IsAuthenticated | 拉黑当前 access |
| GET | `/api/auth/me` | IsAuthenticated | 当前用户信息 |

### 成功响应（2xx，经 EnvelopeJSONRenderer）

```json
// POST /login、/register
{
  "status": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer",
    "user": { "id": 1, "username": "admin" }
  }
}

// POST /refresh
{
  "status": true,
  "data": {
    "access_token": "...",
    "token_type": "bearer"
  }
}

// POST /logout
{ "status": true, "data": {} }

// GET /me
{
  "status": true,
  "data": {
    "user": { "id": 1, "username": "admin" }
  }
}
```

### 失败响应（4xx/5xx）

```json
{ "status": false, "message": "用户名或密码错误" }
```

校验中文文案尽量沿用现有 `auth_views.py`（空字段、过长、两次密码不一致、邮箱格式、重复用户名 409、Redis 不可用 503 等），避免体验回退。

### 破坏性变更

1. 前缀：`/api/ai/auth` → `/api/auth`
2. 成功体：扁平 `access_token` → 进入 `data`
3. 旧路径不再提供

## 5. 后端文件结构

```
apps/accounts/
  __init__.py
  apps.py
  urls.py           # 5 条 path → APIView
  serializers.py    # LoginSerializer / RegisterSerializer / RefreshSerializer
  views.py          # LoginView / RegisterView / RefreshView / LogoutView / MeView
```

### 实现要点

- `LoginView` / `RegisterView` / `RefreshView`：`permission_classes = [AllowAny]`
- `LogoutView` / `MeView`：默认 `IsAuthenticated` + `JWTAuthentication`
- 发牌 / 验牌 / 黑名单：只调用 `shared.auth.jwt_auth`，不复制逻辑
- `register` 成功后返回与 login 同结构的 token 对（保持现行为）
- `logout`：Redis 不可用时返回 503，与现行为对齐
- 不新建迁移表（无新 Model）

### 删除 / 清理

- `apps/ai_assistant/views/auth_views.py`
- `apps/ai_assistant/urls.py` 中 auth 五条路由及相关 import
- `apps/ai_assistant/views/__init__.py`（若有）对 auth 的导出

### 配置

- `INSTALLED_APPS` 增加 `apps.accounts`
- OpenAPI：随默认 `AutoSchema` 暴露；无需单独试点配置

## 6. 前端改动面

| 文件 | 变更 |
|------|------|
| `frontend/src/shared/api/auth.ts` | 路径 → `/auth/login`、`/auth/register`；按信封解包 |
| `frontend/src/shared/types/auth.ts` | `AuthResponse` 对齐 `{ status, data?, message? }` |
| `frontend/src/shared/api-client.ts` | refresh URL → `/api/auth/refresh` |
| `frontend/src/shared/api-auth-interceptors.ts` | 从 `data` 取 `access_token` |
| `frontend/src/modules/ai-assistant/api/sse.ts` | refresh URL + 解包 |
| `frontend/src/views/composables/useAuthFlow.ts` 等 | 按新类型读取 token |

登录页视觉与交互流程不变，只改契约消费方式。

## 7. 测试改动面

| 范围 | 变更 |
|------|------|
| `tests/auth/conftest.py` | 端点常量 → `/api/auth/...` |
| `tests/auth/schemas.py` | 成功 Schema 改为 `data` 嵌套 |
| `tests/auth/test_*.py` | 断言 `body["data"][...]`；错误仍看 `message` |
| `tests/auth/e2e/` | 多数走前端；若有硬编码旧 URL 一并改 |

## 8. 错误处理

| 场景 | HTTP | 响应 |
|------|------|------|
| Serializer 校验失败 | 400 | `{ status: false, message }`（首条中文） |
| 用户名或密码错误 | 401 | 固定文案，不泄露用户是否存在 |
| 无效 / 过期 refresh | 401 | `{ status: false, message }` |
| 用户名已存在 | 409 | `{ status: false, message: "用户名已存在" }` |
| logout 时 Redis 不可用 | 503 | `{ status: false, message, retry: true }`（见下） |
| me 用户已删除 | 404 | `{ status: false, message }` |

**logout 503 特例**：现有 `tests/auth/test_logout.py` 依赖 `retry: true`。默认 `EnvelopeJSONRenderer` 对 4xx/5xx 只输出 `{ status, message }`，会丢掉 `retry`。实现时二选一（优先前者）：

1. 在 `LogoutView` 对该错误返回已包好的最终 JSON（或局部 renderer），保证 body 含 `retry: true`
2. 小幅扩展 `EnvelopeJSONRenderer`：若 data 含布尔字段 `retry`，透传到信封

禁止向用户暴露堆栈、ORM、Redis 原文；技术细节只写日志。

## 9. 验收标准

1. 五个端点仅挂在 `/api/auth/*`；访问 `/api/ai/auth/*` 为 404
2. 成功为 `{ status: true, data: ... }`；失败为 `{ status: false, message }`
3. Vue 登录 / 注册 / 多账号切换 / access 自动 refresh 可用
4. `tests/auth` API 用例按新契约通过；关键 E2E 冒烟通过
5. Swagger / drf-spectacular 可见 accounts 端点
6. `ai_assistant` 不再包含平台登录实现

## 10. Non-goals（本轮不做）

- 自定义 `AUTH_USER_MODEL`
- OAuth / 第三方登录
- 旧路径兼容或 301/转发
- 登录页 UI 改版
- 将认证硬套成资源型 `ModelViewSet`

## 11. 实施顺序（建议）

1. 新建 `apps.accounts`（serializers + views + urls）并挂载
2. 前端改路径与信封解包
3. 删除 `ai_assistant` 旧 auth
4. 更新 `tests/auth` Schema 与端点
5. 跑 API 测试 + 登录 E2E 冒烟
