## 1. 离线资产依赖与配置

- [x] 1.1 `requirements.txt` 新增 `drf-spectacular-sidecar` 并安装 —— 验证：`python -m pip show drf-spectacular-sidecar` 有 Name/Version 输出，`python -c "import drf_spectacular_sidecar" ` 退出码 0 —— **实测**：要求 `>=2026.9.1`，安装得 2026.9.1（沙箱拒写临时目录导致常规 pip 失败，经用户授权以 full-access 重跑该命令后成功）
- [x] 1.2 `config/settings.py` 的 `SPECTACULAR_SETTINGS` 设 `SWAGGER_UI_DIST = "SIDECAR"`（favicon 同类项一并处理，去掉 CDN 默认）—— 验证：`python manage.py spectacular --file <临时文件>` 生成的 HTML 来源不再是 `cdn.jsdelivr.net`，且 `python manage.py check` 0 issues —— **实测**：另在 `INSTALLED_APPS` 注册 `drf_spectacular_sidecar`（sidecar 静态资产需 app registry 才能被 finders 找到）；`manage.py check` 0 issues
- [x] 1.3 `templates/drf_spectacular/swagger_ui.html` 移除 Google Fonts 的 `preconnect`/`stylesheet` 外链（保留既有 animal-island-ui 本地主题样式，字体回退系统字体）—— 验证：该模板内不再出现第三方域名 —— **实测**：模板 0 外链；渲染后页面第三方引用数 = 0

## 2. 静态资产服务（离线可用的前提）

- [x] 2.1 `config/urls.py` 的 DEBUG 静态服务由 `static(STATIC_URL, document_root=STATIC_ROOT)` 改为 finders 口径（`staticfiles_urlpatterns()` 或等价写法），仍限 DEBUG —— 验证：启动 backend 后 `/static/admin/css/base.css` 返回 200、`/static/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js` 返回 200（修复前实测均为 404，先留证据再改）—— **实测**：修复前两者 404（`staticfiles/` 不存在）；改后重启 backend 均为 **200**

## 3. 中文说明补齐（删除手写文档后不丢可读性）

- [x] 3.1 为实测缺失说明的 7 个 operation 补中文说明（`auth_login` / `auth_logout` / `auth_me` / `auth_refresh` / `auth_register` / `elements_files_batch_delete` / `elements_move`），用 docstring 或 `@extend_schema(summary=...)` —— 验证：解析 `/api/schema/`，180 个 operation 的 description 或 summary 全部非空 —— **实测**：改用与仓库既有风格一致的类/函数 docstring；180 operations 缺失数 **7 → 0**
- [x] 3.2 `SPECTACULAR_SETTINGS["TAGS"]` 补各分组中文说明（替代原手写文档的 module desc）—— 验证：`/api/schema/` 的每个 tag 带非空中文 description，Swagger 页分组显示中文 —— **实测**：10 个 tag（dashboard/devices/inspector/elements/cases/workflow/auth/ai/evaluator/schema）全部带中文说明，由新用例断言
- [x] 3.3 复核 spec「文档内容单一来源」—— 验证：`python manage.py spectacular --validate` 报告中 Errors 为 0（Warnings 允许保留并登记）—— **实测**：Errors 0 / Warnings 2（`elements_{api,web}_groups_batch_move_create` 尾斜杠 operationId 冲突，范围外既有项）

## 4. 删除手写文档面

