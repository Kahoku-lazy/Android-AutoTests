## Why

提交任务时若服务端把配置附件写入上传目录失败（例如运行账号对该目录没有写权限），`POST /api/tasks/submit/` 让 `PermissionError` 一路冒到 Django，返回的是 HTML 500 错误页；前端 `formatApiError` 对「5xx 且无 `message`」一律显示「服务暂时异常，请稍后重试」，真实原因在界面上完全不可见。2026-11-25 现场就发生了一次：界面只报一句通用文案，最终要翻 `logs/backend.log` 的 traceback 才定位到写盘失败。

## What Changes

- `POST /api/tasks/submit/` 在把配置附件落到上传目录这一步捕获 `OSError`，改为抛 DRF `APIException`：HTTP 状态码仍是 500，但响应体走既有 `{status: false, message}` 信封，`message` 写明「任务配置文件写入失败」并提示检查上传目录写权限。
- 失败时任务 MUST NOT 落库（沿用现有 `transaction.atomic()` 回滚口径，不新增额外清理逻辑）。
- 不新增自定义异常类（用 DRF 内置 `APIException`），不改接口状态码语义，不改前端错误文案映射。

## 关联文档

无 PRD 条目：本改动来自 2026-11-25 现场故障的排障结论（提交任务 500、界面只显示「服务暂时异常」），属缺陷修复，不对应既有 PRD 需求编号。

## Capabilities

### New Capabilities

- `task-submit-error-contract`: 提交任务接口的失败响应契约——服务端在落盘/建任务阶段失败时必须返回 `{status:false, message}` 信封并给出可读原因，不得把 HTML 错误页或通用文案丢给调用方。

### Modified Capabilities

无。

## Impact

- 后端：`backend/apps/task_list/views.py`（`_submit_assistant_sop`、`_submit_material_workflow` 两处附件落盘调用点）；`backend/apps/task_list/attachments.py` 与 `upload_cleanup.py` 不改。
- 接口：`POST /api/tasks/submit/` 的失败响应体（状态码不变，仍为 500）；成功响应不变。
- 前端：无需改动，`frontend/src/shared/types/api-error.ts` 已优先取 `response.data.message`。
- 测试：新增 `tests/task/api/test_task_submit_storage_error.py`；既有 `tests/task/api/test_task_submit_sop.py`、`tests/task/api/test_task_submit_platform_cases.py` 不得回归。
- 依赖与迁移：无。
