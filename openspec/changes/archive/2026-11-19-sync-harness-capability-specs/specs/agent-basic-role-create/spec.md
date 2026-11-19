## REMOVED Requirements

### Requirement: 基本角色经 YAML 五段与 Factory 创建

**Reason**: `agent_config.yaml`、角色四分段和 `AgentRoleFactory` 已随 `engines/agents` 删除。
**Migration**: 调用方把名称、提示词正文和连接参数传给 `create_agent`，再自行挂工具。

### Requirement: N1 ModelConfig 不进入 Agent

**Reason**: `ModelConfig` 已不存在，没有「配置对象进入 Agent」这条路径。
**Migration**: `create_agent` 只接收已由 `create_model` 创建的模型所对应的连接参数。

### Requirement: N2 四分段配置类型无循环依赖且 1:1

**Reason**: 四分段类型已删除，循环依赖的两个模块都不存在。
**Migration**: 不再单列。角色只有名称、提示词正文、模型。

### Requirement: skills 不在本期基本角色创建变更内

**Reason**: 该需求约束一次已经结束的旧变更，技能目录也不再存在。
**Migration**: 新工具只按 `ae_harness/tools/<域>/` 登记。需要 Skill 或 MCP 时另行变更。

### Requirement: 工具经 tools_config 注入

**Reason**: `tools_config.py` 已删除。
**Migration**: 调用方在 `create_agent` 之后从目录取得工具并挂载。

### Requirement: 提示词经 role_sys_prompts 解析

**Reason**: 提示词文件与 token 解析已删除。
**Migration**: 调用方传入正文。`UI_EXECUTOR_PROMPT` 这类文件名不再被解析。

### Requirement: N3 Agent 只提供角色；workflow 编排旁路清理延后

**Reason**: 该需求把清理工作留到后续，而后续已经落地：编排只在 `ae_harness/workflow/sop/`。
**Migration**: 流程装配在 `backend_bridge`，只调 `load_spec` / `run_sop`。

### Requirement: Realtime Omni 不在基本角色路径内

**Reason**: 实时语音路径已删除，不再存在第二条创建入口。
**Migration**: 不再提供 `RealtimeAgent`。语音需求须先立项。

## ADDED Requirements

### Requirement: 基本角色由调用方三要素创建

一个可运行角色 MUST 由三样东西组成：调用方传入的名称、系统提示词正文，以及经 `create_model` 创建的聊天模型。`create_agent` MUST NOT 接收工具、记忆、能力型中间件、角色表或编排参数。观测、重试、预算与取消 MUST 由调用方显式传入，默认一个都不挂。

#### Scenario: 三要素创建

- **WHEN** 调用方传入名称、非空正文和合法连接参数
- **THEN** 返回的智能体只含这三样，工具包为空

#### Scenario: 不传短名

- **WHEN** 调用方尝试用模型短名创建
- **THEN** 没有可接受短名的参数，创建无法完成

### Requirement: 工具在创建之后挂载

工具 MUST NOT 作为 `create_agent` 的参数。调用方 MUST 在拿到智能体后自行挂载。验收侧 MUST 只挂勾选与只读目录的交集。

#### Scenario: 创建时不带工具

- **WHEN** 刚从 `create_agent` 拿到智能体
- **THEN** 其工具包为空

#### Scenario: 验收勾选含写操作

- **WHEN** 装配验收者，且勾选里有写操作工具
- **THEN** 写操作工具不在验收者的工具集里

### Requirement: 提示词只接受正文

`create_agent` 的系统提示词参数 MUST 按正文使用。它 MUST NOT 打开文件，MUST NOT 把特定字符串当作提示词文件名。业务代码 MUST NOT 在 View 内写死一段角色提示词来绕过调用方配置。

#### Scenario: 旧文件名原样保留

- **WHEN** 传入的正文恰好是 `UI_EXECUTOR_PROMPT`
- **THEN** 智能体的系统提示词就是这串文字，不读取 `prompts/` 下的文件
