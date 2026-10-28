## MODIFIED Requirements

### Requirement: 按回复分轮并按阶段分块

系统 SHALL 以每条 `ReplyStartEvent` 或每条 SOP 步骤起点（事件类型名 `SOP_STEP_STARTED`）开始一轮。一轮内 MUST 按事件顺序排列；阶段相对上一块发生变化时才新开一块。块标题 MUST 为「开始」「推理阶段」「执行阶段」「结束」。连续且同类型、同一步骤与尝试次数的增量 MUST 并成一条，并用 `count` 给出次数；`count` MUST 取该段内所有增量事件的 `delta_count` 之和，写库时已经折叠成一行的事件 MUST 直接采用该行的 `delta_count`。`delta_count` 缺省为 1 的旧数据 MUST 表现与逐条增量合并时一致。步骤起点 MUST 落在它所开启的那一轮里，MUST NOT 被并入上一步骤的最后一轮。

#### Scenario: 增量合并后阶段交替

- **WHEN** 一轮中依次出现回复开始、三条工具参数增量、工具参数完成、工具结果完成、回复结束
- **THEN** 该轮的块依次为开始、推理阶段、执行阶段、结束，推理阶段的增量条 `count` 为 3，其后仍保留参数完成

#### Scenario: 步骤起点开启新的一轮

- **WHEN** 上一步骤的最后一轮已结束，随后到达一条 `SOP_STEP_STARTED`
- **THEN** 该步骤起点位于新的一轮内，其 `round_id` 大于上一步骤各轮的 `round_id`

#### Scenario: 写库已折叠的增量直接采用存储条数

- **WHEN** 一条工具参数增量行的 `delta_count` 为 17,447，且同段没有其它未折叠增量行
- **THEN** 报告的该项 `count` 为 17,447，展示时刻为该段第一条增量的时刻
