# agent-event-fold Specification

## Purpose

把一轮智能体回复的事件流折成有序的结构化记录，并与既有文本日志共用同一次 8 位费用，供后续轨迹入库使用。本能力不写数据库。

## Requirements

### Requirement: 文本日志与结构化记录一起交出
处理一条事件时，系统 MUST 继续按既有动作口径写文本日志，并在该事件需要落记录时交出一条结构化记录。文本日志 MUST 仍能写出这些动作：开始、结束、本轮执行时间、本轮执行总计量、思考、工具调用、工具返回、模型 token、模型费用、步骤开始、运行时提醒、推理轮次用尽。正文块结束 MUST NOT 另写一行文本日志。类型名为 `CustomEvent` 的事件 MUST 只在名称为 `SOP_STEP_STARTED` 时写一行「步骤开始」并交出一条记录；其它名称的 `CustomEvent` MUST NOT 写文本日志，也 MUST NOT 交出记录。未绑定接收方时，记录 MUST 被丢弃，文本日志与本次运行 MUST 照常继续。接收方抛错时 MUST 只记警告，MUST NOT 因此中断本次运行。本能力 MUST NOT 写入数据库，也 MUST NOT 依赖应用层模块完成折叠。

#### Scenario: 未绑定接收方仍写出开始行
- **WHEN** 没有绑定接收方，且到达一条类型名为 `ReplyStartEvent` 的事件
- **THEN** 文本日志写出开始动作与角色名，运行不中断，且没有数据库写入

#### Scenario: 步骤起点写一行并交出记录
- **WHEN** 到达一条名称为 `SOP_STEP_STARTED` 的 `CustomEvent`，其值为「步骤名=打开设置，第几次尝试=2」
- **THEN** 文本日志写出一行「步骤开始」，并交出一条事件类型名为 `SOP_STEP_STARTED` 的记录

#### Scenario: 步骤边界被忽略
- **WHEN** 到达一条名称为 `SOP_STEP_ENDED` 的 `CustomEvent`
- **THEN** 不写文本日志，也不交出记录

### Requirement: 模型费用只算一次并同时出现在日志和记录里
类型名为 `ModelCallEndEvent` 的事件 MUST 只计算一次输入费用、输出费用与缓存命中费用。文本日志中的模型费用行与该条结构化记录 MUST 逐项使用这同一组数，精度为小数点后 8 位。费用行 MUST 以普通十进制带「元」打印这 8 位，MUST NOT 再收成 4 位。未登记模型的三项费用 MUST 为 0.00000000 元，token 行仍写出实际用量。同一次发言结束时的本轮费用合计 MUST 等于该轮各次调用这组 8 位数之和。

#### Scenario: 日志与记录的费用逐项相同
- **WHEN** 一次 `deepseek-flash` 调用在空闲时段结束，输入 1000 token、输出 0、缓存命中 1000 token
- **THEN** 文本日志的模型费用与交出的记录都是输入 0.00000000 元、输出 0.00000000 元、缓存命中 0.00002000 元

#### Scenario: 本轮合计等于各次调用之和
- **WHEN** 同一轮发言内先后结束两次模型调用，费用分别已按 8 位取好
- **THEN** 发言结束时写出的本轮费用合计等于这两次三项费用分别相加，且不再按 4 位重算

### Requirement: 记录带阶段与块类型
每条交出的记录 MUST 带事件类型名、阶段与块类型。阶段 MUST 为「开始」「推理」「执行」「结束」之一。块类型 MUST 为 `reply`、`model_call`、`text`、`thinking`、`data`、`tool_call`、`tool_result`、`sop_step`、`hint` 之一。调用方 MUST 能只靠阶段与块类型区分记录，而不必再解析事件类型名。对应关系 MUST 为：`ReplyStartEvent` 为开始/`reply`；`ReplyEndEvent` 为结束/`reply`；模型调用与文本、思考、数据、工具调用为推理，块类型分别是 `model_call`、`text`、`thinking`、`data`、`tool_call`；工具返回为执行/`tool_result`；`SOP_STEP_STARTED` 为开始/`sop_step`；`HintBlockEvent` 为推理/`hint`；`ExceedMaxItersEvent` 为结束/`hint`。

