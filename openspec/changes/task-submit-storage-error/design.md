## Context

`POST /api/tasks/submit/` 的失败路径有两类：一类由视图主动抛出 DRF 异常（`ValidationError` / `NotFound` / `PermissionDenied`），经 `EnvelopeJSONRenderer` 变成 `{status:false, message}`；另一类是未捕获异常（当前是 `store_flat_upload` 写盘时的 `OSError` / `PermissionError`），由 Django 的 500 处理器渲染成 HTML 页，绕过信封与 `message`。

提交路径上有两处写盘：`_submit_assistant_sop`（本地 YAML 与平台用例来源共用的配置附件）与 `_submit_material_workflow`（用例编写/需求拆解来源的文档附件），都把 `store_flat_upload(...)` 的结果作为 `api.add_task_attachment(..., stored_path=...)` 的参数。`store_flat_upload` 在 `backend/apps/task_list/attachments.py`，内部 `Path.write_bytes` 抛原生 `OSError`。

运行环境：Django 6.0.8 / DRF 3.18.3；DRF 的 `APIException` 默认 `status_code = 500`，会被 `handle_exception` 正常转成响应（不会再次冒泡），再由 `EnvelopeJSONRenderer` 用 `detail` 填 `message`。

## Goals / Non-Goals

**Goals:**

- 写盘失败时返回 500 + `{status:false, message}` 信封，`message` 说明失败环节与可执行排查方向。
- 失败时任务与附件记录都不落库（沿用既有原子性）。
- 成功路径、既有 4xx 文案与状态码完全不变。

**Non-Goals:**

- 不改 `attachments.py` / `upload_cleanup.py` 的接口与语义，不新增自定义异常类。
- 不改状态码语义（不做 4xx/503 转换），不改前端错误文案映射。
- 不处理 `/api/tasks/upload-file/`、`/api/tasks/{id}/rerun/` 等其它端点的写盘失败（另开变更）。
- 不加全局 `EXCEPTION_HANDLER` 把所有 `OSError` 兜底成可读 message。

## Decisions

1. **在视图层做「原生异常 → 可读 API 错误」的转换，放一个私有 helper，不动 `attachments.py`。**
   理由：`attachments.py` 是存储工具，`AttachmentError` 语义是「调用方内容不合法」；若让它抛 DRF 异常，就把 Web 层耦合进工具函数。而现有 `except AttachmentError → ValidationError` 的映射会把磁盘故障误判成 400 客户端错误。
   备选（否）：让 `store_flat_upload` 抛 `AttachmentError` → 被现有 catch 变成 400，语义错；新增一个存储专用异常类 → 触碰「新增自定义异常类需先立项」的红线。
2. **用 DRF 内置 `APIException` 承载错误，`detail` 即前端 message。** 默认 500 正合「服务端环境问题」的语义，且 `EnvelopeJSONRenderer._extract_message` 已支持 `detail`。
3. **状态码保持 500。** 写失败是部署/权限问题，调用方重试与改参数都无效；前端 `formatApiError` 先取 `response.data.message`，因此展示效果只取决于 message 是否存在，与 500 无关。
4. **文案口径：`任务配置文件写入失败：<操作系统原因>，请检查运行账号对该目录的写权限`。**
   原因取 `exc.strerror or str(exc)`（如 `Permission denied`），不带绝对路径——路径只进 `backend_log.exception` 的堆栈，避免把服务器目录结构暴露到界面。
5. **两处调用点共用同一 helper，事务结构不改。** helper 在 `with transaction.atomic():` 内抛出 `APIException`，Django 照常回滚 `create_task` 与其后的附件记录；不新增清理逻辑（打开失败无残片，部分写入残片由既有 `upload_cleanup` 周期清理）。
6. **错误不要吞掉：** 转换前必须 `backend_log.exception(...)` 记一条完整堆栈，保留路径与 errno，供服务端排障。

## 模块防火墙自检

- 跨 App import：本设计只在 `backend/apps/task_list/views.py` → `backend/apps/task_list/attachments.py`（同 App 内部）；不新增任何跨 App 依赖。
- 写库路径：不新增写路径，任务与附件仍分别走 `api.create_task` 与 `api.add_task_attachment`；视图不直接写 ORM。
- 异常类：不新增自定义异常类，复用 `rest_framework.exceptions.APIException`。
- 前端不直连数据库；本设计不触及仪表盘；无新表、无迁移。
- 未放宽任何模块依赖方向。

## Risks / Trade-offs

- [message 里带操作系统原文（可能本地化/含驱动细节）] → 只取 `strerror`，测试按关键词（「写入失败」「写权限」）断言，不断言整句。
- [500 仍落进前端 5xx 分支] → 前端 `formatApiError` 已优先取 `message`；补一条前端断言防止将来映射被改坏。
- [其它写盘端点仍返回 HTML 500] → 明示为 Non-Goal，在 proposal 的 Impact 里登记，后续按需另开变更。
- [只覆盖提交接口的两处调用点，未来新增第三处会漏] → helper 作为唯一落盘入口，新增调用点必须复用它；tasks.md 里加一条「新调用点必须走 helper」的检查项。
