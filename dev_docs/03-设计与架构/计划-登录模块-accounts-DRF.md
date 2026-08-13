# 登录模块 accounts DRF 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将平台登录从 `ai_assistant` 函数视图迁到独立 `apps.accounts`，形成 Vue → Django DRF → ORM，路径为 `/api/auth/*`，响应统一信封 `{status, data|message}`。

**Architecture:** 新建 `apps.accounts`（五个 `APIView` + Serializer）；JWT 继续用 `shared.auth.jwt_auth`；鉴权用 `shared.auth.drf_auth.JWTAuthentication`；成功/失败由 `EnvelopeJSONRenderer` 包信封（logout 503 需透传 `retry`）。删除 `/api/ai/auth/*`，前端与 `tests/auth` 同步改路径与解包。

**Tech Stack:** Django 4.x、DRF、django.contrib.auth.User、PyJWT（现有）、Vue 3、axios、pytest + jsonschema、Playwright E2E

**Spec:** `dev_docs/03-设计与架构/设计-登录模块-accounts-DRF.md`

## Global Constraints

- App 名：`apps.accounts`（禁止命名为 `apps.auth`，避免与 `django.contrib.auth` 冲突）
- URL：仅 `/api/auth/login|register|refresh|logout|me`；旧 `/api/ai/auth/*` 必须 404
- 成功：`{ "status": true, "data": ... }`；失败：`{ "status": false, "message": "..." }`
- logout Redis 不可用：HTTP 503，body 含 `retry: true`
- 不新建 User Model / 不做旧路径兼容 / 不改登录页视觉
- 校验中文文案尽量与旧 `auth_views.py` 一致
- 未获用户明确要求前，可不执行 plan 中的 `git commit` 步骤

---

## File Structure

| 路径 | 职责 |
|------|------|
| `apps/accounts/__init__.py` | 包标记 |
| `apps/accounts/apps.py` | AppConfig |
| `apps/accounts/serializers.py` | Login / Register / Refresh 入参校验 |
| `apps/accounts/views.py` | 五个 APIView |
| `apps/accounts/urls.py` | 路由表 |
| `config/settings.py` | INSTALLED_APPS 注册 |
| `config/urls.py` | `api/auth/` include |
| `shared/renderers.py` | 4xx/5xx 透传 `retry` |
| `apps/ai_assistant/views/auth_views.py` | **删除** |
| `apps/ai_assistant/views/__init__.py` | 去掉 auth 导出 |
| `apps/ai_assistant/urls.py` | 去掉 auth 五条路由 |
| `frontend/src/shared/types/auth.ts` | AuthResponse 信封类型 |
| `frontend/src/shared/api/auth.ts` | 新路径 + 返回信封 |
| `frontend/src/shared/api-client.ts` | refresh URL |
| `frontend/src/shared/api-auth-interceptors.ts` | `data.data.access_token` |
| `frontend/src/modules/ai-assistant/api/sse.ts` | refresh URL + 解包 |
| `frontend/src/views/composables/useAuthFlow.ts` | 从 `data.data` 取 token |
| `frontend/tests/login/p0/*` | mock 信封形状 |
| `tests/auth/conftest.py` / `schemas.py` / `test_*.py` | 新 URL + 信封断言 |
| `tests/e2e/helpers.py` / `tests/auth/e2e/*` | `/api/auth/me`、route 拦截 URL |

---

### Task 1: 脚手架 `apps.accounts` + 挂载空路由

**Files:**
- Create: `apps/accounts/__init__.py`
- Create: `apps/accounts/apps.py`
- Create: `apps/accounts/urls.py`（先空列表或占位）
- Modify: `config/settings.py`（INSTALLED_APPS）
- Modify: `config/urls.py`

**Interfaces:**
- Consumes: 无
- Produces: App `apps.accounts` 可被 Django 加载；前缀 `/api/auth/` 已 include

- [ ] **Step 1: 创建 App 文件**

`apps/accounts/__init__.py`：空文件。

`apps/accounts/apps.py`：

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "平台认证"
```

`apps/accounts/urls.py`：

```python
"""Platform auth URLs — /api/auth/*."""

from django.urls import path

app_name = "accounts"

