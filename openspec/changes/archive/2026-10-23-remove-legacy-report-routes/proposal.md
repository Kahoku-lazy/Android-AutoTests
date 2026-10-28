## Why

`/reports/:runId` 与 `/reports/cases/:type` 是卸掉执行引擎后遗留的两个页面：`ReportDetail.vue` 读的 `GET /api/reports/run/{id}/` 恒 404，`CaseBreakdown.vue` 读的 `GET /api/reports/cases/` 恒返回空组。两页在 `routes.ts` 里仍能手输 URL 打开，在 OpenAPI 与三份 spec 里仍被当成有效契约，`ReportDetail.vue`（793 行）与 `CaseBreakdown.vue`（632 行）还占着前端大文件豁免名单，容易被误认为「报告详情」就是 `/reports/143`，而真正的任务详情在 `/tasks/143`。

## What Changes

- **BREAKING**：删除前端路由 `/reports/:runId`（`report-detail`）与 `/reports/cases/:resultType`（`case-breakdown`）；直接访问落到 404 页，不做重定向。
- 删除仅由这两个路由使用的页面组件 `ReportDetail.vue`、`CaseBreakdown.vue`。
- 删除零消费的 API 辅助 `getCaseBreakdown()` / `getRunReport()` 与 `constants.ts` 的 `ROUTES` 导出。
- 删除后端两个空壳端点 `/api/reports/cases/`、`/api/reports/run/{run_id}/`；报告 App 只保留列表、内容查看、文件下载三个端点。
- 同步 `openspec/openapi.yaml`、`report-ai-task-list` / `frontend-l2-page-region` / `frontend-l4-data-surface` 三份 spec、两个模块的 `AGENTS.md`、`ARCH-平台架构设计.md`、`utils/frontend-whitelist.json`。
- 不新增数据表、不迁移、不改列表与下载行为、不改变列表行点击进入 `/tasks/:id`。

## 关联文档

无（技术债清理：PRD 未定义这两个页面，删除后用户可见入口与跳转路径不变）。

## Capabilities

### New Capabilities

（无。本变更只收回既有能力里对两个已删页面/端点的陈述。）

### Modified Capabilities

- `report-ai-task-list`: 报告端点集合收为列表 / 内容 / 下载三个；工作台不再提供报告详情与用例分解路由。
- `frontend-l2-page-region`: 页面清单去掉两个已删页面，改用 `/reports` 与 `/tasks/{id}` 对齐页头与主题作用域的场景。
- `frontend-l4-data-surface`: 分页消费方清单去掉 `report-generator/ReportDetail`。

## Impact

- 前端：`frontend/src/modules/report-generator/{routes.ts,api.ts,constants.ts,ReportDetail.vue,CaseBreakdown.vue}`、`utils/frontend-whitelist.json`
- 后端：`backend/apps/report_generator/{urls.py,views.py}`、`openspec/openapi.yaml`
- 文档：`dev_docs/ARCH_PRD/ARCH-平台架构设计.md`、`frontend/src/modules/report-generator/AGENTS.md`、`backend/apps/report_generator/AGENTS.md`
- 测试与门禁：`tests/graybox/integration/test_report_envelope.py` 删除 cases 用例；`python run.py check`、`openspec validate`
