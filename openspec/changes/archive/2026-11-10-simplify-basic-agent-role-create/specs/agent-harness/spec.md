## MODIFIED Requirements

### Requirement: 角色经 AgentRoleFactory 装配

新增或修改可运行的 **LLM** 智能体角色时，SHALL 使用 `engines.agents.agent_builders.AgentRoleFactory`（配合 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`）装配 Model 与 toolkit；SHALL 提供每次调用返回独立 `agentscope.agent.Agent` 实例的 `build_*` 入口（不跨任务共享对话状态）。四分段配置类型的定义 MUST 落在不依赖 `AgentRoleFactory` 装配模块的类型模块中，供装载器与 Factory 共同引用。交予 Agent 的模型 SHALL 为已创建的 `ChatModelBase`（或等价），MUST NOT 将 `ModelConfig` 作为 Agent 构造契约。语音 Omni 角色 SHALL 使用 `engines.agents.realtime_vocie_agent`，会话实现落在 `engines.agents.realtime_vocie`。

#### Scenario: 新增设备或用例类角色

- **WHEN** 开发者新增一个可运行 LLM 角色
- **THEN** 实现位于 `engines/agents/agent_builders.py`（或同包新增 builder 模块），经 `AgentRoleFactory(...).create()` 暴露 `build_*() -> Agent`

#### Scenario: 新增语音角色

- **WHEN** 开发者新增 Omni 实时语音能力
- **THEN** 装配入口在 `realtime_vocie_agent.py`，提示词经 `role_sys_prompts.VoiceKnowledgePrompts`，会话不恢复已删除的 livetranslate/pipeline 模式

#### Scenario: 四分段类型可被装载器独立引用

- **WHEN** `load_role_spec`（或等价装载入口）构造 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`
- **THEN** 装载实现不 import `AgentRoleFactory` 所在装配模块

#### Scenario: Agent 不接收 ModelConfig

- **WHEN** Factory 完成基本 LLM 角色装配
- **THEN** `Agent(...)` 收到的是聊天模型对象，而非 `ModelConfig`

### Requirement: 模型配置唯一装载入口

聊天 / 实时模型连接参数 SHALL 经 `engines.agents.config.role_loader`（`ModelConfig` / `ChatModelFactory` / `load_role_spec` / Omni 装载器）从 `config/data/agent_config.yaml` 读取。现成短名目录（`get_text` / `get_realtime` / `get_embedding` / `DeepSeekModelConfig`）亦由该模块提供。`load_role_spec` SHALL 返回可直接交给 `AgentRoleFactory` 的 Model + 四分段五元组，且 MUST NOT 为构造四分段而依赖装配模块。`ModelConfig` MUST 止于建模型管线，MUST NOT 成为 Agent 对外构造参数。MUST NOT 再使用已删除的 `engines.agents.role.models`。

#### Scenario: 装载执行角色模型

- **WHEN** 调用 `load_role_spec("UI_EXECUTOR_ROLE_CONFIG")` 或 `build_ui_executor()`
- **THEN** ModelConfig 与四分段来自 `agent_config.yaml`，经 `config.role_loader` 装载

#### Scenario: 装载与装配单向依赖

- **WHEN** 检查 `engines.agents.config.role_loader` 对装配入口模块的依赖
- **THEN** 不存在为角色创建服务的对 `agent_builders` 的导入（类型来自独立类型模块）

## ADDED Requirements

### Requirement: 基本角色创建清单与复杂度可追溯

针对「基本 LLM 角色创建」的简化或重构变更，SHALL 在 OpenSpec 变更或 `temps/` 分析中保留当前 create 调用链说明（含 YAML → load_role_spec → Factory → build_*），并引用 `temps/agents_architecture.md`（或其后继）与 `GUIDE-创建Agent清单.md`。变更 MUST NOT 在同一变更中捆绑 realtime 重命名、middleware 策略统一化、**skills 产品扩展**、或 workflow 对 `tool_*` 的旁路清理，除非该变更的 proposal 显式扩大范围。

#### Scenario: SPEC-1 范围隔离

- **WHEN** 归档或评审「简化基本 Agent 角色创建」类变更
- **THEN** 可定位到 create 链分析文档，且 proposal 的 Non-goals 排除 realtime / middleware 统一 / skills / workflow tool 旁路

### Requirement: Harness 四分段留在配置层且 skills 延后

Harness 四分段（Role / Tools / Context / ReAct）SHALL 一对一管理、链路不交叉，并留在 Agent 配置/装载层；无特殊需求 MUST NOT 作为稳定对外公共 API。`ToolsConfig` 的 skills 扩展 SHALL 视为后续变更，本期基本角色简化 MUST NOT 以交付 skills 为验收条件。

#### Scenario: 对外以 build_* 为主

- **WHEN** 调用方需要可运行 LLM 角色
- **THEN** 推荐入口为 `build_*` → `Agent`，而非将四分段配置当作稳定公共 SDK

#### Scenario: skills 延后

- **WHEN** 评审本期基本角色创建简化
- **THEN** Non-goals / tasks 标明 skills 后续处理，且无必做 skills 实现项
