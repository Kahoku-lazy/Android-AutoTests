## MODIFIED Requirements

### Requirement: 基本角色经 YAML 五段与 Factory 创建

基本 LLM 角色的可运行实例 SHALL 由以下要素组成并装配：角色节中的模型短名（连接参数止于模型创建层）与 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`（Harness 四分段）。创建 SHALL 经 `engines.agents.assistant` 的唯一出口完成，并生成 `agentscope.agent.Agent`。对外 SHALL 继续提供每次调用返回新实例的 `build_*` 入口，且该入口 MUST 转调 assistant；MUST NOT 跨任务共享同一 Agent 对话状态。

#### Scenario: UI 执行角色创建

- **WHEN** 调用方请求创建 UI 执行角色（如 `build_ui_executor()`）
- **THEN** 系统从 `agent_config.yaml` 的对应 `*_ROLE_CONFIG` 装载模型短名与四分段，经 assistant 创建 Agent，并挂载由 `tools_config` 提供的执行工具包

#### Scenario: 用例编写角色创建

- **WHEN** 调用方请求创建用例编写类角色（如 `build_case_writer()`）
- **THEN** 系统经同一 assistant 出口创建新 Agent，工具包来自 `tools_config` 的用例侧 API

### Requirement: N1 ModelConfig 不进入 Agent

角色节中的模型短名 SHALL 仅用于经 `engines.agents.models_new` 创建模型对象。交予 `agentscope.agent.Agent` 的 SHALL 仅为已创建的 `ChatModelBase`（或等价 model 对象）。`Agent` 的构造参数与对外运行面 MUST NOT 接收、持有或要求调用方传入 `ModelConfig` 或模型连接参数。assistant 内部可短暂持有角色节，但 MUST 仅用于取短名与四分段，MUST NOT 自己读取密钥。

#### Scenario: Agent 构造只接收 model 对象

- **WHEN** assistant（或转调它的 `build_*`）装配基本 LLM 角色
- **THEN** 传入 `Agent(...)` 的是已创建的聊天模型对象，而不是 `ModelConfig` 实例

#### Scenario: 调用方不向 Agent 泄漏 ModelConfig

- **WHEN** 业务代码经 `build_*` 获取 Agent
- **THEN** 返回的 Agent 实例对外不暴露需调用方继续消费的 `ModelConfig` 字段作为装配契约

### Requirement: Realtime Omni 不在基本角色路径内

DashScope Omni 实时语音角色 MUST 经 `engines.agents.assistant` 的同一创建出口装配，返回 `RealtimeAgent`，MUST NOT 要求使用 LLM 的 `AgentRoleFactory` 作为其构造器。会话实现 MUST 继续落在 `engines.agents.realtime_vocie`。本能力的 LLM 四分段要求 MUST NOT 被解释为强制把 Omni 角色改造成聊天 `Agent`。旧模块 `realtime_vocie_agent` 若仍被调用，MUST 转调 assistant，MUST NOT 再直接构造 `RealtimeAgent`。

#### Scenario: 语音角色走 assistant 而非聊天构造器

- **WHEN** 调用方创建 Omni 实时语音助手
- **THEN** 创建经 assistant 完成并返回实时语音智能体，而不是 `build_ui_*` / `build_case_*` 那类聊天角色

#### Scenario: 旧语音入口不再自己构造

- **WHEN** 调用方仍使用 `realtime_vocie_agent` 的创建函数
- **THEN** 该函数转调 assistant，函数体内不再出现 `RealtimeAgent(...)`
