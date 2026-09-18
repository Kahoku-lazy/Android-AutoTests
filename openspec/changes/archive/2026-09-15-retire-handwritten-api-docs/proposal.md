## Why

`/api/docs` 与 `/api/docs.html`（`config/api_docs.py` 手工渲染）实测已不可用：返回的 HTML 中 CSS 的 `{{` 未被还原（实测 71 处），JS 字符串内的单引号转义在 Python 三引号里丢失，抽取线上 `<script>` 跑 `node --check` 报 `SyntaxError: Unexpected identifier 'open'` —— 该页面自首个提交 `48d403ac`（2026-07-05）起就无样式、无内容，且是第三份 API 真相源（手写 29 条 vs `/api/schema` 实测 127 条路径），维护成本高于价值。前序归档单 `2026-09-14-fix-d0-config-drift` 的 D3 决策已裁定「暂时保留 + 加机检」，并把「改由 drf-spectacular schema 渲染」登记为依赖 `complete-openapi-schema` 的后续决策；后者已归档完成（实测 schema 0 errors / 2 warnings、457 条中文 description），本单兑现该决策并清账。

## What Changes

- **BREAKING**：删除 `/api/docs`（JSON）与 `/api/docs.html`（HTML）两个公开端点及其实现模块 `config/api_docs.py`，不保留跳转。
- 文档面收敛为两个既有端点：`/api/schema/`（OpenAPI 3.0）与 `/api/swagger/`（Swagger UI）；内容全部由 drf-spectacular 生成，中文说明来自视图 docstring / `@extend_schema`，不再有第二份手写副本。
- Swagger UI 资产改为**离线自托管**：实测本机 `cdn.jsdelivr.net` 与 `fonts.googleapis.com` 均不可达，现状是「跳到 Swagger 也是白页」；引入 `drf-spectacular-sidecar`（实测可解析到 2026.9.1）并按 `SWAGGER_UI_DIST = "SIDECAR"` 配置，同时移除主题模板中的 Google Fonts 外链。
- 同步清理引用面：`gateway/middleware.py` 的 `PUBLIC_PREFIXES`、`tools/seed_api_endpoints.py` 的平台 API 目录、`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` 与 `技术栈参考.md` 的文档面登记。
- 看守迁移：删除 `tests/graybox/unit/test_api_docs_consistency.py`（其「手写文档 ↔ 路由一致」的前提随文档消失），把「公开文档端点可达」断言迁到 `/api/schema/` 与 `/api/swagger/`。

## 关联文档

- `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` §1.5（API 实现与统一管理；网关图中的 `DOC["/api/schema · /api/swagger · /api/docs"]` 需同改）
- `dev_docs/03-设计与架构/技术栈参考.md` §2.3 文档行（第 85 行登记 `/api/docs · /api/schema · /api/swagger`）
- 前序单：`openspec/changes/archive/2026-09-14-fix-d0-config-drift/`（D3 决策与「改由 schema 渲染」登记）· `openspec/changes/archive/2026-09-14-complete-openapi-schema/`（schema 告警 155→0，本单前置条件）
- PRD：无对应条目（本单只收敛文档面与依赖，不改变业务需求）

## Capabilities

### New Capabilities

- `api-docs-surface`: 平台对外 API 文档面的契约 —— 由哪些 URL 提供、内容来源是什么、离线环境下必须可用。

### Modified Capabilities

（无）

## Impact

- **修改**：`config/urls.py`（删 2 条路由）· `config/settings.py`（`SPECTACULAR_SETTINGS` 增加 `SWAGGER_UI_DIST`，`INSTALLED_APPS` 视方案而定）· `templates/drf_spectacular/swagger_ui.html`（去外链字体）· `gateway/middleware.py` · `tools/seed_api_endpoints.py` · `dev_docs` 两处
- **删除**：`config/api_docs.py` · `tests/graybox/unit/test_api_docs_consistency.py`
- **修改测试**：`tests/graybox/unit/test_ai_tool_gateway_auth.py`（`/api/docs` → `/api/schema/`）
- **新增依赖**：`requirements.txt` 增 `drf-spectacular-sidecar`（离线资产）
- **不影响**：业务端点与响应契约、前端、DB、`apps/` 业务逻辑；`tools/gen_arch_stats.py` 的端点统计只扫 `apps/*/urls.py`，ARCH_STATS 数字不变
- **测试范围**：`manage.py check` · `pytest -m "unit or arch"` · `pytest tests/arch/test_channels.py` · `ruff` · `python tools/gen_arch_stats.py --check-boundaries` · 断网/无 CDN 环境下人工核验 `/api/swagger/` 渲染
