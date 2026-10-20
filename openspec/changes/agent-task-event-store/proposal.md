## Why

结构化事件目前只交给内存中的接收方，任务结束后无法按任务回看轨迹，也无法按 8 位小数累计费用。文本日志仍在，但不能作为用量与图片的查询来源。这一段要先把写入落稳，读接口和报告页才能接着做。

## What Changes

- 平台任务运行时，把已折叠的结构化记录写入任务事件表。任务号为 0 时不写库，本地调试与文本日志照常。
- 工具返回里的图片只存长边不超过 720 的 JPEG 缩略图。同一任务内按原图内容去重，单个任务最多新增 40 张。
- 每次模型调用结束按北京时间的日期、小时、模型、角色和智能体累加 token 与 8 位费用。智能体编号是裸数字，不设外键。
- 任务结束时，只用模型调用结束行把三项费用与合计回写到任务。回复结束行上的轮次合计不参与这次求和。
- 删除任务时一并删除该任务的事件和图片。小时用量表不随任务删除。
- 文本日志保持双写。读接口、泳道图、仪表盘费用来源、历史 4 位兜底计费、原图保存和过期清理都不在本次范围。

## 关联文档

无独立子需求编号。归属平台总需求中的 AI 助手（PRD-08）。本次只覆盖运行轨迹方案里的写入段。

## Capabilities

### New Capabilities

- `agent-task-event-store`: 平台任务把结构化事件、缩略图和小时用量写入数据库，并在任务结束时回写 8 位费用。

### Modified Capabilities

## Impact

- `apps/ai_assistant`：任务费用列、事件表、图片表、小时用量表，以及经 `api.py` 的写入。迁移为 `0058_task_event_store`。
- `apps/ai_assistant/task_runner.py`：任务线程绑定接收方与运行上下文，结束时刷尾并回写费用。
- `engines/agents/event_sink.py`：运行上下文只传递任务号、智能体号、用例标题和步骤。引擎不 import `apps`。
- `engines/agents/workflow/ui_auto_workflow.py`：每条事件前盖上当前步骤序号和尝试次数。
- 测试：`tests/api/test_task_event_store.py`。不改 `tests/engines/agents/test_agents_workflow.py`，也不重跑真实模型。
- 不影响：`apps/dashboard`、`apps/ai_assistant/deepseek_billing.py`、任务卡 4 位展示、前端。
