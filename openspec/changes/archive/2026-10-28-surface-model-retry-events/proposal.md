## Why

上一步（`2026-10-28-add-model-retry-fallback`）让模型调用具备退避重试与备用模型回退，但**重试只写进了 `logs/agents/agent_events.log`**。用户在任务详情里看到的仍是一条「跑了很久」的正常时间线：某一步为什么拖了 20 秒、是不是刚才在重试、有没有换过模型，界面上完全看不出来。排障只能上服务器翻日志。

现有事件链路其实已经具备承载能力：引擎把 `EventRecord` 交给 `TaskEventSink` 落 `task_events`，`task_reports` 用 `_EVENT_LABEL` / `_detail` 生成「标签 + 明细」，前端 `TaskDetailPage` 直接渲染 `event.label || event.event_type` 与 `event.detail`，不做类型白名单。缺的只是**中间件没有往这条链路写**，以及**没有这两类事件的标签与明细**。

## What Changes

- `engines/agents/middleware/model_retry.py`：新增 `_emit()`，在每次重试与每次回退时向 `current_sink()` 写一条 `EventRecord` —— `ModelRetryEvent`（模型 / 第几次 / 退避毫秒 / 失败原因）与 `ModelFallbackEvent`（来源模型 → 目标模型）；写完 `flush_sink()` 让详情页尽快看到。接收方抛异常时只记警告，不影响重试节奏；本地命令行未绑定接收方时由 `_NullSink` 丢弃。
- `backend/apps/task_list/task_reports.py`：`_EVENT_LABEL` 增两条中文标签；`_detail` 增两个分支，把结构化字段拼成一行可读明细（与 `SOP_STEP_STARTED`、`HintBlockEvent` 同风格）。
- 前端不需要改组件：`TaskDetailPage` 的时间线按 `label` + `detail` 泛化渲染，这两类事件会落在该轮「推理阶段」的同一时间线里（phase 取 `推理`）。
- 不写 `payload.status`，避免与工具结果的成功/失败语义混用；不计费、不计入 `count_model_call()`。

## 关联文档

- `openspec/specs/agent-model-resilience/spec.md`：新增「重试与回退写入任务事件流」要求。
- `openspec/specs/agent-task-event-store/spec.md`、`openspec/specs/agent-events-show/spec.md`：事件写入与展示契约不变，本变更只新增两类事件。
- 前序变更：`openspec/changes/archive/2026-10-28-add-model-retry-fallback/`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `agent-model-resilience`：追加「重试与回退写入任务事件流」一条要求。

## Impact

- 修改：`engines/agents/middleware/model_retry.py`、`backend/apps/task_list/task_reports.py`
- 新增测试：`tests/graybox/unit/test_model_retry_middleware.py`（事件写入 3 例）、`tests/graybox/unit/test_sop_event_stream.py`（明细 2 例）
- 数据：`task_events` 每发生一次重试/回退多一行，`event_type` 最长 48 字符、`block_type` 16 字符，均未越界；不新增字段、不新增迁移
- 不影响：任务状态机、计费口径、任务卡列表（详情页才渲染事件明细）
