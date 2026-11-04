## ADDED Requirements

### Requirement: 用例与步骤给出墙钟耗时

`GET /api/tasks/{id}/report/` 的 `data.cases[].duration_ms` MUST 为该用例全部轮次的墙钟跨度（最早 `started_at` 到最晚 `ended_at`），单位毫秒、整数。`data.cases[].steps[].duration_ms` MUST 为该步骤全部轮次（含重试与验收）的同一口径跨度。

跨度 MUST 只按本条用例内的轮次计算，MUST NOT 用 `(step_seq, attempt)` 做跨用例的全局键。本要求 MUST NOT 改变既有 `rounds` / `cases` 的分组口径与字段语义，也 MUST NOT 突破既有报告接口的性能预算。

#### Scenario: 步骤耗时覆盖执行与验收

- **WHEN** 第 1 步的执行轮跨 09:00:00–09:00:30、验收轮跨 09:00:31–09:00:34
- **THEN** 该步 `duration_ms` 为 34000

#### Scenario: 用例耗时覆盖其全部步骤

- **WHEN** 一条用例含 2 个步骤，最早事件 09:00:00、最晚事件 09:02:00
- **THEN** 该用例 `duration_ms` 为 120000
- **AND** 两个步骤的 `duration_ms` 之和不超过该用例 `duration_ms`

#### Scenario: 两条用例都从第 1 步开始时互不串号

- **WHEN** 两条用例各有第 1 步，且第二条用例的第 1 步比第一条晚 2 分钟
- **THEN** 两条用例的 `duration_ms` 分别独立计算，不合并成一段跨度

### Requirement: 轮级给出模型耗时与运行标记

`data.rounds[].model_ms` MUST 只统计该轮 `ModelCallEndEvent` 的 `duration_ms` 之和，MUST NOT 用轮次墙钟冒充模型耗时；该轮没有任何模型调用事件时 MAY 回退为轮次墙钟。

`data.rounds[].running` MUST 标明该轮是否尚未结束（缺少 `ended_at`）。该轮所属的步骤与用例在同一响应里 MUST 也标记为未结束。

#### Scenario: 执行轮的模型耗时不含工具执行

- **WHEN** 某执行轮墙钟 30 秒，其中模型调用合计 12 秒
- **THEN** 该轮 `model_ms` 为 12000

#### Scenario: 运行中的轮次不带数字

- **WHEN** 某轮事件只有 `started_at` 没有 `ended_at`
- **THEN** 该轮 `running` 为 true
- **AND** 该轮所属步骤与用例的 `running` 同为 true

### Requirement: 缺失时间戳不伪造耗时

事件缺少 `started_at` / `ended_at` 的存量任务，四层耗时字段 MUST 返回 0 或 `null`，MUST NOT 用 `called_at`、`moment` 等其它字段推算或伪造时长。

#### Scenario: 存量事件缺少时间戳

- **WHEN** 任务的所有事件 `started_at` 与 `ended_at` 均为空
- **THEN** 用例、步骤、轮的耗时字段返回 0 或 `null`，不出现推算值
