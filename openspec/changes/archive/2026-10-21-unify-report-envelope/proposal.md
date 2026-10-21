## Why

报告相关接口仍有两处 **legacy 平铺响应**（`/api/reports/*` 5 个端点 + `/api/tasks/{id}/report/`），与全平台统一信封 `{status, data}` 不一致：

1. 前端两个模块各自按平铺字段判断成功/失败，错误处理与其它模块不同；
2. `TaskReportAPIView` 退回普通 Django `View` 后，drf-spectacular 不再采集它，`/api/tasks/{id}/report/` 已从 OpenAPI 基线中消失；
3. 现有 `openapi-schema` 门禁只校验"基线与代码一致"，不校验"业务路径是否都有契约"，这类缺口抓不到。

## What Changes

- **BREAKING**：`/api/reports/`、`/api/reports/cases/`、`/api/reports/run/{run_id}/`、`/api/reports/{filename}/content/`、`/api/tasks/{id}/report/` 的响应统一为 `{status, data}`；业务负载移入 `data`，不再自带 `status` 字段。
- `/api/reports/{filename}/` 保持 `FileResponse` 附件下载（不属于 JSON 信封）。
- `TaskReportAPIView` 恢复为 DRF `APIView`，重新进入 OpenAPI；`operationId` 固定为 `task_flow_report`。
- 前端 `report-generator` 与 `task-list` 两个模块的 api 层统一解包 `data`，组件不再读平铺 `status`。
- 新增 `openapi-coverage` 门禁：URLconf 的每条业务路径都必须出现在 `openspec/openapi.yaml` 中（参数名归一化后比对），缺失即失败。
- 更新能力规格：`report-ai-task-list`、`agent-task-flow-report` 增补信封要求；新增 `api-contract-coverage` 能力。

## Capabilities

### New Capabilities

- `api-contract-coverage`: 业务端点必须在 OpenAPI 基线中可查，缺失即阻断。

### Modified Capabilities

- `report-ai-task-list`: 报告列表/用例分解/内容查看改为标准信封。
- `agent-task-flow-report`: 任务事件流程改为标准信封，并恢复 DRF 视图。

## Impact

- 后端：`apps/report_generator/views.py`、`apps/task_list/views.py`、`apps/task_list/task_reports.py`（去掉 payload 内 `status`）。
- 契约：`openspec/openapi.yaml` 重新生成；新增 `tools/check_openapi_coverage.py`。
- 门禁：`tools/check_gates.py` 增 `openapi-coverage`；CI `backend-check` 同步。
- 前端：`frontend/src/modules/report-generator/api.ts`、`index.vue`、`ReportDetail.vue`、`CaseBreakdown.vue`；`frontend/src/modules/task-list/api/tasks.ts`、`TaskDetailPage.vue`。
- 测试：新增 `tests/graybox/integration/test_report_envelope.py`；两个 App 的 AGENTS.md 契约描述同步。