- [x] 4.1 删除 `config/urls.py` 中 `api/docs` 与 `api/docs.html` 两条路由及 `.api_docs` import，删除 `config/api_docs.py` —— 验证：`python manage.py check` 0 issues；`python -c "from django.urls import resolve" ` 探测协议下 `/api/docs` 不再解析到文档视图 —— **实测**：`git rm config/api_docs.py`；`manage.py check` 0 issues；新用例断言 `resolve("/api/docs")` 抛 `Resolver404` 且无凭据请求返回 401
- [x] 4.2 `gateway/middleware.py` 的 `PUBLIC_PREFIXES` 移除 `/api/docs`，保留 `/api/schema/`、`/api/swagger/` 与「有意公开」注释 —— 验证：无凭据请求 `/api/schema/`、`/api/swagger/` 均 200；`pytest tests/arch/test_channels.py -v` 通过 —— **实测**：新用例断言两者 200；`pytest -m "unit or arch"` 中 arch 用例全通过
- [x] 4.3 `tools/seed_api_endpoints.py` 的「根路径 & 文档」分组删除两条失效条目，改收录 `/api/schema/`、`/api/swagger/` —— 验证：`ruff check tools/seed_api_endpoints.py` 通过，脚本内不再出现 `/api/docs` —— **实测**：ruff check/format 均通过，脚本内 0 命中
- [x] 4.4 同步 `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（§1.5 网关图的 `DOC[...]`）与 `dev_docs/03-设计与架构/技术栈参考.md`（文档行）—— 验证：在 `config/ gateway/ tools/ tests/ dev_docs/` 检索 `/api/docs` 命中为 0（`openspec/` 下的历史归档单不计）；`python tools/gen_arch_stats.py --check-md` 无新增漂移 —— **实测**：命中仅剩新用例里用于声明「已删除路径」的常量；`--check-md` 输出与变更前一致（ARCH-00 无 ARCH_STATS 自动区，仅提示初始化）

## 5. 看守迁移

- [x] 5.1 删除 `tests/graybox/unit/test_api_docs_consistency.py`，新增 `tests/graybox/unit/test_api_docs_surface.py`，覆盖 spec 四条需求：老路径不返回文档（401/404）、`/api/schema/`+`/api/swagger/` 无凭据 200、schema 全部 operation 说明非空、`/api/swagger/` 页面无第三方外链且引用资产同源 200 —— 验证：`python -m pytest tests/graybox/unit/test_api_docs_surface.py -v` 全通过 —— **实测**：6 passed。**实施偏差（据实登记）**：资产可取性用例改走 `staticfiles.views.serve`（finders → 文件）而非 HTTP GET —— pytest-django 会把 `DEBUG` 置 False，此时 URLconf 里的静态服务不注册；真实 HTTP 200 由 6.3 在运行中的服务上核验
- [x] 5.2 `tests/graybox/unit/test_ai_tool_gateway_auth.py` 的公开路径回归对照由 `/api/docs` 改为 `/api/schema/` —— 验证：`python -m pytest tests/graybox/unit/test_ai_tool_gateway_auth.py -v` 通过 —— **实测**：7 passed（含 `/api/schema/` 与 `/api/swagger/` 无凭据 200）

## 6. 验证与关单

- [x] 6.1 后端门禁 —— 验证：`python manage.py check` · `ruff check .` + `ruff format --check` · `python -m pytest -m "unit or arch"` 全部通过（若存在与本单无关的既有失败，须据实登记）—— **实测**：check 0 issues；ruff check/format 对本单 8 个文件通过；`pytest -m "unit or arch"` = **202 passed / 62 deselected / 11 errors**，11 个 error 全部是 pytest 与沙箱临时目录冲突的 `PermissionError`（`test_env_loader.py` `test_kb_files.py` 的 `tmp_path` fixture，环境所致、与本单无关；用工作区 basetemp 复跑同样报 `PermissionError`）
- [x] 6.2 架构红线 —— 验证：`python tools/gen_arch_stats.py --check-boundaries` 零违规 —— **实测**：✅ 零违规（日志 `logs/boundary-check.log`）
- [x] 6.3 断网人工核验 —— 验证：阻断 `cdn.jsdelivr.net` / `fonts.googleapis.com`（或使用离线网络）后打开 `http://localhost:8766/api/swagger/`，接口列表正常渲染、浏览器无失败的外部请求 —— **实测**：本机该两域名本就不通（真实离线条件）；重启 backend 后 `/api/swagger/` 200、页面第三方引用 0、4 个同源资产（css/bundle/standalone/favicon）全部 200；`/api/schema/` 200；`/api/docs` 与 `/api/docs.html` 均 401
- [x] 6.4 OpenSpec 校验与关单 —— 验证：`openspec validate retire-handwritten-api-docs --strict` 通过 —— **实测**：`Change 'retire-handwritten-api-docs' is valid`，exit 0
