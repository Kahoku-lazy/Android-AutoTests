## 1. 前端路由与页面

- [x] 1.1 `frontend/src/modules/report-generator/routes.ts`：只保留 `/reports`（name `report-generator`），删除 `/reports/cases/:resultType` 与 `/reports/:runId`。验证：该文件只剩一条路由，`rg "report-detail|case-breakdown" frontend/src` 0 命中。
- [x] 1.2 删除 `frontend/src/modules/report-generator/ReportDetail.vue` 与 `CaseBreakdown.vue`。验证：两文件不存在，`rg "ReportDetail|CaseBreakdown" frontend/src` 只剩注释级 0 命中。
- [x] 1.3 `api.ts` 删 `getCaseBreakdown` / `getRunReport`；`constants.ts` 删 `ROUTES` 导出。验证：`rg "getCaseBreakdown|getRunReport|ROUTES\.reportDetail" frontend/src` 0 命中，`vue-tsc` 门禁 PASS。

## 2. 后端端点

- [x] 2.1 `backend/apps/report_generator/views.py`：删除 `CaseBreakdownAPIView`、`RunReportAPIView` 及随之无用的 import（`ValidationError`）。验证：`ruff-lint` 门禁 PASS，无 F401。
- [x] 2.2 `urls.py`：删除 `cases/` 与 `run/<str:run_id>/` 两条 path，只留 `""`、`{filename}/content/`、`{filename}/`。验证：`test_removed_report_endpoints_return_404` 通过（两条路径均 404）。
- [x] 2.3 `backend/apps/report_generator/AGENTS.md` 契约行由「5 端点」改为 3 端点，删掉「`/reports/run|cases` 仍为空壳」的描述。验证：该文件只把 3 个端点写作有效端点。

## 3. 契约基线

- [x] 3.1 重新生成 `openspec/openapi.yaml`：`python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn`。验证：基线只剩 `/api/reports/`、`/api/reports/{filename}/`、`/api/reports/{filename}/content/` 三条。
- [x] 3.2 `python utils/check_openapi_coverage.py` 通过（门禁 `openapi-coverage` PASS）。

## 4. 测试

- [x] 4.1 `tests/graybox/integration/test_report_envelope.py`：删除 cases 参数校验用例，改为 `test_removed_report_endpoints_return_404` 断言两条已删路径 404。验证：`python -m pytest -c tests/pytest.ini tests/graybox/integration/test_report_envelope.py -q` → 7 passed。

## 5. 文档与豁免

- [x] 5.1 `utils/frontend-whitelist.json` 删除 `ReportDetail.vue`（793 行）与 `CaseBreakdown.vue`（632 行）两条目。验证：`vue-file-size` 门禁 PASS。
- [x] 5.2 `dev_docs/ARCH_PRD/ARCH-平台架构设计.md` 的 report-generator 路由清单改为 `/reports`。验证：该文档不再出现 `/reports/cases/:type`、`/reports/:runId`。
- [x] 5.3 `frontend/src/modules/report-generator/AGENTS.md`：删掉「用例分解 / 任务视角：仍可请求」与相关红线表述，只保留列表 / 内容 / 下载，并登记「禁止复活两个已删路由」。

## 6. 门禁与验收

- [x] 6.1 `python run.py check`：阻塞项 **20/22 PASS**。2 项红项为并发会话在改的文件，非本变更：
  `ruff-engines-format` → `engines/agents/messaging/billing.py`；`prettier-ts` → `frontend/src/modules/ai-assistant/helpers/assistant-cards.ts`。
  本变更文件的单独举证：`npx prettier --check` 三个改动 `.ts` 全绿；`ruff-format` / `ruff-lint` 平台范围门禁 PASS 已覆盖 `backend/apps/report_generator/*` 与改动测试。
- [x] 6.2 浏览器验收（Playwright，账号 `e2e_probe`）：
  `/reports/143` → 404 页；`/reports/cases/pass` → 404 页；`/reports` → 正常渲染「测试报告」。
  列表行点击仍走 `router.push(\`/tasks/${row.run_id}\`)`（`index.vue:204`，本变更未改）；该账号无可见任务，故按代码路径确认。
- [x] 6.3 `openspec validate remove-legacy-report-routes --strict` 通过；已归档为 `2026-10-23-remove-legacy-report-routes`，三份 delta 并入主 spec（+1 / ~5 / -0）。
