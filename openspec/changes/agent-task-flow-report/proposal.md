## Why

任务跑完后的事件已经落在库里，但测试报告列表点不开，任务卡「详情」仍进旧的步骤页。需要按时间把一轮回复展示成开始、推理、执行、结束，并让两个入口都打开这一页。

## What Changes

- `GET /api/reports/task/{id}` 返回当前用户可见任务的事件流程：按 `ReplyStartEvent` 分轮，阶段切换才新开一块，连续同类增量并成一条并带次数。
- 测试报告列表点击一行进入 `/reports/task/:taskId`。KPI 与 `/reports/:id`、用例分解仍不跳转。**BREAKING**：原先「点击行不得改路由」不再成立。
- 任务卡「详情」进入同一报告页，不再进入 `/ai-assistant/tasks/:taskId`。旧详情路由仍保留，但不从卡片进入。
- 报告页起止与每条事件时间为 `YYYY-MM-DD HH:mm:ss`，起止旁给出整次任务执行耗时。页头下方给出验收结论：最后一次判决通过且任务完成时为 PASS，否则为 FAIL，并展示判决说明与执行交付。

## 关联文档

- PRD-07 测试报告
- PRD-08 AI 助手

## Capabilities

### New Capabilities

- `agent-task-flow-report`: 单任务事件流程的只读接口与报告页（分轮、分阶段、增量合并、时间到秒、执行耗时）

### Modified Capabilities

- `report-ai-task-list`: 列表行可进入该任务的事件流程报告
- `ai-task-publishing`: 任务卡「详情」改去事件流程报告

## Impact

- `apps/report_generator/ai_task_reports.py`、`views.py`：只读聚合，不写库
- `frontend/src/modules/report-generator/TaskReport.vue`、`index.vue`
- `frontend/src/modules/ai-assistant/components/TaskBoard.vue`
- 测试：`tests/api/test_task_event_flow.py`
- 仪表盘最近任务仍打开旧详情页，不在本次范围