urlpatterns = []
```

- [ ] **Step 2: 注册 App 与路由**

在 `config/settings.py` 的 `INSTALLED_APPS` 中，于 `apps.ai_assistant` **之前**插入：

```python
"apps.accounts",
```

在 `config/urls.py` 增加（建议紧挨 `api/ai/` 之前）：

```python
path("api/auth/", include("apps.accounts.urls")),
```

并确保文件顶部有：`from django.urls import include, path`（若已有 `include` 则勿重复）。

- [ ] **Step 3: 验证 Django 能加载**

Run:

```bash
python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); from django.urls import reverse; print('accounts ok')"
```

Expected: 打印 `accounts ok`，无 ImportError。

- [ ] **Step 4: Commit（可选，需用户同意）**

```bash
git add apps/accounts config/settings.py config/urls.py
git commit -m "$(cat <<'EOF'
chore(accounts): scaffold apps.accounts and mount /api/auth/

EOF
)"
```

---

### Task 2: Envelope 透传 `retry` + Serializers + LoginView

**Files:**
- Modify: `shared/renderers.py`
- Create: `apps/accounts/serializers.py`
- Create: `apps/accounts/views.py`（先实现 LoginView）
- Modify: `apps/accounts/urls.py`
- Modify: `tests/auth/conftest.py`（LOGIN_URL + auth_token 解包；可先只改 login 相关常量，或一次改全五常量）
- Modify: `tests/auth/schemas.py`（信封版 AUTH_SUCCESS / ERROR）

**Interfaces:**
- Consumes: `shared.auth.jwt_auth.create_token_pair`；`django.contrib.auth.authenticate`
- Produces:
  - `LoginSerializer` — `validate()` 后提供 `username`/`password`；`create` 不用
  - `LoginView.post` → `Response(payload, status=200)`，payload 为裸 data（无 status 字段），由 renderer 包信封
  - `EnvelopeJSONRenderer`：错误体若含 `retry` 则写入最终 JSON

- [ ] **Step 1: 扩展 EnvelopeJSONRenderer**

修改 `shared/renderers.py` 的错误分支：

```python
if response is not None and response.status_code >= 400:
    wrapped = {"status": False, "message": _extract_message(data)}
    if isinstance(data, dict) and "retry" in data:
        wrapped["retry"] = bool(data["retry"])
else:
    wrapped = {"status": True, "data": data}
```

- [ ] **Step 2: 写 Serializers（Login 优先，Register/Refresh 可同文件先写好）**

`apps/accounts/serializers.py`：

```python
"""Auth serializers — login / register / refresh input validation."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        username = attrs.get("username", "")
        password = attrs.get("password", "")

        if not username and not password:
            raise serializers.ValidationError("请输入用户名和密码")
        if not username:
            raise serializers.ValidationError("请输入用户名")
        if not password:
            raise serializers.ValidationError("请输入密码")
        if not str(username).strip():
            raise serializers.ValidationError("用户名不能为空白")
        if len(str(username)) > 150:
            raise serializers.ValidationError("用户名过长，最多150个字符")

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("用户名或密码错误")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(required=False, allow_blank=True, default="")
    password2 = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        username = str(attrs.get("username", "")).strip()
        password = str(attrs.get("password", "")).strip()
        password2 = str(attrs.get("password2", "")).strip()
        email = str(attrs.get("email", "")).strip()

        if not username and not password:
            raise serializers.ValidationError("请输入用户名和密码")
        if not username:
            raise serializers.ValidationError("请输入用户名")
        if not password:
            raise serializers.ValidationError("请输入密码")
        if len(username) < 3:
            raise serializers.ValidationError("用户名至少 3 个字符")
        if len(username) > 20:
            raise serializers.ValidationError("用户名最多 20 个字符")
        if password != password2:
            raise serializers.ValidationError("两次密码不一致")
        if not email:
            raise serializers.ValidationError("请输入邮箱")
        if "@" not in email:
            raise serializers.ValidationError("邮箱格式不正确")
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("用户名已存在")

        attrs["username"] = username
        attrs["password"] = password
        attrs["email"] = email
        return attrs


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=False, allow_blank=True, default="")
```

**注意：** DRF 的 `ValidationError("字符串")` 经 Envelope 后 `message` 为该字符串。认证失败「用户名或密码错误」在旧实现是 **401**；`serializer.is_valid()` 默认变 400。LoginView 必须对认证失败单独返回 401（见 Step 3）。

- [ ] **Step 3: 实现 LoginView**

`apps/accounts/views.py`：

```python
"""Platform auth APIViews — login / register / refresh / logout / me."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.auth.jwt_auth import (
    BlacklistUnavailableError,
    blacklist_token,
    create_access_token,
    create_token_pair,
    verify_token,
)

