## Context

动机见 `proposal.md - Why`；本节只列方案所需的现状与被实测确认的约束：

- **文档面**：`config/urls.py:15-16` 注册 `/api/docs`（JSON）与 `/api/docs.html`（HTML），实现为 `config/api_docs.py`（606 行手写 `ENDPOINTS` 快照）；`/api/schema/`、`/api/swagger/` 由 drf-spectacular 提供。
- **schema 现状**：实测 127 条路径 / 180 个 operation；`manage.py spectacular --validate` = **0 errors / 2 warnings**（`elements_*_batch_move_create` 因尾斜杠变体产生 operationId 冲突）。
- **中文说明覆盖**：180 个 operation 中 7 条既无 description 也无 summary —— `auth_login`、`auth_logout`、`auth_me`、`auth_refresh`、`auth_register`、`elements_files_batch_delete`、`elements_move`；schema 顶层无 `tags` 说明（Swagger 分组仅显示英文 tag 名）。
- **Swagger 资产**：项目自定主题模板 `templates/drf_spectacular/swagger_ui.html` 用 `{{ swagger_ui_css }}` / `{{ swagger_ui_bundle }}` / `{{ swagger_ui_standalone }}` 引用 `https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest/*`，并在 `<head>` 外链 Google Fonts；实测这两类外网域名在本机均不可达。
- **静态资产服务**：`STATIC_ROOT = BASE_DIR/staticfiles`（当前目录不存在）、`STATICFILES_DIRS = [BASE_DIR/static]`（仅 `.gitkeep`）；`config/urls.py:38` 用 `static(STATIC_URL, document_root=STATIC_ROOT)`，实测 `/static/admin/css/base.css` → **404**（全仓无 `collectstatic` 调用、无 whitenoise）。
- **依赖**：`drf-spectacular 0.30.0` 已安装，**无** `drf-spectacular-sidecar`；`requirements.txt:7` 为 `drf-spectacular>=0.28`。pip 源可达（实测解析到 `drf_spectacular_sidecar-2026.9.1-py3-none-any.whl`）。
- **引用面**：`gateway/middleware.py:34`（公开白名单）· `tools/seed_api_endpoints.py:60-61`（平台 API 目录种子）· `tests/graybox/unit/test_ai_tool_gateway_auth.py:68` · `tests/graybox/unit/test_api_docs_consistency.py`（整个文件）· `dev_docs/03-设计与架构/{ARCH-00-平台总体架构.md:303, 技术栈参考.md:85}`。
- `tools/gen_arch_stats.py` 的端点统计只扫 `apps/*/urls.py`（`:71-78`），故删除 `config/urls.py` 的两条路由不改变 ARCH_STATS 数字。

## Goals / Non-Goals

**Goals:**

- 把公开文档面收敛为 schema 驱动的两个端点，并彻底移除手写副本及其看守测试。
- 让 `/api/swagger/` 在无外网环境下真正渲染（不依赖 CDN 与外部字体）。
- 补齐删除手写文档后会丢失的中文说明（7 个 operation + 分组说明）。
- 把「公开文档面可达、页面无外链、schema 零 error」固化为自动化看守。

**Non-Goals:**

- 不改任何业务端点的路径、请求/响应契约、鉴权与信封。
- 不重命名既有 tag、不重组文档分组层级。
- 不引入新的文档工具或第二套 schema 渲染器（Redoc 等）。
- 不做部署形态改造（不引入 nginx / whitenoise / Docker），也不引入自动 `collectstatic` 流程。
- 不修 `/api/schema/` 的 2 条 operationId warning（登记为范围外，见 proposal）。

## Decisions

**D1 删除两个 URL，而不是保留 302 跳转。**
用户裁定。备选「`/api/docs` → `/api/schema/`、`/api/docs.html` → `/api/swagger/` 跳转」被否：那会继续维持两套 URL 面，且 `/api/docs`（JSON 语义）跳到 HTML 页面本身语义不符。删除即「恢复到真实行为」——两个手写端点自首个提交起就未正确渲染过。

**D2 离线资产用 `drf-spectacular-sidecar`，而不是手工把 swagger-ui-dist 拷进 `static/`。**
`SWAGGER_UI_DIST = "SIDECAR"`（配合 sidecar 包）让资产路径与版本由包管理，页面引用变为同源 `/static/drf_spectacular_sidecar/...`；pip 源实测可解析到 2026.9.1。
备选一：手工拷 minified 第三方资产进仓库 —— 需自行管理升级，且把外部构建产物纳入本仓 diff。
备选二：换 Redoc —— 仍需同等离线资产，且丢失现有主题。

**D3 静态资产改为 finders 口径（D2 生效的前提）。**
现状 `static(STATIC_URL, document_root=STATIC_ROOT)` 在 `DEBUG=True` 下只会去空的 `staticfiles/` 找文件，所以连 admin CSS 都是 404；offline 资产同样取不到。改为 finders 口径（`staticfiles_urlpatterns()` 或等价的 `static(STATIC_URL)`，仍限 DEBUG），使 app 静态（admin / jazzmin / sidecar）与本项目 `static/` 在开发启动方式下可取；生产仍由部署方 `collectstatic`。
副作用（正向，需登记）：admin/jazzmin 样式从 404 变为可用，属本单必要改动的连带修复，不作为独立需求扩展。

