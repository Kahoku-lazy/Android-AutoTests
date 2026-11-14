## Purpose

把 AgentScope 中间件里「事件流看不到」的两处信息（上下文是否被压缩、本轮最终 system prompt）采样出来，并随既有运行产物落盘，使「智能体运行中做了什么」在关键处不断档。

## ADDED Requirements

### Requirement: 观测中间件只读，不改变任何行为

观测中间件 MUST 只在 hook 上采样。它 MUST NOT 改变入参、返回值和上下文；对 Onion 型 hook MUST 调用 `next_handler`；对变换式 hook MUST 原样返回收到的值。

观测中间件 MUST NOT 做能力型行为：不重试、不路由、不换模型、不注册工具、不改权限判定、不写智能体状态、不发网络请求、不写文件。

#### Scenario: 变换式 hook 原样透传

- **WHEN** `on_system_prompt` 收到一段 system prompt 文本
- **THEN** 返回值与收到的文本逐字符相同

#### Scenario: Onion 型 hook 必须调用下游

- **WHEN** `on_compress_context` 被调用
- **THEN** 下游 handler 恰好被调用一次
- **AND** 压缩结果与不挂该中间件时一致

#### Scenario: 中间件不提供工具

- **WHEN** 检查该中间件是否实现 `list_tools`
- **THEN** 未实现，不向智能体贡献任何工具

### Requirement: 记录一次上下文压缩的发生与结果

`on_compress_context` MUST 产生一条观测记录，至少包含：发生时间、调用前后的上下文消息条数、本次生效的触发比例与上下文窗口、由两者算出的阈值、是否实际发生了压缩（前后条数是否变化）、本次压缩耗时。

调用方传入压缩指令时，记录 MUST 包含该指令的文本（过长可截断）；未传入时 MUST 明确表示为空。

#### Scenario: 未达阈值不压缩

- **WHEN** 上下文条数在压缩前后相同
- **THEN** 记录中「是否压缩」为假
- **AND** 仍记录触发比例、上下文窗口与阈值

#### Scenario: 达到阈值发生压缩

- **WHEN** 上下文条数在压缩后减少
- **THEN** 记录中「是否压缩」为真
- **AND** 记录同时给出压缩前后的条数

### Requirement: 记录本轮最终 system prompt 全文

`on_system_prompt` MUST 产生一条观测记录，至少包含：发生时间、该次 system prompt 的全文与字符长度。

按需求方决定，全文**不做截断**落盘；由此带来的产物体积增长属明确取舍，MUST NOT 因此丢弃或摘要该字段。

#### Scenario: 每轮一条且内容完整

- **WHEN** 一次回复经历多轮推理
- **THEN** 每一轮各产生一条记录
- **AND** 每条记录的文本与当轮实际组装的 system prompt 完全一致

### Requirement: 观测记录随运行产物落盘

观测记录 MUST 写进该次运行既有的 JSONL 产物，并与事件行可区分（事件类型字段不同）。记录 MUST 同时可从该次运行的记录对象读取，使调用方不必解析文件。

未挂观测中间件时，产物的行集合 MUST 与未引入本变更前一致。

#### Scenario: 记录进入既有产物

- **WHEN** 一次运行挂了观测中间件并产生观测记录
- **THEN** JSONL 中出现对应行
- **AND** 这些行不与既有事件行的类型混淆

#### Scenario: 不挂中间件时产物不变

- **WHEN** 一次运行未挂观测中间件
- **THEN** JSONL 不含任何观测行
- **AND** 其余行与改造前一致

### Requirement: 观测中间件只经显式观测入参装配

观测中间件 MUST 只经角色创建出口的**显式观测入参**传入；该入参 MUST 与能力型中间件的入参分开命名，MUST NOT 复用同一个参数名。

不传该入参时，角色与运行行为 MUST 与改造前一致。

#### Scenario: 经观测入参传入

- **WHEN** 调用方以观测入参传入一个观测中间件
- **THEN** 该中间件被装配到智能体上并收到 hook 调用

#### Scenario: 不传观测入参

- **WHEN** 调用方不传观测入参
- **THEN** 智能体照常创建与运行
- **AND** 不产生任何观测记录

### Requirement: 采集不引入后端依赖

观测实现 MUST 限定在 `engines/ae_harness/middleware/` 内，MUST NOT 引入 Django、后端应用或网络调用；MUST NOT 读取密钥明文或配置表。

观测层 MUST 不导入同包其它模块；采集结果的投递 MUST 只经调用方提供的回调或其自有容器，MUST NOT 直接操作事件层的落盘。

#### Scenario: 无后端环境可运行

- **WHEN** 在未安装 Django、无数据库的环境里运行
- **THEN** 观测记录照常产出

#### Scenario: 观测层不依赖同包模块

- **WHEN** 审查 `middleware/` 下模块的导入
- **THEN** 没有任何同包导入（`engines.ae_harness.*`）