from .serializers import LoginSerializer, RefreshSerializer, RegisterSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            msg = _first_error(ser.errors)
            # 认证失败保持 401；其余校验 400
            code = (
                status.HTTP_401_UNAUTHORIZED
                if msg == "用户名或密码错误"
                else status.HTTP_400_BAD_REQUEST
            )
            return Response({"detail": msg}, status=code)

        user = ser.validated_data["user"]
        tokens = create_token_pair(str(user.id))
        return Response(
            {
                **tokens,
                "user": {"id": user.id, "username": user.username},
            }
        )


def _first_error(errors) -> str:
    """Extract first user-facing message from DRF error dict/list."""
    if isinstance(errors, dict):
        non_field = errors.get("non_field_errors")
        if isinstance(non_field, list) and non_field:
            return str(non_field[0])
        for value in errors.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    if isinstance(errors, list) and errors:
        return str(errors[0])
    return "请求无效"
```

（同文件后续 Task 再追加其余 View；本 Task 可先只导出 LoginView。）

- [ ] **Step 4: 挂 login 路由**

`apps/accounts/urls.py`：

```python
from django.urls import path

from .views import LoginView

app_name = "accounts"

urlpatterns = [
    path("login", LoginView.as_view(), name="login"),
]
```

- [ ] **Step 5: 更新测试契约（schemas + conftest）**

`tests/auth/conftest.py` 端点改为：

```python
LOGIN_URL = "/api/auth/login"
REGISTER_URL = "/api/auth/register"
REFRESH_URL = "/api/auth/refresh"
LOGOUT_URL = "/api/auth/logout"
ME_URL = "/api/auth/me"
```

`auth_token` fixture：

```python
body = resp.json()
assert body.get("status") is True, body
data = body["data"]
return {
    "access_token": data["access_token"],
    "refresh_token": data["refresh_token"],
}
```

`tests/auth/schemas.py` — `AUTH_SUCCESS_SCHEMA` 改为：

```python
AUTH_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "minLength": 10},
                "refresh_token": {"type": "string", "minLength": 10},
                "token_type": {"const": "bearer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                    },
                    "required": ["id", "username"],
                    "additionalProperties": False,
                },
            },
            "required": ["access_token", "refresh_token", "token_type", "user"],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}
```

同步改 `REGISTER_SUCCESS_SCHEMA`（user 含 `email`）、`REFRESH_SUCCESS_SCHEMA`、`ME_USER_SCHEMA`、`LOGOUT_SUCCESS_SCHEMA`：

```python
LOGOUT_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {"type": "object"},
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

REFRESH_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "minLength": 10},
                "token_type": {"const": "bearer"},
            },
            "required": ["access_token", "token_type"],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

ME_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                    },
                    "required": ["id", "username"],
                },
            },
            "required": ["user"],
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

REGISTER_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "minLength": 10},
                "refresh_token": {"type": "string", "minLength": 10},
                "token_type": {"const": "bearer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                    },
                    "required": ["id", "username", "email"],
                },
            },
            "required": ["access_token", "refresh_token", "token_type", "user"],
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}
```

`ERROR_RESPONSE_SCHEMA` 保持 `{status:false, message}`；另增：

```python
ERROR_503_RETRY_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": False},
        "message": {"type": "string", "minLength": 1},
        "retry": {"const": True},
    },
    "required": ["status", "message", "retry"],
    "additionalProperties": False,
}
```

- [ ] **Step 6: 修正 test_login 中直接读扁平字段的断言（若有）**

全局将 `tests/auth/test_login.py` 里对成功体的 `body["access_token"]` 改为 `body["data"]["access_token"]`（本 Task 至少保证 login 文件可跑）。

- [ ] **Step 7: 跑登录 API 测试**

Run:

```bash
pytest tests/auth/test_login.py -v --tb=short
```

Expected: 全部 PASS（需后端已启动或使用项目惯用的 live API fixture；若测试依赖 `base_url` 真服务，先 `python run.py start` 或按 `tests/auth/README.md` 启动）。

若失败：对照 message 文案与 401/400 状态码是否与旧行为一致。

- [ ] **Step 8: Commit（可选）**

```bash
git add shared/renderers.py apps/accounts tests/auth/conftest.py tests/auth/schemas.py tests/auth/test_login.py
git commit -m "$(cat <<'EOF'
feat(accounts): add DRF LoginView under /api/auth/login

