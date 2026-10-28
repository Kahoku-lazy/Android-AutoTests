# agent-task-flow-report 变更

## MODIFIED Requirements

### Requirement: 按回复分轮并按阶段分块

系统 SHALL 以每条 `ReplyStartEvent` 或每条 SOP 步骤起点（事件类型名 `SOP_STEP_STARTED`）开始一轮。一轮内 MUST 按事件顺序排列；阶段相对上一块发生变化时才新开一块。块标题 MUST 为「开始」「推理阶段」「执行阶段」「结束」。连续且同类型、同一步骤与尝试次数的增量 MUST 并成一条，并用 `count` 给出次数。步骤起点 MUST 落在它所开启的那一轮里，MUST NOT 被并入上一步骤的最后一轮。

#### Scenario: 增量合并后阶段交替

- **WHEN** 一轮中依次出现回复开始、三条工具参数增量、工具参数完成、工具结果完成、回复结束
- **THEN** 该轮的块依次为开始、推理阶段、执行阶段、结束，推理阶段的增量条 `count` 为 3，其后仍保留参数完成

#### Scenario: 步骤起点开启新的一轮

- **WHEN** 上一步骤的最后一轮已结束，随后到达一条 `SOP_STEP_STARTED`
- **THEN** 该步骤起点位于新的一轮内，其 `round_id` 大于上一步骤各轮的 `round_id`

## ADDED Requirements

### Requirement: 步骤起点与运行提醒可读

事件项的展示文本 SHALL 覆盖新增的三类事件：步骤起点 MUST 展示步骤名与该步第几次尝试；运行时注入提醒 MUST 展示提醒全文，MUST NOT 截断；推理轮次用尽 MUST 给出一句可读说明。三类事件的标题 MUST 为可读中文，MUST NOT 直接暴露事件类型名。明细仍 MUST 只去掉回车符与首尾空白，MUST NOT 追加省略号。缺少步骤名或尝试次数时 MUST 只展示已有的部分，MUST NOT 打印 `None`。

#### Scenario: 步骤起点给出步骤与尝试次数

- **WHEN** 一条步骤起点事件的步骤名为「打开设置」、尝试次数为 2
- **THEN** 该事件项的明细为「打开设置 · 第 2 次尝试」，标题为可读中文而非 `SOP_STEP_STARTED`

#### Scenario: 运行提醒全文下发

- **WHEN** 一条运行时注入提醒的正文为 500 字
- **THEN** 该事件项的明细与该正文逐字相同，长度不小于 500，且不以省略号结尾

#### Scenario: 推理轮次用尽有可读说明

- **WHEN** 一条推理轮次用尽事件进入报告
- **THEN** 该事件项有非空的可读明细，且标题为可读中文
