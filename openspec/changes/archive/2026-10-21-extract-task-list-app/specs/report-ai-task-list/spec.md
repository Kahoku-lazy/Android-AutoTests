## MODIFIED Requirements

### Requirement: Report list is sourced from assistant tasks

`GET /api/reports` MUST return a flat envelope `{status, summary, trend, runs}` whose `runs` are the current user's visible `Task` rows from `task_list` (one row per task). Visibility MUST match the task list module (same agent scope). The endpoint MUST remain read-only and MUST NOT write `task_tasks` or other business tables.

#### Scenario: List includes a published task

- **WHEN** the user has at least one visible task
- **THEN** `runs` contains a corresponding row and `summary.total_runs` equals the filtered task count

#### Scenario: Empty when no tasks

- **WHEN** the user has no visible tasks
- **THEN** `runs` is an empty list, summary counts are zero, and trend series are zeros for the requested chart range

### Requirement: Report workbench opens the task flow

测试报告列表 MUST 把任务编号显示为纯文本，MUST NOT 链到 `/reports/:id`。KPI 的通过与失败卡片 MUST NOT 进入用例分解。点击列表中的一行 MUST 进入任务清单的任务详情页 `/tasks/:taskId`。

#### Scenario: Clicking a row opens the task flow

- **WHEN** 用户点击测试报告列表中的一行
- **THEN** 浏览器进入 `/tasks/` 加上该行的任务编号

#### Scenario: Task id is not a run detail link

- **WHEN** 用户查看列表中的任务编号
- **THEN** 该编号不是指向 `/reports/:id` 的链接

### Requirement: Empty copy points to AI assistant

When `runs` is empty, the workbench MUST tell the user to create a task in the task list. Copy MUST NOT tell the user to run tests in the execution engine.

#### Scenario: Empty table hint

- **WHEN** the report table has no rows
- **THEN** the empty hint mentions the task list and does not mention the execution engine
