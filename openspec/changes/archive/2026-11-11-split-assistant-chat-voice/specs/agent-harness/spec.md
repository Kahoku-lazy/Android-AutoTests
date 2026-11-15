## MODIFIED Requirements

### Requirement: 角色经 AgentRoleFactory 装配

新增或修改可运行的 **LLM** 智能体角色时，创建实现 MUST 走聊天助手出口，并只接受聊天模型；对外仍 SHALL 提供每次调用返回独立 `agentscope.agent.Agent` 实例的 `build_*` 入口（不跨任务共享对话状态）。`build_*` MUST 转调聊天出口，MUST NOT 再按模型实例类型选择语音智能体。四分段配置类型的定义 MUST 落在不依赖装配模块的类型模块中。交予聊天智能体的模型 SHALL 为已创建的 `ChatModelBase`（或等价），MUST NOT 将 `ModelConfig` 作为构造契约。

实时语音角色的创建 MUST 走语音助手出口，并只接受实时语音模型。会话循环、音频传输与 `reply_stream` SHALL 留在 `engines.agents.realtime_vocie`，MUST NOT 留在助手创建层。`engines.agents.realtime_vocie_agent` 若保留，只作为转调语音出口的兼容名字。

#### Scenario: 新增设备或用例类角色

- **WHEN** 开发者新增一个可运行 LLM 角色
- **THEN** `build_*() -> Agent` 经聊天助手出口创建，不经「先造模型再看类型」的混合出口

#### Scenario: 新增语音角色

- **WHEN** 开发者新增 Omni 实时语音能力
- **THEN** 创建走语音助手出口；会话仍在 `realtime_vocie`，不恢复已删除的 livetranslate/pipeline 模式

#### Scenario: 四分段类型可被装载器独立引用

- **WHEN** 装载入口构造 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`
- **THEN** 装载实现不 import 聊天助手创建模块

#### Scenario: Agent 不接收 ModelConfig

- **WHEN** 聊天出口完成基本 LLM 角色创建
- **THEN** 聊天智能体收到的是聊天模型对象，而非 `ModelConfig`

#### Scenario: 语音模型不能进入聊天出口

- **WHEN** `build_*` 所读角色节引用的模型族为 realtime
- **THEN** 创建失败，不返回 `RealtimeAgent`
