## MODIFIED Requirements

### Requirement: 角色经 AgentRoleFactory 装配

新增或修改可运行的智能体角色（含 LLM 与 Omni 实时语音）时，SHALL 经 `engines.agents.assistant` 的唯一创建出口装配：调用方传入已读好的角色表与模型表，以及角色键；模型实例 MUST 由 `engines.agents.models_new` 按短名创建后再交给智能体。SHALL 仍提供每次调用返回独立实例的 `build_*` 入口（不跨任务共享对话状态）；这些入口 MUST 转调 assistant，MUST NOT 再直接构造 `Agent` 或 `RealtimeAgent`。四分段配置类型的定义 MUST 落在不依赖装配模块的类型模块中。交予聊天智能体的模型 SHALL 为已创建的 `ChatModelBase`（或等价），MUST NOT 将 `ModelConfig` 作为智能体构造契约。语音会话实现仍 SHALL 落在 `engines.agents.realtime_vocie`，但该包 MUST NOT 再内联构造 `RealtimeAgent`。

#### Scenario: 新增设备或用例类角色

- **WHEN** 开发者新增一个可运行 LLM 角色
- **THEN** 创建经 `engines.agents.assistant` 完成，`agent_builders` 的 `build_*` 只转调该出口并返回新的 `Agent`

#### Scenario: 新增语音角色

- **WHEN** 开发者新增 Omni 实时语音能力
- **THEN** 创建同样经 `engines.agents.assistant` 完成，会话仍在 `realtime_vocie`，且不恢复已删除的 livetranslate/pipeline 模式

#### Scenario: 四分段类型可被装载器独立引用

- **WHEN** 角色装载构造 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`
- **THEN** 装载实现不 import assistant 创建出口，也不 import `AgentRoleFactory` 所在装配模块

#### Scenario: Agent 不接收 ModelConfig

- **WHEN** assistant 完成基本 LLM 角色装配
- **THEN** `Agent(...)` 收到的是聊天模型对象，而非 `ModelConfig`

#### Scenario: 会话不再内联构造语音智能体

- **WHEN** 语音会话需要一个 Omni 智能体
- **THEN** 实例来自 assistant 创建出口，`realtime_vocie/session.py` 内不再出现 `RealtimeAgent(...)`
