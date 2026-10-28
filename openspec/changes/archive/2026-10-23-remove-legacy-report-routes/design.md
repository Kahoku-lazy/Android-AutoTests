# 设计：删除遗留报告详情与用例分解路由

## 背景

`frontend/src/modules/report-generator/routes.ts` 注册了三条路由：`/reports`（列表）、`/reports/cases/:resultType`、`/reports/:runId`。后两条在卸掉执行引擎后就没有真实数据源：

- `ReportDetail.vue`（793 行）调 `getRunReport()` → `GET /api/reports/run/{id}/`，后端 `RunReportAPIView` 恒 `raise NotFound("run not found")`；
- `CaseBreakdown.vue`（632 行）调 `getCaseBreakdown()` → `GET /api/reports/cases/`，后端恒返回 `groups: []`；
- 列表页 `openReport` / `openCaseBreakdown` 已在 2026-09-16 删除，`constants.ts` 的 `ROUTES.reportDetail` / `ROUTES.caseBreakdown` 零调用；
- 两个文件仍在 `utils/frontend-whitelist.json` 里占着「大文件待拆分」豁免；
- `openspec/openapi.yaml` 仍把两个空壳端点登记为有效契约。

## 决策

### D1：直接删路由，不加兼容重定向

重定向会把一个没有数据源的页面伪造成「还能用」，且需要再维护一张映射表。路由删掉后由既有 catch-all 落到 404 页，语义正确：这两个页面从来不是 PRD 承诺的入口。

### D2：连带删页面组件、api helper 与 `ROUTES` 常量

模块 AGENTS 禁止零消费声明。只删路由会留下三个死文件与两个死导出，下一次有人「复用」它们就会复活死接口。因此同一次删除：`ReportDetail.vue`、`CaseBreakdown.vue`、`getRunReport()`、`getCaseBreakdown()`、`ROUTES`。

### D3：后端两个空壳端点一并删除

`CaseBreakdownAPIView` 与 `RunReportAPIView` 唯一调用方就是上面两个页面。删后 `/api/reports/` 只留三个端点：列表、`{filename}/content/`、`{filename}` 下载。列表与下载逻辑不变，`build_report_list` 不动。

### D4：白名单与文档同步

- `utils/frontend-whitelist.json` 删两条目（文件已不存在，留着会变成永不消费的豁免）。
- `ARCH-平台架构设计.md` 的路由清单、两个模块的 `AGENTS.md` 契约行同步。
- 三份 spec 的 delta 收回对这两个页面的陈述。

### D5：不动数据与任务域

不新增/修改数据表、不迁移、不改 `/api/tasks/*`；任务详情仍由 `task-list` 提供，列表行点击仍进 `/tasks/:id`。

## 风险

- **BREAKING**：外部书签与历史分享链接打到 `/reports/143`、`/reports/cases/pass` 会 404。PRD 未承诺这两个地址，且真正的任务详情一直是 `/tasks/143`。
- `openspec/openapi.yaml` 必须同步重新生成，否则 `openapi-schema` 门禁会报「接口改了但基线没更新」。
- `tests/graybox/integration/test_report_envelope.py` 有一条 cases 参数校验用例，删端点后必须一并删除，否则变成红灯。
- `report-generator/AGENTS.md` 与 `backend/apps/report_generator/AGENTS.md` 若不同步，会让下一位接手者按旧契约实现。

## 验证

- `python run.py check`（含 `openapi-schema`、`openapi-coverage`、前端体积与 prettier）。
- `python -m pytest tests/graybox/integration/test_report_envelope.py -q`。
- 手工：`/reports/143` 与 `/reports/cases/pass` 落到 404 页；`/reports` 列表点行仍进 `/tasks/143`；报告列表与文件下载正常。
- `openspec validate remove-legacy-report-routes --strict`。
