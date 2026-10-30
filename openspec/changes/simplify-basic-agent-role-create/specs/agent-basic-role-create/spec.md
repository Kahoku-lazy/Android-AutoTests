## Purpose

定义平台「基本 LLM Agent 角色」的创建路径与模块边界：从 `agent_config.yaml` 装载 Model + 四分段 Harness 配置，经 `AgentRoleFactory` 与 `build_*` 得到独立 `agentscope.agent.Agent` 实例；按三节点（N1 ModelConfig 防火墙 / N2 Harness 1:1 / N3 Agent=角色 vs workflow）验收。不含 realtime Omni、middleware 统一化、**skills**、workflow `tool_*` 旁路清理。

## ADDED Requirements

### Requirement: 基本角色经 YAML 五段与 Factory 创建

基本 LLM 角色的可运行实例 SHALL 由以下要素组成并装配：`ModelConfig`（模型连接，止于建模型）与 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`（Harness 四分段），经 `AgentRoleFactory(...).create()` 生成 `agentscope.agent.Agent`。对外 SHALL 提供每次调用返回新实例的 `build_*` 入口；MUST NOT 跨任务共享同一 Agent 对话状态。

#### Scenario: UI 执行角色创建

- **WHEN** 调用方请求创建 UI 执行角色（如 `build_ui_executor()`）
- **THEN** 系统从 `agent_config.yaml` 的对应 `*_ROLE_CONFIG` 装载 Model 与四分段，经 Factory 创建 Agent，并挂载由 `tools_config` 提供的执行工具包

#### Scenario: 用例编写角色创建

- **WHEN** 调用方请求创建用例编写类角色（如 `build_case_writer()`）
- **THEN** 系统同样经 `load_role_config`（或等价装载）与 Factory 创建新 Agent，工具包来自 `tools_config` 的用例侧 API

### Requirement: N1 ModelConfig 不进入 Agent

`ModelConfig` SHALL 仅用于约束/校验 YAML 并经 `ChatModelFactory`（或等价）创建聊天模型对象。交予 `agentscope.agent.Agent` 的 SHALL 仅为已创建的 `ChatModelBase`（或等价 model 对象）。`Agent` 的构造参数与对外运行面 MUST NOT 接收、持有或要求调用方传入 `ModelConfig`。Factory 内部可短暂持有 `ModelConfig`，但 MUST 仅用于建模型。

#### Scenario: Agent 构造只接收 model 对象

- **WHEN** `AgentRoleFactory.create`（或等价）装配基本 LLM 角色
- **THEN** 传入 `Agent(...)` 的是已创建的聊天模型对象，而不是 `ModelConfig` 实例

#### Scenario: 调用方不向 Agent 泄漏 ModelConfig

- **WHEN** 业务代码经 `build_*` 获取 Agent
- **THEN** 返回的 Agent 实例对外不暴露需调用方继续消费的 `ModelConfig` 字段作为装配契约

### Requirement: N2 四分段配置类型无循环依赖且 1:1

`RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig` 的定义模块 MUST NOT 依赖 `AgentRoleFactory` 所在装配模块；角色 YAML 装载模块（`engines.agents.config.models`）MUST NOT 为解析四分段而 import 装配模块。装配模块可以依赖类型模块与装载模块。各分段 MUST 字段职责 1:1、MUST NOT 把另一分段的字段写入本分段。四分段配置 SHALL 留在 Agent 配置/装载层；无特殊需求 MUST NOT 作为稳定对外公共 API（对外以 `build_*` → `Agent` 为主）。

#### Scenario: 装载模块可独立导入

- **WHEN** 仅导入角色 YAML 装载模块以调用 `load_role_config`
- **THEN** 导入成功且不需要先导入 `agent_builders` 装配入口

#### Scenario: 类型可被装载与装配双方使用

- **WHEN** 装载器构造四分段实例且 Factory 消费该实例
- **THEN** 双方引用同一类型定义模块，行为与字段默认值一致

#### Scenario: 分段不交叉

- **WHEN** 装载或构造任一四分段配置
- **THEN** 该分段不包含另一分段职责字段（例如 `RoleConfig` 不含 toolkit / ReAct 轮次；`ToolsConfig` 不含 system_prompt）

### Requirement: skills 不在本期基本角色创建变更内

本能力变更 MUST NOT 要求扩展 `ToolsConfig` 的 skills 字段或改变 skills 产品语义。skills SHALL 视为后续单独变更（Non-goal / deferred）。工具包本期仍 SHALL 经 `tools_config` 注入。

#### Scenario: 本期不交付 skills

- **WHEN** 评审或实现本 change 的 tasks
- **THEN** 无「为 ToolsConfig 增加 skills / 启用 skills 链路」的必做实现项

### Requirement: 工具经 tools_config 注入

基本角色创建路径中，设备或用例工具包 SHALL 由 `engines.agents.tools_config` 的 `build_*_toolkit`（或同等公开 API）提供，并在 `build_*` / Factory 组装时注入。YAML 中 `ToolsConfig` 为空时 MUST 视为空工具包占位，MUST NOT 在装载器内硬编码设备工具。业务代码 MUST NOT 为绑角色而直接 import `engines.agents.tools.tool_*`。

#### Scenario: YAML ToolsConfig 为空

- **WHEN** 某 `*_ROLE_CONFIG` 的 `ToolsConfig` 节为空
- **THEN** 装载结果为空白 Toolkit 占位，实际工具由对应 `build_*` 经 `tools_config` 注入

### Requirement: 提示词经 role_sys_prompts 解析

`RoleConfig.system_prompt` 为 prompts 目录下的短 token 时，SHALL 经 `engines.agents.role_sys_prompts.resolve_system_prompt` 读取 `config/data/prompts/*.md` 正文；多行正文 SHALL 原样使用。MUST NOT 在 backend View 或 `apps.*` 内硬编码整段角色 system prompt 以绕过该入口。

#### Scenario: token 解析为 md

- **WHEN** YAML 中 `system_prompt: UI_EXECUTOR_PROMPT`
- **THEN** 角色系统提示词正文等于对应 md 文件内容

### Requirement: N3 Agent 只提供角色；workflow 编排旁路清理延后

Agent SHALL 只作为已装配角色提供给编排层。workflow SHALL 经 `build_*`（或文档约定的等价入口）获取 Agent 再编排，MUST NOT 把 `ModelConfig` 或四分段配置当作编排 API 对外穿梭。本能力变更 MUST NOT 强制清理 workflow 对 `tool_*` / `tools_config` 的旁路或 create 后改 toolkit；该类清理 SHALL 属后续变更（Non-goal）。

#### Scenario: 编排消费角色实例

- **WHEN** workflow 需要 LLM 角色参与步骤
- **THEN** 编排侧持有/调用的是经 `build_*` 得到的 Agent 角色实例，而不是重新解析 YAML 五段作为编排参数

#### Scenario: 本期不做 tool 旁路清理

- **WHEN** 实现本 change
- **THEN** 不以「删除或改写 workflow 内 tool_* 旁路」为必做验收项

### Requirement: Realtime Omni 不在基本角色路径内

DashScope Omni 实时语音角色 MUST 继续经 `engines.agents.realtime_vocie_agent`（及 `realtime_vocie` 会话）装配，MUST NOT 要求使用 `AgentRoleFactory` 作为唯一创建入口。本能力的要求 MUST NOT 被解释为强制重命名或合并该路径。

#### Scenario: 语音角色仍走独立入口

- **WHEN** 调用方创建 Omni 实时语音助手
- **THEN** 入口位于 `realtime_vocie_agent`（或其后继文档所指模块），而非 LLM `build_ui_*` / `build_case_*` 列表