#### Scenario: 发言开始记录标为开始
- **WHEN** 到达 `ReplyStartEvent`
- **THEN** 交出的记录阶段为开始，块类型为 `reply`，事件类型名为 `ReplyStartEvent`

#### Scenario: 工具返回记录标为执行
- **WHEN** 到达 `ToolResultEndEvent` 并交出记录
- **THEN** 该记录阶段为执行，块类型为 `tool_result`

#### Scenario: 步骤起点记录标为开始且块类型为 sop_step
- **WHEN** 到达名称为 `SOP_STEP_STARTED` 的 `CustomEvent`
- **THEN** 该记录阶段为开始，块类型为 `sop_step`

### Requirement: 聚合增量不成条，结束事件成一条
`TextBlockDeltaEvent`、`ThinkingBlockDeltaEvent`、`DataBlockDeltaEvent` 与 `ToolResultDataDeltaEvent` MUST NOT 各自交出记录，内容 MUST 按块累积。对应的结束事件 MUST 交出一条记录：文本或思考带拼好的全文与增量条数；数据块带媒体类型与拼好的 base64。`TextBlockStartEvent`、`ThinkingBlockStartEvent`、`DataBlockStartEvent`、`ModelCallStartEvent`、`ToolCallStartEvent`、`ToolResultStartEvent` MUST NOT 交出记录。结束记录 MUST 带该块的开始时刻与结束时刻。`ModelCallStartEvent` 上的模型名 MUST 写入本轮状态，供随后的 `ModelCallEndEvent` 记录使用。

#### Scenario: 文本增量合并成一条
- **WHEN** 同一正文块先到两条 `TextBlockDeltaEvent`，再到 `TextBlockEndEvent`
- **THEN** 只在结束时交出一条记录，正文为两段增量按到达顺序拼接，增量条数为 2，且不为这两条增量各写文本日志

#### Scenario: 模型名从调用开始带到调用结束
- **WHEN** `ModelCallStartEvent` 带有模型名，随后到达没有模型名的 `ModelCallEndEvent`
- **THEN** 调用开始不交出记录，调用结束交出的记录使用该模型名

### Requirement: 工具入参与返回文本逐条成记录
`ToolCallDeltaEvent` 与 `ToolResultTextDeltaEvent` MUST 每条交出一条记录，带本次增量文本与该块内从 0 起的序号，并标为增量。`ToolCallEndEvent` MUST 交出一条记录，工具名来自对应的开始事件，入参为各增量按序拼接。`ToolResultEndEvent` MUST 交出一条记录，工具名来自对应的开始事件，状态来自该结束事件，返回文本为各文本增量按序拼接。文本日志仍 MUST 在调用结束与返回结束时各写一行全文，MUST NOT 为每一条工具增量另写一行。

#### Scenario: 入参增量逐条交出
- **WHEN** 同一次工具调用先到 `ToolCallStartEvent`，再连续到达两条 `ToolCallDeltaEvent`，最后到 `ToolCallEndEvent`
- **THEN** 开始事件不交出记录，两条增量各交出一条且序号为 0 和 1，结束记录的入参为这两段按序拼接，文本日志只有结束时的那一行工具调用

#### Scenario: 返回文本增量逐条交出
- **WHEN** 同一次工具返回先到 `ToolResultStartEvent`，再到一条 `ToolResultTextDeltaEvent`，最后到 `ToolResultEndEvent`
- **THEN** 文本增量交出一条记录，结束记录的返回文本等于该增量，状态为结束事件上的状态

### Requirement: 一轮发言内继承角色
`ReplyStartEvent` 上的名称 MUST 作为该轮 `role_name`。该轮内随后交出的记录 MUST 带上同一个 `role_name`。`role_kind` MUST 按名称映射：`executor_role` 为 `executor`，`verifier_role` 为 `verifier`，`planner_role` 为 `planner`；其它名称的 `role_kind` MUST 为空字符串。新的 `ReplyStartEvent` MUST 结束上一轮的角色继承。

