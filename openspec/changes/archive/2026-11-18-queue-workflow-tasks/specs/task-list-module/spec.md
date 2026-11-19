## MODIFIED Requirements

### Requirement: Task detail report moves to the task list

任务报告 MUST 从任务清单表格的「报告」操作打开。系统 MUST NOT 再要求 `/tasks/:id` 作为任务详情页。测试报告列表点击一行时 MUST NOT 进入不存在的 `/tasks/:id`。

#### Scenario: Task card detail opens /tasks/:id

- **WHEN** 用户在任务清单点击一行的「报告」
- **THEN** 系统打开该任务已生成的报告
- **AND** 不进入 `/tasks/:id`

#### Scenario: Report list row opens the task list detail

- **WHEN** 用户在测试报告列表点击一行任务
- **THEN** 系统不进入 `/tasks/:id`

### Requirement: Frontend task list module

前端 SHALL 提供 `frontend/src/modules/task-list/`，路由 MUST 包含 `/tasks`，侧栏「AI任务」分组 MUST 提供「任务清单」入口。该模块 MUST 提供工作流任务表格、筛选、重跑、关闭与报告入口。它 MUST NOT 再提供新建任务弹窗或 `/tasks/:id` 页面。`ai-assistant` MUST NOT 引用任务清单的私有组件或组合式函数。

#### Scenario: Task list module renders list and detail

- **WHEN** 用户访问 `/tasks`
- **THEN** 页面渲染工作流任务表格，接口请求走 `/api/tasks/*`
- **AND** 页面没有新建任务弹窗

#### Scenario: AI assistant has no task imports

- **WHEN** 检查 `frontend/src/modules/ai-assistant/` 的 import
- **THEN** 不存在对 task-list 模块任务组件、组合式函数或任务 API 的引用
