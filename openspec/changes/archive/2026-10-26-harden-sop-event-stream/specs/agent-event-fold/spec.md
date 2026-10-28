# agent-event-fold 变更

## MODIFIED Requirements

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

## ADDED Requirements

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