#### Scenario: 执行者发言内的工具记录带同一角色
- **WHEN** `ReplyStartEvent` 的名称为 `executor_role`，随后在该轮内交出一条工具调用结束记录
- **THEN** 两条记录的 `role_name` 都是 `executor_role`，`role_kind` 都是 `executor`

#### Scenario: 下一轮发言更换角色
- **WHEN** 一轮 `executor_role` 结束后，下一条 `ReplyStartEvent` 的名称为 `verifier_role`
- **THEN** 其后交出的记录 `role_name` 为 `verifier_role`，`role_kind` 为 `verifier`

### Requirement: 图片内容不进文本日志
工具返回中的图片增量 MUST NOT 把 base64 原文写入文本日志；日志 MUST 仍只记录媒体类型与 base64 长度。这些增量 MUST 在内存中按到达顺序拼接，并在对应的 `ToolResultEndEvent` 记录上把媒体类型与完整 base64 交给接收方。`DataBlockDeltaEvent` 的 base64 MUST 同样只在 `DataBlockEndEvent` 的记录上交出。文本日志 MUST NOT 包含这段 base64 原文。

#### Scenario: 截图返回只在记录里带完整 base64
- **WHEN** 一次工具返回含若干 `ToolResultDataDeltaEvent`，媒体类型为 `image/png`，随后到达 `ToolResultEndEvent`
- **THEN** 文本日志只含媒体类型与 base64 长度，结束记录交给接收方的是按序拼好的完整 base64，且日志正文不含该 base64

### Requirement: SOP 步骤起点成记录
名称 `SOP_STEP_STARTED` 的事件 MUST 交出一条记录，载荷 MUST 带该步的步骤名与这是该步第几次尝试。步骤起点不属于任何一轮发言，其记录上的角色名、角色类别与模型名 MUST 为空字符串，MUST NOT 继承上一条记录的取值。名称 `SOP_STEP_ENDED` 的事件 MUST NOT 交出记录：步骤终点由下一个步骤起点或整次运行结束表达。步骤起点 MUST NOT 清空本轮已累积的正文、思考、工具入参或用量状态。

#### Scenario: 步骤起点不带上一轮的角色与模型
- **WHEN** 上一轮发言的角色为 `executor_role`、模型为 `deepseek-flash`，随后到达一条 `SOP_STEP_STARTED`
- **THEN** 该记录的角色名、角色类别与模型名都为空字符串

#### Scenario: 步骤终点不落记录
- **WHEN** 到达一条名称为 `SOP_STEP_ENDED`、值为「阶段=completed」的 `CustomEvent`
- **THEN** 不交出任何记录

### Requirement: 运行提醒与超轮次成记录
类型名为 `HintBlockEvent` 的事件 MUST 交出一条记录，载荷 MUST 带该次注入的提醒全文与来源，提醒全文 MUST NOT 被截断或改写。类型名为 `ExceedMaxItersEvent` 的事件 MUST 交出一条记录，用于说明该次发言因推理轮次用尽被强制收尾。这两类记录 MUST 沿用本轮已记住的角色与模型名，MUST NOT 各自新开一轮。事件流里 MUST 至少留下其中一条记录，使「模型为何在该轮停止」可由事件表单独判定，而不必借助进程日志。

#### Scenario: 提醒全文进入载荷
- **WHEN** 到达一条 `HintBlockEvent`，其提醒正文为 500 字
- **THEN** 交出的记录载荷里提醒正文与原正文逐字相同，长度不小于 500

#### Scenario: 超轮次可被事件表判定
- **WHEN** 一次发言因推理轮次用尽被强制收尾，事件流随后到达 `ExceedMaxItersEvent`
- **THEN** 交出一条事件类型名为 `ExceedMaxItersEvent`、阶段为结束的记录，且该记录的模型名与本轮一致
