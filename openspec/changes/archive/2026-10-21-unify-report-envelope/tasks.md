## 1. 契约与规格

- [x] 1.1 `openspec/changes/unify-report-envelope/specs/` 三份 delta 写入并 `openspec validate unify-report-envelope --strict` 通过
- [x] 1.2 `openspec/specs/report-ai-task-list`、`agent-task-flow-report` 的信封描述随归档并入主规格

## 2. 后端

- [x] 2.1 `apps/report_generator/views.py`：删除 `FlatJSONAPIView` 与 `JSONRenderer` 覆盖；5 个端点返回 `Response(payload)`；错误改 `{"message": ...}` + 400/404
- [x] 2.2 `apps/task_list/views.py`：`TaskReportAPIView` 改回 `APIView`，`NotFound` 表达 404，补 `@extend_schema(operation_id="task_flow_report")`
- [x] 2.3 `apps/task_list/task_reports.py`：`build_report_list`、`build_task_flow` 去掉顶层 `"status"`
- [x] 2.4 重新生成 `openspec/openapi.yaml`（含 `/api/tasks/{task_id}/report/`）
- [x] 2.5 `apps/report_generator/AGENTS.md`、`apps/task_list/AGENTS.md`：信封描述改为标准信封

## 3. 门禁

- [x] 3.1 新增 `tools/check_openapi_coverage.py`（URLconf ↔ OpenAPI 归一化比对）
- [x] 3.2 `tools/check_gates.py` 注册 `openapi-coverage`（阻塞）
- [x] 3.3 `.github/workflows/ci-phase1.yml` 的 OpenAPI 步骤改为 `--only openapi-schema,openapi-coverage`

## 4. 前端

- [x] 4.1 `report-generator/api.ts` 解包 `data.data`；`index.vue`、`ReportDetail.vue`、`CaseBreakdown.vue` 去掉平铺 `status` 判断
- [x] 4.2 `task-list/api/tasks.ts` 解包 `data.data`；`TaskDetailPage.vue` 改读 `data` 并去掉平铺判断

## 5. 测试与验收

- [x] 5.1 新增 `tests/graybox/integration/test_report_envelope.py`：列表 / 用例分解 / 内容查看 / 任务流程的成功与错误信封
- [x] 5.2 `python tools/check_gates.py --only openapi-schema,openapi-coverage` 通过
- [x] 5.3 `python -m pytest tests/graybox/integration/test_report_envelope.py -q` 通过
- [x] 5.4 `python manage.py check` 与 `ruff check` 通过
