# agent-harness Specification

## Purpose

约束平台 **Agent = Model + Harness** 的实现落点：角色装配、工具/提示词配置入口、engines 与 Django 边界。与根 `AGENTS.md`「平台架构定位」、`dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`、`engines/agents/AGENTS.md`「创建 Agent 统一流程」对齐；接口字段细节仍以其它 specs / OpenAPI 为准。

## Requirements

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

### Requirement: 提示词唯一配置入口

角色系统提示词正文 SHALL 存放在 `engines/agents/config/data/prompts/*.md`，并由 `engines.agents.role_sys_prompts` 解析 token / 导出常量后供角色取用。业务代码 MUST NOT 在 `backend/apps` 或 View 内硬编码整段角色 system prompt 以绕过该入口。已废弃路径 `engines/agents/prompts/`、`prompt_config.py`、`role/` 包 MUST NOT 再引入。

#### Scenario: 角色读取提示词

- **WHEN** 角色构造需要 system prompt
- **THEN** YAML `RoleConfig.system_prompt` 为 token 时经 `role_sys_prompts.resolve_system_prompt` 读 md；或从 `role_sys_prompts` 导出常量取值

### Requirement: 模型配置唯一装载入口

模型连接参数的**代码** SHALL 集中在 `engines/agents/models` 包；模型连接参数的**数据** SHALL 继续留在 `engines/agents/config/data/`（`agent_config.yaml` 的 `ModelConfig` 段与同目录 `config.yaml`），位置与格式 MUST NOT 因本约束而改变，`models` 包内 MUST NOT 存放模型数据文件。角色四分段（Role / Tools / Context / ReAct）的装载 SHALL 留在 `engines/agents/config`，其装载入口 MUST NOT 把模型连接参数回传给角色装配层。`ModelConfig` MUST 止于建模型管线，MUST NOT 成为 Agent 对外构造参数。已删除的 `engines.agents.role.models` MUST NOT 再使用；`engines.agents.config.models` MUST NOT 恢复。

#### Scenario: 装载执行角色模型

- **WHEN** 装配执行角色（`build_ui_executor()` 或等价的角色装配入口）
- **THEN** 模型连接参数取自 `agent_config.yaml` 的 `ModelConfig` 段，经 `engines/agents/models` 读取；角色装配代码里看不到 `ModelConfig` 实例，Agent 构造只接收已建好的模型

#### Scenario: 模型数据仍在 config

- **WHEN** 检查模型数据的落点
- **THEN** 角色与模型数据仍在 `engines/agents/config/data/` 下，`engines/agents/models/` 内没有任何 `.yaml` 数据文件

#### Scenario: 角色装载只回传四分段

- **WHEN** 调用角色装载入口取某个角色的配置
- **THEN** 返回的是角色与三段 Harness 配置，模型连接参数不在返回值里

#### Scenario: 旧模块路径不再存在

- **WHEN** 检查 `engines/agents/config/models.py` 与 `engines/agents/role/models.py`
- **THEN** 两个路径均不存在，且仓内没有对它们的导入

### Requirement: 工具唯一分配入口

Agent 工具实现 SHALL 放在 `engines/agents/tools/tool_*.py`；分配给角色 SHALL 经 `engines/agents/tools_config.py`（如 `build_*_toolkit`）。技能目录 SHALL 落在 `engines/agents/config/data/skills/`，经 `tools_config` 挂载。业务代码 MUST NOT 直接 import 工具模块以绑到角色。废弃文件名 `test_device.py` / `test_serial.py` MUST NOT 再使用。

#### Scenario: 为角色挂载设备工具

- **WHEN** executor 需要设备动作工具
- **THEN** 工具来自 `tools_config.build_executor_toolkit`（或同等 `tools_config` API）

### Requirement: engines 零 Django / apps 依赖

`engines/**` MUST NOT import `django`、`apps.*` 或 `backend.apps.*`。任务、密钥解密、写库 SHALL 留在 backend；engines 经注入或环境配置获取明文密钥与只读协议对象。

#### Scenario: 静态边界

- **WHEN** 扫描 `engines/` 下 Python 源码的 import
- **THEN** 不存在对 `django`、`apps`、`backend.apps` 的导入（机械化检查见 `engines-agents-style` 的 `no-django-apps-import`）

### Requirement: Harness 底座经工具暴露

设备控制、串口日志、OCR 能力 SHALL 分别落在 `engines/device`、`engines/uart_log`、`engines/vision`，并由 `tool_*.py` 暴露给角色。上层 MUST NOT 为业务任务直接 import `uiautomator2` / `airtest` 或绕过 `action` 调用 `engines.device.android`。

#### Scenario: OCR 调用链

- **WHEN** 角色需要页面文字
- **THEN** 经 `tools_config` 装配的 OCR 工具调用 `engines.vision`，且工具模块对 cnocr 保持延迟导入

### Requirement: 创建清单可追溯

新增 Agent 角色的变更说明或 OpenSpec 变更请求 SHOULD 引用 `dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md` 与 `engines/agents/AGENTS.md`「创建 Agent 统一流程」，并完成该清单中的自检项（含风格检查技能）。

#### Scenario: 文档引用

- **WHEN** 合并一个新增角色的变更
- **THEN** 描述中可定位到 GUIDE 清单与统一流程，且 `engines-agents-style` 检查已运行

### Requirement: 模型实例只经单一门面获取

