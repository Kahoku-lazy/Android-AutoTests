## 1. 现状与取舍

- [x] 1.1 确认事件链路可承载新类型：引擎 `EventRecord` → `TaskEventSink`（`backend/apps/task_list/event_store.py:34`）→ `task_events` → `task_reports._item`（`task_reports.py:473`）生成 `label` + `detail` → 前端 `TaskDetailPage.vue:327` 泛化渲染，无类型白名单
- [x] 1.2 确认落库边界：非增量记录单独成行、不参与 fold；`phase` ≤ 8 字符、`block_type` ≤ 16 字符、`event_type` ≤ 48 字符，`ModelRetryEvent` / `ModelFallbackEvent` / `推理` / `retry` 均未越界；不设 `payload.status`，避免与工具结果语义混用
- [x] 1.3 补齐异步边界：引擎在事件循环里跑，Django ORM 不能直接查 —— 新增 `event_sink.emit_record()`，Django 已启动时用 `database_sync_to_async(thread_sensitive=False)` 放进工作线程（与既有 `ui_auto_workflow.show_event` 同一做法），本地命令行仍直接调用

## 2. 实现

- [x] 2.1 `engines/agents/event_sink.py` 新增 `_django_ready` / `_deliver` / `emit_record`，模块文档同步
- [x] 2.2 `engines/agents/middleware/model_retry.py` 新增 `_emit()`（`phase="推理"`、`block_type="retry"`、带 `role_name` / `model`），接收方异常只记警告
- [x] 2.3 重试分支：日志 → `ModelRetryEvent`（attempt / attempts / delay_ms / reason）→ 退避；回退分支：日志 → `ModelFallbackEvent`（from_model / to_model / attempts）→ 调备用模型
- [x] 2.4 `backend/apps/task_list/task_reports.py`：`_EVENT_LABEL` 增「模型调用重试」「模型回退到备用模型」；`_detail` 增两个分支

## 3. 验证

- [x] 3.1 单测（`test_model_retry_middleware.py` +2 例）：绑假接收方断言重试事件的 `event_type` / `phase` / `block_type` / `role_name` / `payload`，以及「重试 → 回退」两条事件的顺序与字段
- [x] 3.2 单测：接收方 `emit` 抛异常时重试照常完成（`test_sink_failure_does_not_block_retry`，结果为 `ok`、调用 2 次、日志含「事件写入失败」）
- [x] 3.3 单测（`test_sop_event_stream.py` +1 例）：`_detail` 两个分支拼出「deepseek-flash · 第 1/2 次 · 500 ms 后重试 · …」与「deepseek-flash → deepseek-pro · 主模型重试用尽」，`_EVENT_LABEL` 两条中文标签
- [x] 3.4 端到端（`tests/api/test_task_event_flow.py` +1 例，`django_db(transaction=True)`）：真 `TaskEventSink` + `bind_run_context` 跑一次「主失败 → 回退成功」，`task_events` 落两行（`ModelRetryEvent` / `ModelFallbackEvent`，`phase=推理`、`block_type=retry`、`step_seq=1`），`build_task_flow` 取出的 items 标签为「模型调用重试」「模型回退到备用模型」
- [x] 3.5 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_model_retry_middleware.py tests/graybox/unit/test_sop_event_stream.py tests/api/test_task_event_flow.py -q` → **58 passed**
- [x] 3.6 `python -m ruff format --check` / `ruff check` 对本次改动的 6 个文件 → 全部通过（`ruff format` 已就地格式化）
- [x] 3.7 `python run.py check` → 与本次相关的项全 PASS（django-check / ruff-lint / pytest-collect / ruff-engines-format / ruff-engines-lint / boundary / vue-tsc / vitest / vite-build）；5 项 FAIL 均指向在途的 knowledge-assistant 与 usage_ledger 改动（`event_store.py` 的 `record_usage` 缩进、`usage_ledger/*`、两个 knowledge_assistant 测试、openapi 未登记新路径、前端 6+4 个文件未格式化）
- [x] 3.8 `npx openspec validate surface-model-retry-events --strict` 通过
