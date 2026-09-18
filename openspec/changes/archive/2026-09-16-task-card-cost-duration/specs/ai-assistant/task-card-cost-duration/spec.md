## Purpose

让任务看板卡片直接展示该任务的 DeepSeek 费用与执行耗时，列表不必进详情即可读到成本与时长。

## ADDED Requirements

### Requirement: Task list row includes cost and timestamps
The task list API MUST include `deepseek_cost` (same billing as task detail), `started_at`, and `finished_at` on each task row. Empty timestamps MUST be empty strings. `deepseek_cost` MUST be a number (zero when there is no billable usage).

#### Scenario: Serialized row has cost and times
- **WHEN** a task row is serialized for the agent task list
- **THEN** the payload includes numeric `deepseek_cost` and string `started_at` / `finished_at`

### Requirement: Task card shows cost and duration
The task board card MUST show meta rows labeled 费用 and 耗时. Cost MUST display as four decimal places in 元. Duration MUST use the same start/end formatting as task detail; missing start or end MUST display as — (em dash).

#### Scenario: Pending card without start
- **WHEN** a pending task has no `started_at`
- **THEN** the card shows 耗时 as — and 费用 as `0.0000 元` when cost is zero

#### Scenario: Completed card with times
- **WHEN** a completed task has `started_at`, `finished_at`, and a non-zero `deepseek_cost`
- **THEN** the card shows formatted duration and the cost with four decimal places and 元
