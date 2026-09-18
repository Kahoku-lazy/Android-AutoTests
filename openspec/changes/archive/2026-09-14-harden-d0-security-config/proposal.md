## Why

D0 复检实测：`python manage.py check --deploy` 报出 5 条安全告警，其中 W003 是**功能性缺口**（不是加固建议）：

```
security.W003  'django.middleware.csrf.CsrfViewMiddleware' is not in your MIDDLEWARE
security.W004  SECURE_HSTS_SECONDS 未设
security.W008  SECURE_SSL_REDIRECT 未设为 True
security.W012  SESSION_COOKIE_SECURE 未设为 True
security.W018  DEBUG=True（本地环境预期）
```

关键背景（决定修法）：

1. **管理后台是 session + 表单**：`config/urls.py:20` 挂 `admin/`，`/admin/` 在 `PUBLIC_PREFIXES`（`gateway/middleware.py:26`）属免 JWT 面，MIDDLEWARE 里有 `SessionMiddleware`/`AuthenticationMiddleware`/`XFrameOptionsMiddleware` 却**没有 CsrfViewMiddleware** → 后台登录与表单提交无 CSRF 保护（`MIDDLEWARE` 现 10 项，见 `config/settings.py:101-113`）。
2. **不能简单加中间件了事**：平台 API 由 SPA 以 JWT 头访问，大量非 DRF 视图是手写函数视图并已用 `@csrf_exempt`（`apps/report_generator/views.py` ×6 · `apps/evaluator/views.py` ×10 · `apps/workflow/views.py` ×10 · `apps/element_locator/views.py` ×25 · `apps/ai_assistant/views/tool_gateway.py` ×3），DRF 的 `APIView` 本身即 csrf_exempt；但**是否还有未豁免的裸视图**未经枚举，贸然加中间件可能让 API 出现 403。
3. `JWTAuthenticationMiddleware`（`gateway/middleware.py:43-84`）是 `__call__` 风格中间件：校验通过后调用内层链 → 只要把 `CsrfViewMiddleware` 排在其**之后**，就能在有效 JWT 请求上做定向豁免（浏览器无法跨站携带自定义 `Authorization` 头，JWT 请求不构成 CSRF 风险），从而「只保护后台、不动 API」。
4. W004/W008/W012 目前**无任何开关**可配：`.env.example` 与 `config/settings.py` 中 `SECURE_` / `*_COOKIE_SECURE` / `SECURE_PROXY_SSL_HEADER` 零命中 → 生产只能靠改代码。

## What Changes

1. **补 CSRF 中间件 + JWT 定向豁免**：
   - `config/settings.py` MIDDLEWARE 增 `django.middleware.csrf.CsrfViewMiddleware`，位置在 `gateway.middleware.JWTAuthenticationMiddleware` **之后**；
   - `gateway/middleware.py` 在**有效 Bearer 令牌**分支置 `request._dont_enforce_csrf_checks = True`（附注释说明为何 JWT 请求不需 CSRF）；
   - 枚举全部非 DRF 的裸函数视图，确认「已 `@csrf_exempt`」或「必须受 CSRF 保护」，形成结论写进本变更 tasks 验证项。
2. **生产加固开关（全部环境变量驱动，默认不改变本地行为）**：
   - `SECURE_HSTS_SECONDS`（默认 `0` = 关）/ `SECURE_SSL_REDIRECT`（默认 `False`）/ `SECURE_PROXY_SSL_HEADER`（默认不启用，反代场景显式打开）；
   - `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE`：默认 `not DEBUG`（生产自动 True，本地不受影响）。
3. `.env.example` 增上述键与说明（含「反代终止 TLS 时不要再开 SECURE_SSL_REDIRECT」等注意事项）。
4. `ARCH-00` §七「关键开关」同步新增这几项。
5. **BREAKING（部署侧）**：默认值已选「不改变现状」（HSTS/SSL 跳转默认关），**不会**自动中断现有 HTTP 部署；但生产若启用 `SECURE_SSL_REDIRECT=True` 而本身是明文访问，会立刻 301 循环——`.env.example` 与 ARCH-00 必须写清。CSRF 中间件对纯 JWT 客户端无影响。

## 关联文档

- 取证：`python manage.py check --deploy` 输出（W003/W004/W008/W012/W018）
- 代码：`config/settings.py` MIDDLEWARE + 安全项 · `gateway/middleware.py` · `config/urls.py`（admin 挂载）
- 前序：`openspec/changes/archive/2026-09-14-fix-d0-fail-open-defaults/`（D0-5/6 fail-open 默认值，同一治理线）
- 范围外登记：API schema 告警（155 条）· `api_docs.py` 手写真相源 · D0 一致性清理（注释/缩进/空转代码）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；`openspec/specs/` 无配置/安全类能力，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **修改**：`config/settings.py`（MIDDLEWARE +1 项、新增 5 个安全配置项）· `gateway/middleware.py`（有效 JWT 请求置豁免标记）· `.env.example` · `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §七
- **新增**：CSRF 行为用例（admin 表单 + API 两组）
- **不影响**：前端 SPA（JWT 头请求豁免 CSRF）、API 契约、DB、`apps/` 业务逻辑
- **测试范围**：`python manage.py check`（本地零 issues）· `python manage.py check --deploy`（生产档位）· 新用例 · `pytest -m "unit or integration"` · `ruff` · `openspec validate --strict`
