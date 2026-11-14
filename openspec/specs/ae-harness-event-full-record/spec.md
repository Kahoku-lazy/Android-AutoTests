# ae-harness-event-full-record Specification

## Purpose
把事件流里框架已经给出、但被丢弃的信息补进运行产物，并提供一个默认开启的「全量模式」：字段齐全、块级折叠、不硬截断，使事后排查不必再靠重跑。

## Requirements

### Requirement: 全量模式开关默认开启

事件记录器 MUST 接受一个记录保真度开关，默认值 MUST 为开启。开关为开启时按下述各条补齐字段与取消截断；关闭时行结构与字段 MUST 与引入本变更前一致。

#### Scenario: 默认开启

- **WHEN** 调用方不显式传该开关
- **THEN** 记录按全量模式产出

#### Scenario: 关闭后回到旧结构

- **WHEN** 调用方显式关闭该开关
- **THEN** 事件行不新增 `created_at` / `event_id` / `session_id` / `source` / `text` 等字段
- **AND** 思考与工具输出重新按原长度上限截断

### Requirement: 逐条补齐框架已提供的公共字段

全量模式下，每条事件行 MUST 带上框架给出的发生时刻与事件唯一标识；框架给出非空 `metadata` 时 MUST 一并记录。

绝对时刻 MUST 直接取自框架，MUST NOT 再用运行起点与相对偏移推算。

#### Scenario: 事件行带绝对时刻与事件标识

- **WHEN** 全量模式记录任意一条事件
- **THEN** 该行含 `created_at`（框架时间）与 `event_id`
- **AND** 框架该事件没有给出时间或标识时不写空字段

#### Scenario: 元数据非空才写

- **WHEN** 事件带非空 `metadata`
- **THEN** 该行记录 `metadata` 的内容

### Requirement: 补齐回复与提示块的作用域字段

全量模式下，回复开始与结束的事件行 MUST 带该次回复的会话标识；提示块事件行 MUST 带提示来源标签。

#### Scenario: 回复行带会话标识

- **WHEN** 记录 `ReplyStartEvent` 或 `ReplyEndEvent`
- **THEN** 该行含 `session_id`

#### Scenario: 提示块行带来源

- **WHEN** 记录提示块事件
- **THEN** 该行同时含 `hint` 与 `source`

### Requirement: 文本块记录最终文本

全量模式下，文本块结束事件行 MUST 记录该块的最终文本（可为空串）。非全量模式 MUST NOT 记录该字段。

#### Scenario: 记录文本块最终文本

- **WHEN** 收到文本块结束事件
- **THEN** 该行含 `text`，值为该块最终文本

### Requirement: 全量模式不硬截断思考与工具输出

全量模式下，思考块与工具结果的正文 MUST NOT 被长度上限截断，MUST 保留原文。非全量模式 MUST 继续按原上限截断。

#### Scenario: 思考全文保留

- **WHEN** 一段思考文本超过原上限
- **THEN** 全量模式下该行保留全文
- **AND** 非全量模式下仍按原上限截断

#### Scenario: 工具输出全文保留

- **WHEN** 一次工具结果输出超过原上限
- **THEN** 全量模式下该行保留全文
- **AND** 非全量模式下仍按原上限截断

### Requirement: 全量模式仍按块级折叠

全量模式 MUST NOT 逐条落增量事件。文本、思考、工具调用参数与工具输出的增量 MUST 在内存累积，只落各自的块级结果。

#### Scenario: 增量事件不单独成行

- **WHEN** 某轮产生 100 条思考增量
- **THEN** 产物中不出现 100 条增量行
- **AND** 只出现对应的思考块结果行

### Requirement: 块级行始终带关联键

工具调用行与工具结果行 MUST 带该次调用的标识，使两者可按标识配对，MUST NOT 只靠顺序配对。

创作块行（思考、文本）MUST 带该块在框架侧的标识，使行可回溯到原始事件。

这些关联键 MUST 与全量开关无关、始终写入：它们标识身份，不是可选补充。

#### Scenario: 调用与结果按标识配对

- **WHEN** 一次模型调用要求调用工具，随后工具返回结果
- **THEN** 调用行与结果行携带同一个工具调用标识
- **AND** 消费方据此把入参与输出配成一对

#### Scenario: 块行可回溯

- **WHEN** 记录一个思考块或文本块的结束行
- **THEN** 该行带该块的标识
- **AND** 同一标识在同一批事件里唯一

#### Scenario: 关闭全量仍带关联键

- **WHEN** 记录器以非全量模式运行
- **THEN** 调用行、结果行、块行仍带上述标识

### Requirement: 补齐不引入后端依赖、不改变观测行

字段补齐 MUST 在既有事件记录层完成，MUST NOT 引入 Django、后端应用或网络调用。

观测中间件产生的记录行 MUST NOT 受本开关影响。

#### Scenario: 观测行保持原结构

- **WHEN** 全量模式下同时存在观测记录
- **THEN** 观测行的字段集合与非全量模式相同