需要模型实例的模块 MUST 只从 `engines/agents/models` 的包入口取实例：MUST NOT 直接 import 该包的子模块，MUST NOT 自行构造 `agentscope` 的聊天、实时语音、嵌入或语音合成模型对象。同一类模型的构造逻辑 MUST 只有一处实现。备用模型的连接参数（`AGENT_FALLBACK_*`）SHALL 由 `models` 解析，重试与回退策略 MUST NOT 自行解析模型连接参数，只接收已建好的备用模型实例。嵌入模型的 token 用量计量 SHALL 由 `models` 提供，调用方只传用量回调。

聊天模型实例 SHALL 由门面按「配置指纹 + 事件循环亲和」复用：同一事件循环内、连接参数（provider / 模型名 / 基础 URL / 密钥 / vision / stream）完全相同的两次取用 MUST 返回同一实例；任一参数变化 MUST 视为不同实例。MUST NOT 在另一个事件循环里复用先前循环建好的实例（异步客户端与循环绑定）。包入口 SHALL 提供显式清空实例复用的手段，供测试隔离环境变量。

#### Scenario: 角色装配只调门面取聊天模型

- **WHEN** 装配任一 LLM 角色
- **THEN** 代码只在包入口调用「按角色键取聊天模型」，装配与工作流代码里不出现 provider、密钥、基础 URL、vision / stream 等连接参数

#### Scenario: 同配置复用同一实例

- **WHEN** 同一次运行内连续装配多个步骤的执行者与验收者
- **THEN** 相同角色键取到的聊天模型是同一对象，不重复构造客户端

#### Scenario: 配置变化即新实例

- **WHEN** 环境变量里的密钥变化，或角色节的 vision / stream / 模型名 / 地址不同
- **THEN** 门面返回新建的实例，不复用旧配置的客户端

#### Scenario: 跨事件循环不复用

- **WHEN** 两个任务在各自线程的事件循环里装配同一角色
- **THEN** 后起的循环拿到新实例，不复用先前循环建好的异步客户端

#### Scenario: 备用模型由门面提供

- **WHEN** 环境里配置了 `AGENT_FALLBACK_MODEL`（可选 `AGENT_FALLBACK_PROVIDER` / `AGENT_FALLBACK_BASE_URL` / `AGENT_FALLBACK_API_KEY`）
- **THEN** 包入口返回可用的备用聊天模型实例；未配置模型名时返回空；重试模块不再解析这些变量，只使用传入的实例

#### Scenario: 非聊天模型同样走门面

- **WHEN** 需要 Omni 实时语音、嵌入或语音合成模型
- **THEN** 分别经包入口的对应入口取实例，调用方模块内不出现 `DashScopeRealtimeModel` / `DashScopeEmbeddingModel` / `DashScopeTTSModel` 的构造代码

#### Scenario: 实时语音模型构造只有一处

- **WHEN** 分别检查实时语音角色装配与会话路径取模型的方式
- **THEN** 两条路径走同一处实现，不存在两套并列的 Omni 模型构造

#### Scenario: 门面不被旁路

- **WHEN** 扫描 `engines/` 源码的 import
- **THEN** 包外模块没有 `engines.agents.models.<子模块>` 形式的导入，也没有对 `agentscope.model` / `agentscope.embedding` / `agentscope.tts` / `agentscope.realtime` 模型类的直接构造

#### Scenario: 复用后的实例不被重复包装

- **WHEN** 门面返回的聊天模型被多次交给装配层
- **THEN** 强制结构化交卷的请求改写只挂一次，模型实例上的调用入口不发生叠加包装

### Requirement: 角色装配配置严格校验

装载角色四分段时，`agent_config.yaml` 的 `ContextConfig` / `ReActConfig` 节 MUST 只出现对应 dataclass 的字段名：出现未知键 MUST 抛 `ValueError`，且报错 MUST 同时列出未知键与合法键。节点缺失、`null`、空映射、空白字符串仍 SHALL 视为空节并取 dataclass 默认值。`agent_builders` 的 `__all__` MUST 与模块实际定义一致：`__all__` 中的每个名字 MUST 是模块属性。

#### Scenario: 分段键拼写错误立即失败

- **WHEN** 在 `ReActConfig` 下写了 dataclass 不存在的键（如 `max_iter`）
- **THEN** `load_role_spec` 抛 `ValueError`，消息点名该键并给出合法键列表

#### Scenario: 空节仍取默认值

- **WHEN** 某个角色节没有写 `ContextConfig`
- **THEN** 装载结果使用 `ContextConfig` 的默认值，不报错

#### Scenario: 导出清单与实现一致

- **WHEN** 对 `engines.agents.agent_builders` 执行 `import *`
- **THEN** 成功，且 `__all__` 里不存在已删除的符号

### Requirement: 基本角色创建清单与复杂度可追溯

针对「基本 LLM 角色创建」的简化或重构变更，SHALL 在 OpenSpec 变更或 `temps/` 分析中保留当前 create 调用链说明（含 YAML → `load_role_spec` → Factory → `build_*`），并引用 `temps/agents_architecture.md`（或其后继）与 `GUIDE-创建Agent清单.md`。变更 MUST NOT 在同一变更中捆绑 realtime 重命名、middleware 策略统一化、**skills 产品扩展**、或 workflow 对 `tool_*` 的旁路清理，除非该变更的 proposal 显式扩大范围。

#### Scenario: 范围隔离

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
