## Purpose

把任务域从 AI 助手拆成独立的前后端模块：后端 `task_list` 拥有任务、附件、事件、媒体与小时用量表及 `/api/tasks/*`，前端拥有 `/tasks` 列表与 `/tasks/:id` 详情；AI 助手只保留助手与线路/身份配置。

## ADDED Requirements

### Requirement: Task list app owns the task domain

系统 SHALL 提供 Django App `apps.task_list`，拥有 `Task`、`TaskAttachment`、`TaskEvent`、`TaskMedia`、`TaskUsageHourly` 五个模型，分别使用 `task_tasks`、`task_attachments`、`task_events`、`task_media`、`task_usage_hourly` 表。`Task.agent` MUST 为指向 `ai_assistant.AIAgent` 的外键。`apps.ai_assistant` MUST NOT 再定义任务、附件、任务事件、任务媒体或任务用量模型。

数据库迁移 MUST 通过重命名既有 `ai_tasks`、`ai_task_attachments`、`ai_task_events`、`ai_task_media`、`ai_usage_hourly` 完成，MUST NOT 丢失任何行、外键关系或自增序列。迁移 MUST 可回滚到旧表名。

#### Scenario: Existing task rows survive the table rename

- **WHEN** 迁移前数据库中存在任务、附件、事件、媒体与小时用量行
- **THEN** 迁移后这些行分别出现在 `task_tasks`、`task_attachments`、`task_events`、`task_media`、`task_usage_hourly`，行数与关联关系不变

#### Scenario: AI assistant no longer owns task models

- **WHEN** 迁移完成后检查 `apps.ai_assistant` 的模型
- **THEN** 其中不存在任务、附件、任务事件、任务媒体或任务用量模型

### Requirement: Task APIs live under /api/tasks

任务域接口 MUST 注册在 `/api/tasks/` 下：提交、列表、详情、重跑、关闭、删除、清空、详情报告与文件上传。旧 `/api/ai/tasks/*` 与 `/api/ai/agent-tasks/*` MUST 不再注册，直接访问 MUST 返回 404。响应信封 MUST 保持 `{status, data}`。

#### Scenario: New task endpoints respond

- **WHEN** 前端调用 `GET /api/tasks/`、`POST /api/tasks/submit/` 或 `POST /api/tasks/{id}/rerun/`
- **THEN** 请求命中 `task_list` 的视图并返回既有 `{status, data}` 结构

#### Scenario: Old task endpoints are gone

- **WHEN** 客户端访问 `/api/ai/tasks/submit/` 或 `/api/ai/agent-tasks/`
- **THEN** 返回 404，不发生任务创建或列表读取

### Requirement: Task detail report moves to the task list

任务详情报告 MUST 由 `GET /api/tasks/{id}/report/` 提供，前端页面 MUST 为 `/tasks/:id`。`/api/reports/task/{id}` 与前端 `/reports/task/:id` MUST 不再提供任务详情。测试报告列表 MUST 继续只读展示任务行，但行点击 MUST 进入 `/tasks/:id`。

#### Scenario: Task card detail opens /tasks/:id

- **WHEN** 用户在任务清单点击任务卡「详情」
- **THEN** 路由进入 `/tasks/:id`，页面展示该任务的事件流程报告

#### Scenario: Report list row opens the task list detail

- **WHEN** 用户在测试报告列表点击一行任务
- **THEN** 路由进入 `/tasks/:id`，不进入 `/reports/task/:id`

### Requirement: AI assistant keeps only assistant and route configuration

`apps.ai_assistant` MUST 只保留 `AIAgent`、线路/身份配置页、`/api/ai/agents/*`、头像上传与配对引擎配置。它 MUST NOT 再提供任务列表、任务详情、任务创建、调度、重跑、关闭、删除、清空、任务费用或任务用量接口/页面。

#### Scenario: Assistant page only configures routes

- **WHEN** 用户打开平台小助手页
- **THEN** 页面只展示助手与线路/身份配置，不出现任务列表、任务详情或新建任务入口

### Requirement: Frontend task list module

前端 SHALL 提供 `frontend/src/modules/task-list/`，路由 MUST 包含 `/tasks` 与 `/tasks/:id`，侧栏「AI任务」分组 MUST 提供「任务清单」入口。任务卡、新建任务弹窗、任务详情、日志证据、组合式函数与 API 客户端 MUST 从 `ai-assistant` 模块迁入；`ai-assistant` MUST NOT 再引用任务清单的私有组件或组合式函数。

#### Scenario: Task list module renders list and detail

- **WHEN** 用户访问 `/tasks` 或 `/tasks/:id`
- **THEN** 分别渲染任务清单列表与任务详情，接口请求走 `/api/tasks/*`

#### Scenario: AI assistant has no task imports

- **WHEN** 检查 `frontend/src/modules/ai-assistant/` 的 import
- **THEN** 不存在对 task-list 模块任务组件、组合式函数或任务 API 的引用
