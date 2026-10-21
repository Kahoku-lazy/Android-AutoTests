# 设计：统一报告接口信封 + 覆盖门禁

## 背景

全平台成功响应由 `shared/renderers.EnvelopeJSONRenderer` 统一包成 `{status, data}`；只有报告相关接口例外：`report_generator` 的 5 个端点用 `FlatJSONAPIView`（渲染器覆盖为 `JSONRenderer`）返回平铺负载，`task_list` 的任务流程报告用普通 Django `View` + `JsonResponse` 返回平铺负载。后者还导致该端点从 OpenAPI 基线中消失。

## 决策

### D1：删掉 `FlatJSONAPIView`，统一走全局渲染器

所有报告端点改为 `APIView` 子类，返回 `Response(payload)`。`EnvelopeJSONRenderer` 负责包成 `{status: true, data: payload}`；错误响应由同一渲染器包成 `{status: false, message}`（DRF 4xx/5xx 分支）。这样信封只有一处实现。

### D2：业务负载不再自带 `status`

`build_report_list`、`build_task_flow`、`case_breakdown`、`report_content` 的返回值去掉顶层 `status`，避免出现 `{status, data: {status, ...}}` 的双层状态。前端只读信封的 `status`，业务字段全部从 `data` 取。

### D3：错误用 HTTP 状态码表达

参数错误 → 400，资源不存在 → 404，响应体 `{"message": "..."}`；由渲染器补 `status: false`。不再手写 `{"status": False, ...}`。

### D4：任务流程报告恢复 DRF 视图

`TaskReportAPIView` 改回 `APIView`，加 `@extend_schema(operation_id="task_flow_report", responses=OpenApiTypes.OBJECT)`；不可见/不存在时 `raise NotFound("任务不存在")`。这样 `/api/tasks/{task_id}/report/` 重新进入 OpenAPI。

### D5：前端 api 层解包 `data`

`report-generator/api.ts` 与 `task-list/api/tasks.ts` 的读接口返回 `data.data`（业务负载），组件不再判断平铺 `status`；错误统一走 `catch`（`formatApiError` / `message`）。下载 URL 不变。

### D6：覆盖门禁独立成脚本

`tools/check_openapi_coverage.py`：`django.setup()` 后递归枚举 URLconf，过滤 `/api/`、去 `format` 后缀、去 Router 根（`/api/ai/`、`/api/cases/`、`/api/workflow/`）、去 `schema`/`swagger`；把两边参数名归一化为 `{}` 后做集合比较。缺失则打印清单并退出 1。不做 allowlist：文件下载端点 `/{filename}/` 本身在 schema 中，应被覆盖。

在 `tools/check_gates.py` 注册为 `openapi-coverage`（阻塞），CI `backend-check` 的 OpenAPI 步骤改为 `--only openapi-schema,openapi-coverage`。

## 风险

- **BREAKING**：任何仍按平铺字段读响应的地方会失效。仓内消费点只有 `report-generator` 与 `task-list` 两个模块，已一并修改；无外部调用方。
- 报告下载 `FileResponse` 不套信封，保持附件语义。
- 任务流程页 `status` 字段含义从"任务状态字符串"改为"信封布尔值"，页面内部改读 `data.task.status`。

## 验证

- `python tools/check_gates.py --only openapi-schema,openapi-coverage` 通过。
- `python -m pytest tests/graybox/integration/test_report_envelope.py -q` 通过。
- `python manage.py check`、`ruff check` 通过。
- 手工：报告列表、用例分解、文件查看、任务流程页各打开一次。
