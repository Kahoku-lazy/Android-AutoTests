# agent-harness Specification

## Purpose

约束平台 **Agent = Model + Harness** 的实现落点：角色装配、工具/提示词配置入口、engines 与 Django 边界。与根 `AGENTS.md`「平台架构定位」、`dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`、`engines/agents/AGENTS.md`「创建 Agent 统一流程」对齐；接口字段细节仍以其它 specs / OpenAPI 为准。

## Requirements

### Requirement: 角色经 AgentRoleFactory 装配

新增或修改可运行的 **LLM** 智能体角色时，SHALL 使用 `engines.agents.agent_builders.AgentRoleFactory`（配合 `RoleConfig` / `ToolsConfig` / `ContextConfig` / `ReActConfig`）装配 Model 与 toolkit；SHALL 提供每次调用返回独立 `agentscope.agent.Agent` 实例的 `build_*` 入口（不跨任务共享对话状态）。语音 Omni 角色 SHALL 使用 `engines.agents.realtime_vocie_agent`，会话实现落在 `engines.agents.realtime_vocie`。

#### Scenario: 新增设备或用例类角色

- **WHEN** 开发者新增一个可运行 LLM 角色
- **THEN** 实现位于 `engines/agents/agent_builders.py`（或同包新增 builder 模块），经 `AgentRoleFactory(...).create()` 暴露 `build_*() -> Agent`

#### Scenario: 新增语音角色

- **WHEN** 开发者新增 Omni 实时语音能力
- **THEN** 装配入口在 `realtime_vocie_agent.py`，提示词经 `role_sys_prompts.VoiceKnowledgePrompts`，会话不恢复已删除的 livetranslate/pipeline 模式

### Requirement: 提示词唯一配置入口

角色系统提示词正文 SHALL 存放在 `engines/agents/config/data/prompts/*.md`，并由 `engines.agents.role_sys_prompts` 解析 token / 导出常量后供角色取用。业务代码 MUST NOT 在 `backend/apps` 或 View 内硬编码整段角色 system prompt 以绕过该入口。已废弃路径 `engines/agents/prompts/`、`prompt_config.py`、`role/` 包 MUST NOT 再引入。

#### Scenario: 角色读取提示词

- **WHEN** 角色构造需要 system prompt
- **THEN** YAML `RoleConfig.system_prompt` 为 token 时经 `role_sys_prompts.resolve_system_prompt` 读 md；或从 `role_sys_prompts` 导出常量取值

### Requirement: 模型配置唯一装载入口

聊天 / 实时模型连接参数 SHALL 经 `engines.agents.config.models`（`ModelConfig` / `ChatModelFactory` / `load_role_config` / Omni 装载器）从 `config/data/agent_config.yaml` 读取。现成短名目录（`get_text` / `get_realtime` / `get_embedding` / `DeepSeekModelConfig`）亦由该模块提供。MUST NOT 再使用已删除的 `engines.agents.role.models`。

#### Scenario: 装载执行角色模型

- **WHEN** 调用 `load_role_config("UI_EXECUTOR_ROLE_CONFIG")` 或 `build_ui_executor()`
- **THEN** ModelConfig 与四分段来自 `agent_config.yaml`，经 `config.models` 装载

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
