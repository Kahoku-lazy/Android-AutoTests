# single-agent-chat Specification

## Purpose
让用户在助手页选一张单智能体编排卡片后直接对话。事件由该智能体自己的中间件观察，设备操作前必须选定当前设备。

## Requirements

### Requirement: 选择卡片后与该智能体对话

用户选择一张单智能体编排卡片后，发送的消息 MUST 交给该编排的唯一智能体，MUST NOT 直接发给裸模型。未选择卡片时 MUST NOT 发送。同一连接内 MUST 复用同一个智能体实例，以保留多轮上下文。

#### Scenario: 选中 Android UI 控制后发送

- **WHEN** 用户选中「Android UI 控制」并发送一条消息，且已选定设备
- **THEN** 回复来自 UI 执行智能体
- **AND** 同一连接的下一条消息仍进入同一个实例

### Requirement: 事件由单智能体中间件观察

单智能体的过程事件 MUST 由挂在该智能体上的 `on_reply` 中间件观察，并交给现有事件接收方。该中间件 MUST NOT 挂到 SOP 的执行者或验收者上。SOP 的事件消费 MUST 保持原样。

#### Scenario: 一次回复的模型事件被看见

- **WHEN** Android UI 控制完成一次回复
- **THEN** 中间件观察到该回复中的模型事件
- **AND** SOP 运行的事件记录没有因此多出一条

### Requirement: 操作设备前必须有当前设备

Android UI 控制在会操作设备的对话开始前 MUST 收到一个设备序列号。未选设备时系统 MUST 拒绝发送，并说明需要先选设备。序列号 MUST 进入该智能体当轮可见的上下文，而不是另写一套设备工具。

#### Scenario: 未选设备

- **WHEN** 用户未选设备就向 Android UI 控制发送消息
- **THEN** 消息不被执行，界面说明需要先选择设备

#### Scenario: 已选设备

- **WHEN** 用户选择一台当前可用设备后再发送
- **THEN** 智能体收到的上下文包含该设备序列号
