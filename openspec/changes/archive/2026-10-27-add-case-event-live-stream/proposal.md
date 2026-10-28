# 用例编写模型事件流实时可见

## Why

用例编写任务运行时间长（003 任务单轮编写约 10 分钟），事件接收方按 50 条批量落库，报告页只在打开时请求一次。任务运行中打开报告看不到任何过程，只能等结束后再看。

## What Changes

- 用例编写流程逐条事件立即 flush，运行中即可在 `task_events` 看到 SOP/思考/工具/模型调用事件。
- 任务详情页对 `case_authoring` 运行中任务每 3 秒自动刷新报告，显示「运行中，自动刷新…」；进入终态后停止轮询。
- 运行中尚无事件时显示「模型正在运行，事件写入后会自动出现」，不再空白。
- 「重新执行」放开到 `interrupted` 任务（后端重启导致中断的任务可直接重跑）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `appliance-case-authoring-task`：用例编写事件流支持运行中实时落库与报告自动刷新。

## Impact

- 后端：`engines/agents/event_sink.py`、`engines/agents/messaging/messages.py`、`engines/agents/workflow/ui_auto_workflow.py`、`engines/agents/workflow/case_authoring_workflow.py`、`backend/apps/task_list/views.py`。
- 前端：`TaskDetailPage.vue`、`TaskBoard.vue`、`task-list/constants.ts`。
- 设备执行任务保持原行为（不逐条 flush、不自动轮询）。