EOF
)"
```

---

### Task 3: RegisterView + RefreshView

**Files:**
- Modify: `apps/accounts/views.py`
- Modify: `apps/accounts/urls.py`
- Modify: `tests/auth/test_register.py`、`tests/auth/test_refresh.py`（扁平 → `data`；硬编码旧 URL → 常量）

**Interfaces:**
- Consumes: `RegisterSerializer`、`RefreshSerializer`、`create_token_pair`、`create_access_token`、`verify_token`
- Produces:
  - `POST /api/auth/register` — 成功 200；用户名冲突 **409**
  - `POST /api/auth/refresh` — 成功 `{access_token, token_type}` 进 data

- [ ] **Step 1: 追加 RegisterView / RefreshView**

在 `views.py` 追加：

```python
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            msg = _first_error(ser.errors)
            code = (
                status.HTTP_409_CONFLICT
                if msg == "用户名已存在"
                else status.HTTP_400_BAD_REQUEST
            )
            return Response({"detail": msg}, status=code)

        data = ser.validated_data
        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data["email"],
        )
        tokens = create_token_pair(str(user.id))
        return Response(
            {
                **tokens,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            }
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        ser = RefreshSerializer(data=request.data)
        ser.is_valid(raise_exception=False)
        token = (ser.validated_data or {}).get("refresh_token") or request.data.get(
            "refresh_token", ""
        )
        try:
            payload = verify_token(token, expected_type="refresh")
            if payload.get("type") != "refresh":
                return Response(
                    {"detail": "Not a refresh token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            new_access = create_access_token(payload["sub"])
            return Response(
                {"access_token": new_access, "token_type": "bearer"}
            )
        except Exception as exc:
            return Response(
                {"detail": str(exc) or "Invalid token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
```

- [ ] **Step 2: 注册路由**

```python
path("register", RegisterView.as_view(), name="register"),
path("refresh", RefreshView.as_view(), name="refresh"),
```

- [ ] **Step 3: 改测试解包**

在 `test_register.py` / `test_refresh.py`：
- 成功：`body["data"]["access_token"]` 等
- 文档字符串中的旧 URL 改为 `/api/auth/...`
- 任何硬编码 `/api/ai/auth/...` 改为使用 conftest 常量

`test_refresh.py` 中：

```python
assert body["data"]["access_token"] != auth_token["access_token"]
new_access = body["data"]["access_token"]
```

- [ ] **Step 4: 跑测试**

```bash
pytest tests/auth/test_register.py tests/auth/test_refresh.py -v --tb=short
```

Expected: PASS。

- [ ] **Step 5: Commit（可选）**

```bash
git add apps/accounts/views.py apps/accounts/urls.py tests/auth/test_register.py tests/auth/test_refresh.py
git commit -m "$(cat <<'EOF'
feat(accounts): add register and refresh DRF endpoints

EOF
)"
```

---

### Task 4: LogoutView + MeView

**Files:**
- Modify: `apps/accounts/views.py`
- Modify: `apps/accounts/urls.py`
- Modify: `tests/auth/test_logout.py`、`tests/auth/test_me.py`

**Interfaces:**
- Consumes: `JWTAuthentication`（默认）、`blacklist_token`、`User.objects.get`
- Produces:
  - `POST /api/auth/logout` → 成功 `Response({})`；503 时 `Response({"detail": ..., "retry": True}, status=503)`
  - `GET /api/auth/me` → `Response({"user": {...}})`

- [ ] **Step 1: 实现 LogoutView / MeView**

```python
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            try:
                blacklist_token(auth_header[7:])
            except BlacklistUnavailableError as exc:
                return Response(
                    {"detail": str(exc), "retry": True},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        return Response({})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = getattr(request.user, "id", None)
        if not user_id:
            return Response(
                {"detail": "Not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"user": {"id": user.id, "username": user.username}})
```

说明：`JWTAuthentication` 返回的 `SimpleNamespace(id=..., is_authenticated=True)` 即 `request.user`。

- [ ] **Step 2: 挂路由**

```python
path("logout", LogoutView.as_view(), name="logout"),
path("me", MeView.as_view(), name="me"),
```

完整 `urlpatterns` 应为五条。

- [ ] **Step 3: 更新 logout/me 测试**

- 所有 `login_resp.json()["access_token"]` → `login_resp.json()["data"]["access_token"]`
- 成功 logout 可用 `LOGOUT_SUCCESS_SCHEMA` 校验（含 `data`）
- 硬编码旧 URL 改为常量

- [ ] **Step 4: 跑全量 Auth API**

```bash
pytest tests/auth/test_login.py tests/auth/test_register.py tests/auth/test_refresh.py tests/auth/test_logout.py tests/auth/test_me.py -v --tb=short
```

Expected: 全部 PASS（含 skip/xfail 保持原标记）。

- [ ] **Step 5: Commit（可选）**

```bash
git add apps/accounts tests/auth
git commit -m "$(cat <<'EOF'
feat(accounts): add logout and me DRF endpoints

EOF
)"
```

---

### Task 5: 前端契约对齐（路径 + 信封）

**Files:**
- Modify: `frontend/src/shared/types/auth.ts`
- Modify: `frontend/src/shared/api/auth.ts`
- Modify: `frontend/src/shared/api-client.ts`
- Modify: `frontend/src/shared/api-auth-interceptors.ts`
- Modify: `frontend/src/views/composables/useAuthFlow.ts`
- Modify: `frontend/src/modules/ai-assistant/api/sse.ts`
- Modify: `frontend/tests/login/p0/useAuthFlow.spec.ts`
- Modify: `frontend/tests/login/p0/apiAuthInterceptors.spec.ts`

**Interfaces:**
- Consumes: `/api/auth/*` 信封响应
- Produces: 前端类型与调用链统一读 `response.data`（axios）里的 `{status, data}`

- [ ] **Step 1: 更新类型**

`frontend/src/shared/types/auth.ts`：

```typescript
/** 单个账号的 token 对（localStorage.auth_accounts 的 value） */
export interface AccountTokens {
  access_token: string
  refresh_token: string
}

/** localStorage.auth_accounts 的完整存储格式 */
export type AuthPool = Record<string, AccountTokens>

/** 登录/注册成功时 data 载荷 */
export interface AuthTokenData {
  access_token: string
  refresh_token: string
  token_type?: string
  user?: { id: number; username: string; email?: string }
}

/** refresh 成功时 data 载荷 */
export interface AuthRefreshData {
  access_token: string
  token_type?: string
}

/** 登录/注册/refresh API 响应 — 信封格式 */
export type AuthResponse =
  | { status: true; data: AuthTokenData | AuthRefreshData }
  | { status: false; message: string }

/** 登录页视图状态机 */
export type ViewState = 'switchPrompt' | 'login' | 'register'

/** 表单字段校验错误（key 为字段名） */
export interface FieldErrors {
  username?: string
  password?: string
  password2?: string
  email?: string
}
```

- [ ] **Step 2: 更新 auth API**

`frontend/src/shared/api/auth.ts`：

```typescript
/** Auth API — 登录/注册 HTTP 调用。不从属于任何业务模块，作为认证基础设施独立存在。 */
import djangoClient from '@/shared/api-client'
import type { AuthResponse } from '@/shared/types/auth'

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>('/auth/login', { username, password })
  return data
}

export async function register(
  username: string,
  password: string,
  password2: string,
  email: string,
): Promise<AuthResponse> {
  const { data } = await djangoClient.post<AuthResponse>('/auth/register', {
    username,
    password,
    password2,
    email,
  })
  return data
}
```

- [ ] **Step 3: api-client refresh URL**

将：

```typescript
refreshRequest: (body) => axios.post("/api/ai/auth/refresh", body),
```

改为：

```typescript
refreshRequest: (body) => axios.post("/api/auth/refresh", body),
```

- [ ] **Step 4: interceptors 解包**

在 `api-auth-interceptors.ts` 成功分支：

```typescript
const resp = await refreshPromise
if (resp.data.status) {
  const access = resp.data.data.access_token
  deps.setToken(access)
  originalRequest.headers.Authorization = `Bearer ${access}`
  return deps.retryRequest(originalRequest)
}
```

TypeScript：`resp.data` 为 `AuthResponse`；需窄化 `status === true` 后访问 `data.access_token`。

- [ ] **Step 5: useAuthFlow**

```typescript
if (data.status) {
  auth.loginAccount(
    username.trim(),
    data.data.access_token,
    // refresh 仅 login/register 有；断言为 AuthTokenData
    (data.data as { refresh_token: string }).refresh_token,
  )
  // ...
}
```

更稳妥：

```typescript
if (data.status && "refresh_token" in data.data) {
  auth.loginAccount(username.trim(), data.data.access_token, data.data.refresh_token)
  // ...
}
```

- [ ] **Step 6: SSE refresh**

`frontend/src/modules/ai-assistant/api/sse.ts`：

- URL：`/api/auth/refresh`
- `setToken(refreshResp.data.data.access_token)`（注意 axios 响应多层：若当前是 `refreshResp.data.access_token`，改为信封）

核对现有代码：

```typescript
return axios.post('/api/ai/auth/refresh', { refresh_token: refreshToken })
// ...
setToken(refreshResp.data.access_token)
```

改为：

```typescript
return axios.post('/api/auth/refresh', { refresh_token: refreshToken })
// ...
setToken(refreshResp.data.data.access_token)
```

（若 Envelope 已把 body 变成 `{status, data}`，则 `refreshResp.data` 是整包，`refreshResp.data.data.access_token` 才是 token。）

- [ ] **Step 7: 更新前端单测 mock**

`useAuthFlow.spec.ts`：成功 mock 改为：

```typescript
{ status: true, data: { access_token: 'a1', refresh_token: 'r1' } }
```

`apiAuthInterceptors.spec.ts`：

```typescript
data: {
  status: true,
  data: { access_token: 'new-access', token_type: 'bearer' },
}
```

并发用例的 resolve 类型同步改成信封。

- [ ] **Step 8: 跑前端登录单测**

```bash
cd frontend && node tests/run.mjs login/p0
```

（若项目用 vitest/其他入口，以 `frontend/tests/README.md` 为准；当前仓库为 `npm run test:ui` / `tests/run.mjs`。）

Expected: P0 登录相关 PASS。

- [ ] **Step 9: Commit（可选）**

```bash
git add frontend/src/shared frontend/src/views/composables/useAuthFlow.ts frontend/src/modules/ai-assistant/api/sse.ts frontend/tests/login
git commit -m "$(cat <<'EOF'
feat(frontend): consume /api/auth envelope for login flow

EOF
)"
```

---

### Task 6: 删除 ai_assistant 旧 auth + 验证旧路径 404

**Files:**
- Delete: `apps/ai_assistant/views/auth_views.py`
- Modify: `apps/ai_assistant/views/__init__.py`
- Modify: `apps/ai_assistant/urls.py`
- Test: 手工或 pytest 断言旧 URL 404

**Interfaces:**
- Consumes: Task 2–4 已提供的 `/api/auth/*`
- Produces: `ai_assistant` 不再导出/路由平台登录

- [ ] **Step 1: 从 urls 与 __init__ 移除 auth**

`apps/ai_assistant/urls.py`：删除 `login/register/refresh_token/logout/me` 的 import 与五条 `path("auth/...")`。

`apps/ai_assistant/views/__init__.py`：删除 `from .auth_views import ...` 及 `__all__` 中对应名字。

- [ ] **Step 2: 删除 `auth_views.py`**

确认无其它文件 `import auth_views` 后删除该文件。

- [ ] **Step 3: 验证旧路径 404、新路径 200**

```bash
# 需后端运行中
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/api/ai/auth/login -H "Content-Type: application/json" -d "{\"username\":\"a\",\"password\":\"b\"}"
# Expected: 404

curl -s -X POST http://127.0.0.1:8000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
# Expected: 200 + {"status":true,"data":{...}}
```

- [ ] **Step 4: 再跑全量 Auth API**

```bash
pytest tests/auth/test_login.py tests/auth/test_register.py tests/auth/test_refresh.py tests/auth/test_logout.py tests/auth/test_me.py -v --tb=short
```

Expected: PASS。

- [ ] **Step 5: Commit（可选）**

```bash
git add apps/ai_assistant
git commit -m "$(cat <<'EOF'
refactor(ai_assistant): remove legacy platform auth endpoints

EOF
)"
```

---

### Task 7: E2E / helpers URL 更新 + 冒烟

**Files:**
- Modify: `tests/e2e/helpers.py`（`/api/ai/auth/me` → `/api/auth/me`）
- Modify: `tests/auth/e2e/test_login_flow.py`（route `**/api/auth/login`）
- Modify: 其它 e2e 中硬编码旧 auth URL 的文件（用 grep 扫一遍）

**Interfaces:**
- Consumes: 前端已指向新 API
- Produces: E2E 拦截与 me 探测使用新路径

- [ ] **Step 1: grep 残留旧路径**

```bash
rg "/api/ai/auth" tests frontend -g '!**/dist/**'
```

Expected: 无业务残留（文档可保留历史说明）。

- [ ] **Step 2: 改 helpers / e2e**

`tests/e2e/helpers.py` 中 `fetch('/api/ai/auth/me'` → `fetch('/api/auth/me'`。

`tests/auth/e2e/test_login_flow.py`：

```python
page.route("**/api/auth/login", abort_login)
# ...
page.unroute("**/api/auth/login")
```

- [ ] **Step 3: 冒烟 E2E（需前后端 + Chromium）**

```bash
pytest tests/auth/e2e/test_login_flow.py -v --tb=short
```

Expected: 关键登录/失败提示用例 PASS。

- [ ] **Step 4: 更新 tests/auth/README.md 端点表**

将文档中 `/api/ai/auth` 改为 `/api/auth`，并注明信封格式。

- [ ] **Step 5: Commit（可选）**

```bash
git add tests/e2e tests/auth
git commit -m "$(cat <<'EOF'
test(auth): point E2E and helpers at /api/auth

EOF
)"
```

---

### Task 8: 验收清单（对照 Spec §9）

- [ ] **Step 1: 逐条验收**

| # | 标准 | 验证命令/方式 |
|---|------|----------------|
| 1 | 仅 `/api/auth/*`；旧路径 404 | curl 两条 |
| 2 | 信封格式 | 登录响应肉眼/Schema |
| 3 | Vue 登录/注册/切换/refresh | 浏览器手测 + E2E |
| 4 | Auth API 测试通过 | `pytest tests/auth/test_*.py` |
| 5 | Swagger 可见 | 打开 `/api/swagger/` 搜 auth |
| 6 | ai_assistant 无登录实现 | `rg auth_views apps/ai_assistant` 无结果 |

- [ ] **Step 2: 最终回归**

```bash
pytest tests/auth/test_login.py tests/auth/test_register.py tests/auth/test_refresh.py tests/auth/test_logout.py tests/auth/test_me.py -v --tb=short
cd frontend && node tests/run.mjs login/p0
```

Expected: 全绿（允许原有 skip/xfail）。

---

## Spec Coverage Self-Review

| Spec 项 | Task |
|---------|------|
| 独立 `apps.accounts` | Task 1 |
| `/api/auth/*` 五端点 | Task 2–4 |
| 信封响应 | Task 2（renderer + schemas）+ Task 5 |
| logout `retry: true` | Task 2 renderer + Task 4 LogoutView |
| 删除 ai 旧 auth | Task 6 |
| 前端路径/解包 | Task 5 |
| 测试/E2E | Task 2–4、7 |
| 验收 | Task 8 |
| Non-goals（自定义 User 等） | 未列入任务 |

无 TBD/TODO 占位；类型名在前后 Task 一致（`AuthResponse` / `data.access_token`）。
