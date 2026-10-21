## Why

「任务清单」目前只是 `ai_assistant` 模块里的一个页面：任务模型、任务接口、任务调度、计费与执行链仍归 AI 助手所有。产品要求把任务域整体拆成独立的前后端模块，`ai_assistant` 只保留助手与线路/身份配置（配对引擎的工作流）。

## What Changes

- **BREAKING** 新增 Django App `apps/task_list`，接管任务域：
  - 模型：`Task`、`TaskAttachment`、`TaskEvent`、`TaskMedia`、`TaskUsageHourly`。
  - 表名改为 `task_*`，通过重命名现有 `ai_tasks` / `ai_task_attachments` / `ai_task_events` / `ai_task_media` / `ai_usage_hourly` 完成，保留全部数据。
  - 迁移任务服务：`task_runner`、`engine_adapter`、`attachments`、`event_store`、`deepseek_billing`、`log_history`、任务后台恢复。
- **BREAKING** 新 API 前缀 `/api/tasks/*`（提交 / 列表 / 详情 / 重跑 / 关闭 / 删除 / 清空 / 任务详情报告 / 文件上传）；旧 `/api/ai/tasks/*` 与 `/api/ai/agent-tasks/*` **下线**，不保留兼容别名。
- **BREAKING** 任务详情页从测试报告迁入任务清单：`/tasks/:id` 取代 `/reports/task/:id`；后端 `GET /api/tasks/{id}/report/` 接管原 `/api/reports/task/{id}` 的任务事件流程聚合。
- 前端新增 `frontend/src/modules/task-list/`：`/tasks` 列表、`/tasks/:id` 详情、侧栏入口；任务卡、发布弹窗、详情、日志证据、组合式函数与 API 客户端整体迁入。
- `ai_assistant` 只保留：`AIAgent`、线路/身份配置页（`AgentRouteCard`、`AgentDetail`）、`/api/ai/agents/*`、头像上传与配对引擎配置；删除任务页面、任务 API、任务模型与任务服务。
- 仪表盘与测试报告改为读取 `task_list` 的任务模型，任务入口统一指向 `/tasks/:id`。

## 关联文档

- PRD-01 仪表盘（任务卡片入口）
- PRD-07 测试报告（任务报告列表）
- PRD-08 AI 助手（助手与线路配置）

## Capabilities

### New Capabilities

- `task-list-module`: 任务清单独立前后端模块的模型归属、`/api/tasks/*` 契约、前端 `/tasks` 页面与 AI 助手边界

### Modified Capabilities

- `dashboard-agent-tasks`: 任务详情入口从 `/ai-assistant/tasks/:id` 改为 `/tasks/:id`
- `report-ai-task-list`: 任务行点击从 `/reports/task/:id` 改为 `/tasks/:id`，数据源改为 `task_list.Task`
- `ai-task-publishing`: 任务卡「详情」与任务详情路由改为 `/tasks/:id`，移除旧 `/ai-assistant/tasks/:taskId` 口径

## Impact

- 新增 `apps/task_list/`（models / migrations / views / urls / services / admin / tests）
- `apps/ai_assistant/`：拆分 models、views_drf、urls、api、task_runner、engine_adapter、attachments、event_store、deepseek_billing、log_history、admin、apps.py 启动恢复
- `apps/report_generator/ai_task_reports.py`、`views.py`、`urls.py`：任务详情聚合迁出，列表改读 `task_list`
- `apps/dashboard/ai_usage.py`、`views.py`：改读 `task_list` 任务/用量模型
- `config/settings.py`、`config/urls.py`、`INSTALLED_APPS`
- 前端新增 `modules/task-list/`，改造 `modules/ai-assistant/`、`modules/report-generator/`、`modules/dashboard/`、`shared/components/sidebarNavConfig.ts`
- 大量后端/前端测试与 OpenSpec specs 同步
- 数据库迁移：表重命名 + 状态迁移；需备份与迁移演练
