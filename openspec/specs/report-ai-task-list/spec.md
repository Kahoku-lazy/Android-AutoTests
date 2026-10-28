# report-ai-task-list Specification

## Purpose

把测试报告工作台的列表、KPI 与趋势接到当前用户可见的 AI 助手任务卡。点击一行进入该任务的事件流程；任务编号不链到已失效的 Run 详情。

## Requirements

### Requirement: Report list is sourced from assistant tasks

`GET /api/reports` MUST return a flat envelope `{status, summary, trend, runs}` whose `runs` are the current user's visible `Task` rows from `task_list` (one row per task). Visibility MUST match the task list module (same agent scope). The endpoint MUST remain read-only and MUST NOT write `task_tasks` or other business tables.

#### Scenario: List includes a published task

- **WHEN** the user has at least one visible task
- **THEN** `runs` contains a corresponding row and `summary.total_runs` equals the filtered task count

#### Scenario: Empty when no tasks

- **WHEN** the user has no visible tasks
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

### Requirement: 报告接口返回标准信封

`/api/reports/`、`/api/reports/{filename}/content/` MUST 返回标准信封 `{status, data}`，业务负载放在 `data` 中且 MUST NOT 自带 `status` 字段。`/api/reports/{filename}/` MUST 继续以附件形式返回文件（`FileResponse`），不套 JSON 信封。系统 MUST NOT 提供 `/api/reports/cases/` 与 `/api/reports/run/{run_id}/`。

#### Scenario: 报告列表使用信封

- **WHEN** 登录用户请求 `GET /api/reports/`
- **THEN** 响应为 200 且顶层只有 `status` 与 `data`
- **AND** `data` 含 `summary`、`trend`、`runs`

#### Scenario: 用例分解缺参数返回错误信封

- **WHEN** 请求 `GET /api/reports/cases/`（带或不带 `result`）
- **THEN** 响应为 404，MUST NOT 再返回 400、200 或空组负载

#### Scenario: 文件内容查看使用信封

- **WHEN** 请求 `GET /api/reports/{filename}/content/` 且文件存在
- **THEN** 响应为 200，`data` 含 `name`、`type`、`size`、`content`、`rows`、`headers`

#### Scenario: 文件不存在返回错误信封

- **WHEN** 请求 `GET /api/reports/{filename}/content/` 且目标不存在
- **THEN** 响应为 404，响应体为 `{status: false, message}`

#### Scenario: Run 详情端点不再存在

- **WHEN** 请求 `GET /api/reports/run/{run_id}/`
- **THEN** 响应为 404，MUST NOT 返回信封或任何报告负载

### Requirement: Report workbench filters rows by status

测试报告工作台 SHALL 在「测试报告」分区头提供状态筛选条，包含「全部 / 已完成 / 失败 / 已停止」四项，并在每项上显示当前查询条件下的条数。筛选条 MUST 使用共享 `FilterTabs`，MUST NOT 用内容页签（`AppTabs`）承载状态筛选。

「全部」的计数 SHALL 等于当前查询返回的任务卡总数；「已完成」SHALL 统计 `completed` 与 `success`；「失败」SHALL 只统计 `failed`；「已停止」SHALL 只统计 `stopped`。其它状态（`running` / `pending` / `interrupted` / `error` 等）MUST 只计入「全部」，MUST NOT 新增第五个筛选项。

切换筛选项 SHALL 只改变同一张报告表呈现的行，MUST NOT 为每个状态各渲染一张表格，MUST NOT 产生页签内层纵向滚动。

#### Scenario: Counts follow the current query

- **WHEN** 当前查询返回 12 张任务卡，其中 1 张为 `completed`、11 张为 `failed`
- **THEN** 筛选条依次显示「全部 12」「已完成 1」「失败 11」「已停止 0」

#### Scenario: Switching filters reuses one table

- **WHEN** 用户从「全部」切到「失败」
- **THEN** 页面上只有一张报告表，表内只剩 `failed` 行
- **AND** 纵向滚动仍由页面主体承担，表格容器内没有独立纵向滚动条

#### Scenario: Non-terminal statuses stay in All only

- **WHEN** 当前结果里存在 `running` 或 `pending` 的任务卡
- **THEN** 它们只出现在「全部」的计数与行里，不计入「已完成 / 失败 / 已停止」

#### Scenario: Empty result keeps a stable filter row

- **WHEN** 当前查询没有任何任务卡
- **THEN** 四个筛选项仍然渲染，计数均为 0，报告表显示空态

### Requirement: 报告工作台不提供报告详情与用例分解路由

测试报告工作台 MUST 只注册列表页 `/reports` 一个路由。系统 MUST NOT 注册 `/reports/:runId`、`/reports/cases/:resultType` 或等价路径；列表行、任务编号与 KPI 卡 MUST NOT 链到这两个路径。任务级详情 MUST 由任务清单的 `/tasks/:taskId` 提供。

#### Scenario: 直接访问已删的报告详情路由

- **WHEN** 用户直接打开 `/reports/143`
- **THEN** 前端不渲染报告详情页，落到 404 页

#### Scenario: 用例分解路由不可打开

- **WHEN** 用户直接打开 `/reports/cases/pass`
- **THEN** 前端落到 404 页，MUST NOT 渲染用例分解页

#### Scenario: 列表行仍进入任务详情

- **WHEN** 用户点击测试报告列表中的一行
- **THEN** 浏览器进入 `/tasks/` 加上该行的任务编号
