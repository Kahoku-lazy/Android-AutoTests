## Purpose

把测试报告工作台的列表、KPI 与趋势接到当前用户可见的 AI 助手任务卡，并禁止从该页跳进已失效的 Run/用例详情。

## ADDED Requirements

### Requirement: Report list is sourced from assistant tasks
`GET /api/reports` MUST return a flat envelope `{status, summary, trend, runs}` whose `runs` are the current user's visible `AITask` rows (one row per task). Visibility MUST match the assistant task board (same agent scope). The endpoint MUST remain read-only and MUST NOT write `ai_tasks` or other business tables.

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

### Requirement: Report workbench does not navigate away
The report workbench list MUST render task id as plain text, not as a link to `/reports/:id`. KPI pass/fail cards MUST NOT navigate to case breakdown. Clicking a table row MUST NOT change the route.

#### Scenario: Clicking a row stays on the page
- **WHEN** the user clicks a report list row or the task id cell
- **THEN** the browser remains on `/reports`

### Requirement: Empty copy points to AI assistant
When `runs` is empty, the workbench MUST tell the user to publish a task in AI assistant. Copy MUST NOT tell the user to run tests in the execution engine.

#### Scenario: Empty table hint
- **WHEN** the report table has no rows
- **THEN** the empty hint mentions AI assistant and does not mention the execution engine
