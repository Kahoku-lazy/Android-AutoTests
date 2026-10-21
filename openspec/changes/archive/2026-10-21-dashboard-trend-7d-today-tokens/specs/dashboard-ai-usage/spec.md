## MODIFIED Requirements

### Requirement: 仪表盘提供 AI 用量统计接口

系统 SHALL 在仪表盘统计接口的 `ai_usage` 中提供任务数量、输入 token、输出 token、合计 token、缓存命中 token、缓存命中率、平均每任务 token 与 DeepSeek 费用，且均分「今日 / 累计」。输入、输出、缓存命中与费用 MUST 来自当前用户可见智能体的小时用量合计。今日 MUST 指统计日等于当前日期。任务数量 MUST 按可见任务计数，MUST NOT 改用小时记录的调用次数。DeepSeek 费用 MUST 为这些小时费用之和，精度到小数点后 8 位。MUST NOT 用任务上的 token 列，或按小数点后 4 位重算的费用，作为这组数字。`ai_usage.agents` MUST 为每个可见智能体给出一份整份用量。近 7 日的 Token 曲线与费用曲线 MUST 按同一小时用量、以统计日分桶。

#### Scenario: 统计接口返回 AI 用量

- **WHEN** 用户请求仪表盘统计接口
- **THEN** 响应含 `ai_usage`，其 `task_count`、`input_tokens`、`output_tokens`、`total_tokens`、`cache_hit_tokens`、`cache_hit_rate`、`avg_tokens_per_task`、`deepseek_cost` 各含 `today` 与 `total`，并含 `agents` 数组

#### Scenario: 缓存命中率除零

- **WHEN** 输入 token 总数为 0
- **THEN** 缓存命中率为 0，不报错

#### Scenario: 两个角色的费用并进同一份

- **WHEN** 同一智能体在同一统计日有执行者与验收者两条小时用量
- **THEN** 该日输入、输出、缓存命中与费用等于两条记录之和，且只对应这一份智能体用量

## ADDED Requirements

### Requirement: 今日用量按小时返回且不提前出数

系统 SHALL 在统计接口的 `charts.today_usage` 返回当天逐小时的用量，字段为 `tokens`、`cost`（等长 24 项，下标即小时 0–23）与 `current`。`tokens[h]` MUST 为第 h 小时（`[h:00, h+1:00)`）内「输入 token + 输出 token」之和，`cost[h]` MUST 为该小时内 DeepSeek 费用之和（元，8 位小数）；该小时尚未走完或尚未开始时，对应项 MUST 为 `null`，MUST NOT 提前给出该小时的数据，MUST NOT 返回当天累计值。`current` MUST 描述正在进行中的那一小时：`hour` 为当前时刻（0–24，最多 2 位小数）、`tokens` 与 `cost` 为该小时从起点到当前时刻的消耗；当前时刻正好落在整点时 `current` MUST 为 `null`。所有数值 MUST 来自当前用户可见智能体的小时用量表，MUST NOT 取任务表上的 token 列或按任务回写的费用。当天没有用量或小时用量表不可用时，已走完的小时 MUST 为 `0`、未走完与未开始的小时 MUST 为 `null`，且 MUST 不报错。该字段 MUST NOT 包含缓存命中序列。

#### Scenario: 未到达的小时不出数

- **WHEN** 当天 `11:05` 时读取统计接口，且 `[09:00,10:00)` 已消耗 1,239,521 token
- **THEN** `tokens[9]` 为 `1,239,521`，`tokens[11]` 及之后的小时均为 `null`
- **AND** `current.hour` 约为 `11.08`，`current.tokens` 为 `[11:00,11:05)` 的消耗

#### Scenario: 整点后归入已完成小时

- **WHEN** 当天已过 `12:00`，`[11:00,12:00)` 共消耗 40 token
- **THEN** `tokens[11]` 为 `40`，`current` 指向 `12` 点这一小时

#### Scenario: 整点边界无进行中数据

- **WHEN** 当前时刻正好是 `12:00:00`
- **THEN** `current` 为 `null`，`tokens[11]` 已带出完整值

#### Scenario: 当天无用量

- **WHEN** 当前用户可见智能体当天没有任何小时用量
- **THEN** 已走完的小时为 `0`，未走完与未开始的小时为 `null`，`current` 的 `tokens` 与 `cost` 为 0，接口仍返回成功
