## 1. CSRF 保护

- [x] 1.1 非 DRF 裸视图豁免审计（`temps/csrf_audit.py` 用 Django URL resolver 枚举全部回调的 `csrf_exempt` 属性）：URL 回调 **exempt=249 / enforced=205**；205 中约 **179 条是 `/admin/*`**（Django Admin，本就应受保护），非 admin 仅 **24 条**：`config.urls.<lambda>` · `api/docs` · `api/docs.html`（均 GET-only）· 19 个 element_locator / workflow / report_generator / evaluator 裸函数视图 · 2 个 `django.views.static.serve`。**结论：加中间件不会回归任何 API 路径** —— 无令牌请求在 `JWTAuthenticationMiddleware` 即 401（早于 CSRF），有效 JWT 请求由 1.2 的豁免标记放行。反证：`apps/evaluator/views.py:423 kb_self_test` 是 **POST 却未加 `@csrf_exempt`**，若不做定向豁免，该端点会对所有调用方立刻 403 —— 这正是选「中间件 + JWT 豁免」而非「逐视图补装饰器」的实证理由
- [x] 1.2 `gateway/middleware.py`：`JWTAuthenticationMiddleware` 校验通过分支新增 `request._dont_enforce_csrf_checks = True`，附注释说明依据（浏览器无法跨站携带自定义 `Authorization` 头 ⇒ JWT 请求不构成 CSRF 场景）
- [x] 1.3 `config/settings.py` MIDDLEWARE：在 `gateway.middleware.JWTAuthenticationMiddleware` **之后**插入 `django.middleware.csrf.CsrfViewMiddleware`（附注释说明顺序依赖），保证 JWT 请求先打豁免标记、后台 session 面正常受保护

## 2. 生产加固开关

- [x] 2.1 `config/settings.py` 新增安全加固块（全部 `os.environ` 驱动、默认不改变现状）：`SECURE_HSTS_SECONDS`（默认 `0` = 关）· `SECURE_HSTS_INCLUDE_SUBDOMAINS` · `SECURE_HSTS_PRELOAD`（默认 False）· `SECURE_SSL_REDIRECT`（默认 False）· `SECURE_PROXY_SSL_HEADER`（默认不启用，`SECURE_PROXY_SSL_HEADER=True` 时置 `("HTTP_X_FORWARDED_PROTO", "https")`）· `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE`（默认 `False if DEBUG else True`）
- [x] 2.2 `.env.example` 新增该组键（全部注释形式 + 说明）：含「确认全站 HTTPS 后再设 HSTS」「反代已终止 TLS 时**不要**开 `SECURE_SSL_REDIRECT`（会 301 循环）」「Cookie 安全标志生产默认已 True」
- [x] 2.3 `ARCH-00` §七「关键开关」新增 4 行（HSTS / SSL_REDIRECT / PROXY_SSL_HEADER / Cookie 标志）并补一段 CSRF 说明（中间件顺序与 JWT 豁免依据）

## 3. 验证

- [x] 3.1 本地档位：`python manage.py check` → **System check identified no issues (0 silenced)**
- [x] 3.2 `--deploy` 两档位对照：**本地**（DEBUG=True）残留 `W004 / W008 / W012 / W016 / W018`（本地开发预期；`W003` 已消失 —— 中间件到位），**生产档位**（DEBUG=False + 长 SECRET_KEY + HSTS 3 件套 + SSL 跳转 + 代理头 + 两 Cookie 标志全开）→ **`security.W*` 告警 0 条**（剩余 155 条是 drf-spectacular 的 `W001/W002`，源自 schema 元数据缺失，属 `complete-openapi-schema` 单，与本变更无关）
- [x] 3.3 新增 `tests/graybox/unit/test_csrf_protection.py`（6 例，**用 `Client(enforce_csrf_checks=True)`** —— Django 测试客户端默认豁免 CSRF，不显式打开就无法验证保护是否生效）→ **6 passed**：① 有效 JWT 的 `POST /api/reports/` → **200**（强制 CSRF 下仍放行，证明豁免生效）② 无令牌 POST → 401（JWT 先于 CSRF）③ 非法令牌 POST → 401（不产生 403）④ `/admin/login/` 缺 CSRF token 的 POST → **403**（保护生效）⑤ 带 `csrfmiddlewaretoken` → 非 403 ⑥ OPTIONS 预检 → 非 403
- [x] 3.4 跨域预检回归：见 3.3 第 ⑥ 例（`OPTIONS` + `Origin` + `Access-Control-Request-Method` 未被 CSRF 拦）
- [x] 3.5 `python -m pytest -m "unit or integration"` → **1 failed, 78 passed, 46 deselected**（78 = 上轮 72 + 本轮 6；唯一失败仍是既有 `test_case_manager_ids::test_next_case_id_increments_same_day`，与本变更无关）
- [x] 3.6 `python -m ruff check gateway config`：**All checks passed**；新增/改动文件均通过 `ruff format --check`；`python tools/gen_arch_stats.py --check-boundaries` → **零违规**
- [x] 3.7 `openspec validate harden-d0-security-config --strict` → **Change is valid**

## 4. 遗留说明（本单未动，避免夹带）

- 仓库既有 ruff 债（本轮扫描发现，均非本变更引入，未修）：`tests/graybox/unit/test_task_progress_persist.py` 的 `I001`（import 排序）；`config/settings.py` · `tests/graybox/unit/test_case_manager_projects.py` · `test_device_detector.py` · `test_example_unit.py` 的 `ruff format` 待格式化。其中 `config/settings.py` 的只是既有 JAZZMIN `icons` 缩进行，属 `cleanup-d0-consistency` 单。
- `README` / 部署文档未描述新增的 6 个环境变量（`.env.example` 与 ARCH-00 §七 已覆盖；如需要独立部署手册属另单）。
