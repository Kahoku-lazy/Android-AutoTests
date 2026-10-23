## ADDED Requirements

### Requirement: 报告接口只读取渲染所需事件字段

系统 SHALL 在生成 `GET /api/tasks/{id}/report/` 响应时，只从事件表读取渲染所需的列。流式增量事件的载荷（`payload`）MUST NOT 进入报告聚合，也 MUST NOT 出现在响应中；增量 MUST 仅参与合并计数与 `count` 的计算。响应 MUST 继续使用 `{status, data}` 信封，`data` 中 `task`、`rounds`、`cases`、`conclusion` 的字段与语义 MUST 与变更前保持一致。在开发机本地 MySQL、单任务 10 万级事件（其中 9 成以上为流式增量）的条件下，服务端完成该次聚合的耗时 MUST 小于 4 秒（变更前实测 10.2 秒）。

#### Scenario: 大量增量任务的报告四秒内返回

- **WHEN** 单任务有 147,850 条事件，其中 139,948 条为工具参数增量
- **THEN** 接口在 4 秒内返回，且该增量段在 `data.rounds` 中仍是一条，`count` 等于该段内的增量条数

#### Scenario: 增量载荷不进入响应

- **WHEN** 任务里每条流式增量事件的 `payload` 各为 1 MB
- **THEN** 响应体不包含任何增量 `payload` 原文，响应体积不随增量载荷体积增长

#### Scenario: 输出与变更前逐字段一致

- **WHEN** 同一任务分别用变更前与变更后的实现生成报告
- **THEN** `task`、`rounds`、`cases`、`conclusion` 深度相等，时间、费用与判决均一致
