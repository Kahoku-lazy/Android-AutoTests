## Context

- 证据与背景见 proposal「Why」；两条关键实测结论：
  1. `MIDDLEWARE` 无 `CsrfViewMiddleware`（`config/settings.py:101-113`，10 项），而 admin 是 session 表单面；
  2. `JWTAuthenticationMiddleware` 为 `__call__` 风格（`gateway/middleware.py:53-84`），排在它之后的中间件只在「已通过校验」的请求上运行——这是实现「JWT 请求豁免 CSRF」的着力点。
- `SECURE_` 系列当前零配置（grep 全仓仅出现在 Django 文档字符串之外无命中）。
- 用户裁定与本单的关系：本单只做 D0 内的 CSRF 与生产加固开关，不动公开前缀策略（工具网关令牌另单）。

## Goals / Non-Goals

**Goals:**

- 让 `/admin/` 这类 session 面重新受 CSRF 保护，同时**不改变** JWT API 的调用方式；
- 让 `check --deploy` 的 W004/W008/W012 在**生产环境通过环境变量清零**，且默认值不改变现有本地/HTTP 部署行为。

**Non-Goals:**

- 不改公开前缀白名单（工具网关令牌 = 单 `secure-ai-tool-gateway`）；
- 不引入 TLS 终止、反代配置或证书（属部署层）；
- 不修 drf-spectacular 的 155 条 schema 告警（另单）；
- 不把 `DEBUG` 默认值改成 False（现在已是 False，见 `settings.py:40`）。

## Decisions

**D1 采用「CsrfViewMiddleware + JWT 定向豁免」，而不是逐个视图加 `@csrf_exempt`。**
理由：逐个豁免需要枚举所有裸视图且以后新增视图会漏；定向豁免把规则收敛到一处（有效 JWT ⇒ 不存在浏览器自动附带凭据的 CSRF 场景），同时后台自动获得保护。
备选：全局加中间件 + 全量审计裸视图 —— 工作量大且回归面广，且对新视图无保护性。

**D2 豁免标记写在 `JWTAuthenticationMiddleware` 的成功分支（`request._dont_enforce_csrf_checks = True`），并加注释。**
理由：该分支即「令牌已验证」的唯一位置；Django 官方即以此属性做请求级豁免（`CsrfViewMiddleware.process_view` 读取）。

**D3 `CsrfViewMiddleware` 排在 `JWTAuthenticationMiddleware` 之后。**
理由：`__call__` 风格中间件的「前置代码」按外层到内层执行，排在其后可保证标记先于 CSRF 检查写入；同时 `corsheaders` 仍在其外层，OPTIONS 预检不受影响。

**D4 加固开关全部环境变量驱动，默认值 = 不改变现状。**
`SECURE_HSTS_SECONDS=0`、`SECURE_SSL_REDIRECT=False`、`SECURE_PROXY_SSL_HEADER` 默认不启用；仅 `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` 默认 `not DEBUG`（生产为 True，且当前无生产登录 cookie 依赖）。
理由：避免「修告警修出 301 循环」；把「是否已上 TLS」这个只有部署方知道的判断交给环境变量。

**D5 `.env.example` 与 ARCH-00 §七 必须写清「反代已终止 TLS 时不要再开 SECURE_SSL_REDIRECT」，并给出清零 `check --deploy` 的生产档位示例。**
理由：本次的可验证目标就是「生产档位下告警可控清零」，配置项必须有可复制的正确用法。

## Risks / Trade-offs

- [存在未豁免的裸函数视图，加 CSRF 后其 POST 变 403] → tasks 里强制「枚举全部非 DRF 视图并出具结论」，并在 `check --deploy` + `pytest -m "unit or integration"` 后再关单；枚举结果写进 tasks 验证记录。
- [`_dont_enforce_csrf_checks` 属私有属性，Django 版本升级可能改名] → 注释写明依赖点与版本（Django 4.2）；升级时由 `manage.py check` + 用例兜底。
- [运维照抄 `.env.example` 打开 `SECURE_SSL_REDIRECT` 导致 301 循环] → D5 的显式警示 + 该键在模板里默认注释掉。
- [HSTS 一旦开启且设置很长，回退困难] → 模板里给短值示例并注明「确认全站 HTTPS 后再加大」。
