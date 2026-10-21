# report-ai-task-list Specification

## Purpose

把测试报告工作台的列表、KPI 与趋势接到当前用户可见的 AI 助手任务卡。点击一行进入该任务的事件流程；任务编号不链到已失效的 Run 详情。

## Requirements

### Requirement: Report list is sourced from assistant tasks
`GET /api/reports` MUST return a flat envelope `{status, summary, trend, runs}` whose `runs` are the current user's visible `task_list.Task` rows (one row per task). Visibility MUST match the assistant task board (same agent scope). The endpoint MUST remain read-only and MUST NOT write `task_tasks` or other business tables.

#### Scenario: List includes a published task
- **WHEN** the user has at least one visible assistant task
- **THEN** `runs` contains a corresponding row and `summary.total_runs` equals the filtered task count

#### Scenario: Empty when no tasks
- **WHEN** the user has no visible assistant tasks
- **THEN** `runs` is an empty list, summary counts are zero, and trend series are zeros for the requested chart range

### Requirement: Task-card success metrics
Summary and daily trend MUST count a task as pass when status is `completed` or `success`, and as fail when status is `failed`. Pass rate MUST be pass / (pass + fail), or `0` when there are no terminal pass/fail tasks. Pending and running tasks MUST appear in `runs` and `total_runs` but MUST NOT increment pass or fail totals.

#### Scenario: Mixed statuses
- **WHEN** visible tasks include pending, completed, and failed
- **THEN** `summary.total_pass` counts completed (and success), `summary.total_fail` counts failed, and pending is excluded from both

### Requirement: Report row fields without case columns
Each `runs[]` item MUST include: task id, device display (`device_label` if non-empty else `device_serial`), task title, assistant name, status, duration text, and start time. The list payload MUST NOT include case-centric fields `case_count`, `passed`, `failed`, or `rate`.

#### Scenario: Device label fallback
- **WHEN** a task has empty `device_label` and a non-empty `device_serial`
- **THEN** the row device field shows the serial

### Requirement: Report workbench opens the task flow

测试报告列表 MUST 把任务编号显示为纯文本，MUST NOT 链到 `/reports/:id`。KPI 的通过与失败卡片 MUST NOT 进入用例分解。点击列表中的一行 MUST 进入该任务的事件流程页 `/tasks/:id`。

#### Scenario: Clicking a row opens the task flow

- **WHEN** 用户点击测试报告列表中的一行
- **THEN** 浏览器进入 `/tasks/` 加上该行的任务编号

#### Scenario: Task id is not a run detail link

- **WHEN** 用户查看列表中的任务编号
- **THEN** 该编号不是指向 `/reports/:id` 的链接

### Requirement: Empty copy points to AI assistant
When `runs` is empty, the workbench MUST tell the user to publish a task in AI assistant. Copy MUST NOT tell the user to run tests in the execution engine.

#### Scenario: Empty table hint
- **WHEN** the report table has no rows
- **THEN** the empty hint mentions AI assistant and does not mention the execution engine