**D4 中文说明补齐，且只用官方标注手段。**
7 条缺失 operation 用 docstring 或 `@extend_schema(summary=...)` 补齐；分组说明用 `SPECTACULAR_SETTINGS["TAGS"]` 写中文说明（对应原手写文档的 module desc）。这两项直接兑现 spec 的「中文说明完整」需求；不新增自维护的说明文件。

**D5 看守迁移而非净删除。**
删 `tests/graybox/unit/test_api_docs_consistency.py`（其前提是手写文档与路由一致）；新增 `tests/graybox/unit/test_api_docs_surface.py`（名称待实施时定），覆盖 spec 的四条场景：老路径不再返回文档、两个保留端点公开可达、schema 内 operation 说明非空、`/api/swagger/` 页面无第三方外链且引用资产同源 200。`test_ai_tool_gateway_auth.py:68` 的 `/api/docs` 改为 `/api/schema/`，保持「公开路径不受 JWT 拦截」的回归对照。

**D6 公开白名单同步收敛。**
`gateway/middleware.py` 的 `PUBLIC_PREFIXES` 删除 `/api/docs`，保留 `/api/schema/` 与 `/api/swagger/`，并保留「有意公开」注释。`tests/arch/test_channels.py` 的业务前缀黑名单不含 `/api/docs`，无需改动（已核对 `:43-53`）。

**D7 平台 API 目录种子同步。**
`tools/seed_api_endpoints.py` 的 `根路径 & 文档` 分组删除两条失效条目，改收录 `/api/schema/` 与 `/api/swagger/`——该分组语义是「根路径与文档」，只删不补会让该分组缺失文档面。

## 模块防火墙自检

逐条确认（规则见 `AGENTS.md` 与应用规范）：

- **跨 App import**：本单不新增任何跨 App import（改动集中在 `config/`、`gateway/`、`templates/`、`tests/`、`tools/`、`dev_docs/`）。
- **写操作收敛**：无任何 INSERT/UPDATE/DELETE 新增或修改；不触碰任何 App 的 `api.py`。
- **前端**：无前端改动，不涉及前端直连数据库或绕过 `/api` 出口。
- **引擎边界**：不涉及 `engines/`、`device_pool` 与 airtest/uiautomator2。
- **通信通道**：只减少一个公开 HTTP 前缀，不新增通道；WS 生产点保持 0。

## Risks / Trade-offs

- [破坏性：外部书签/脚本访问 `/api/docs` 会 401/404] → 用户已裁定删除；在 proposal 与本文件登记，不提供跳转。
- [静态服务口径变更影响 admin/jazzmin 既有表现] → 变更方向是从 404 到可用，且仍在 DEBUG 内生效；实施时以 `/static/admin/css/base.css` 200 作为验证锚点。
- [sidecar 会换掉 Swagger UI 版本（由 CDN `@latest` 变为包内固定版本）] → 这是期望行为（可复现）；测试只断言「无第三方外链 + 同源 200」，不锁具体版本号。
- [目标环境离线时 `pip install` 不可用] → 实测 pip 源可达；若目标机离线，需预置 wheel（实施注意项，不改变方案）。
- [`/api/schema/` 仍有 2 条 operationId warning] → 范围外登记；不影响生成与渲染。
- [删除漂移看守后短期失去「文档 ↔ 路由」检测] → 漂移源（手写副本）本身被删除，schema 自动生成不会漂移；新用例补上可达性与离线约束。

## Migration Plan

1. 依赖与配置：`requirements.txt` 增 `drf-spectacular-sidecar` → 安装 → `SPECTACULAR_SETTINGS` 设 `SWAGGER_UI_DIST = "SIDECAR"`（含 favicon 同类项）→ 主题模板去掉 Google Fonts 外链。
2. 静态服务：`config/urls.py` 的 DEBUG 静态服务改 finders 口径；验证 `/static/admin/css/base.css` 与 sidecar 资产均 200。
3. 文档面：删 `config/api_docs.py` 与两条路由 → 同步 `gateway/middleware.py`、`tools/seed_api_endpoints.py`、dev_docs 两处。
4. 看守：删旧一致性用例、加新文档面用例、改公开路径回归对照。
5. 人工核验：断网（或 hosts 阻断 CDN）状态下打开 `http://localhost:8766/api/swagger/`，确认接口列表渲染、无外部请求。
6. 回滚：`git revert` 本单提交即可（无数据迁移、无 DB 变更）；若仅离线资产出问题，可单独把 `SWAGGER_UI_DIST` 回退为 CDN。

## Open Questions

- 生产/CI 何时、由谁执行 `collectstatic`（本单只保证开发启动方式下资产可取，不含部署自动化）——可在后续部署类变更中决定，不影响本单方案与任务拆分。
