## ADDED Requirements

### Requirement: 报告轮次只下发一份

`data.rounds[]` MUST 带稳定的 `round_id`（从 0 起、同一响应内唯一）。`data.cases[]` MUST 用 `round_ids` 引用轮次，MUST NOT 再内嵌 `rounds` 字段；`round_ids` 中每个值 MUST 能在 `data.rounds` 中找到 `round_id` 相同的项。同一轮次对象在响应里 MUST 只序列化一次。单任务 15 万级事件、156 轮的响应 MUST 小于 5MB（未压缩）。

#### Scenario: 用例只引用不复制轮次

- **WHEN** 请求一个 156 轮、12 个用例的终态任务报告
- **THEN** `data.cases[]` 不含 `rounds` 字段，其 `round_ids` 合计 156 项
- **AND** `data.rounds` 仍是 156 项

#### Scenario: 轮次引用可解析且顺序一致

- **WHEN** 校验任一用例的 `round_ids`
- **THEN** 每个值都能在 `data.rounds[].round_id` 中找到唯一对应项
- **AND** 按 `round_ids` 顺序取出的轮次与该用例实际执行顺序一致

#### Scenario: 响应体积不因用例引用翻倍

- **WHEN** 同一任务分别用改动前与改动后的实现生成报告
- **THEN** 改动后响应小于改动前的 60%，且小于 5MB
- **AND** `task`、`rounds`、`conclusion` 的字段与语义不变

### Requirement: 终态任务报告缓存与条件请求

状态为 `completed`、`failed`、`interrupted`、`cancelled` 或 `stopped` 的任务，其报告 MUST 被缓存，TTL MUST 不小于 10 分钟。缓存键 MUST 包含任务编号与该任务当前最大事件 `seq`；最大 `seq` 增大（重跑、补写事件）后 MUST 重新构建，MUST NOT 继续返回旧报告。非终态任务 MUST NOT 缓存。响应 MUST 带 `ETag`；请求带相同 `If-None-Match` 时 MUST 返回 `304` 且响应体为空。缓存命中时 MUST 在 300ms 内返回（本地开发机口径）。

#### Scenario: 二次打开命中缓存

- **WHEN** 对同一终态任务连续请求两次报告
- **THEN** 第二次在 300ms 内返回，且 `data` 与第一次深度相等

#### Scenario: ETag 命中返回 304

- **WHEN** 客户端带上一次响应里的 `ETag` 再次请求
- **THEN** 返回 304 且没有响应体

#### Scenario: 重跑后不复用旧报告

- **WHEN** 任务被重跑并写入新事件后再请求报告
- **THEN** 响应包含新事件的轮次，MUST NOT 与重跑前缓存逐字段相等

#### Scenario: 运行中任务不写缓存

- **WHEN** 任务处于 `running`，连续请求两次报告，且期间新增了一轮事件
- **THEN** 第二次响应的轮次数比第一次多 1
