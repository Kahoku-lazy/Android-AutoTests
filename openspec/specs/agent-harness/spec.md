# agent-harness Specification

## Purpose

约束平台 **Agent = Model + Harness** 的实现落点：角色装配、工具/提示词配置入口、engines 与 Django 边界。与根 `AGENTS.md`「平台架构定位」、`dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`、`engines/agents/AGENTS.md`「创建 Agent 统一流程」对齐；接口字段细节仍以其它 specs / OpenAPI 为准。

## Requirements

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

### Requirement: 提示词唯一配置入口

角色系统提示词正文 SHALL 存放在 `engines/agents/config/data/prompts/*.md`，并由 `engines.agents.role_sys_prompts` 解析 token / 导出常量后供角色取用。业务代码 MUST NOT 在 `backend/apps` 或 View 内硬编码整段角色 system prompt 以绕过该入口。已废弃路径 `engines/agents/prompts/`、`prompt_config.py`、`role/` 包 MUST NOT 再引入。

#### Scenario: 角色读取提示词

- **WHEN** 角色构造需要 system prompt
- **THEN** YAML `RoleConfig.system_prompt` 为 token 时经 `role_sys_prompts.resolve_system_prompt` 读 md；或从 `role_sys_prompts` 导出常量取值

### Requirement: 模型配置唯一装载入口

模型连接参数的数据 SHALL 只存在于配置层读出的模型表；读取该表与密钥加解密 MUST 只有配置层一处实现。模型实例的创建 MUST 由模型创建层按短名完成，创建层 MUST NOT 自己读文件或环境变量。角色四分段（Role / Tools / Context / ReAct）的装载 SHALL 留在配置层，其装载入口 MUST NOT 把模型连接参数回传给角色装配层。`ModelConfig` MUST 止于建模型管线，MUST NOT 成为 Agent 对外构造参数。已删除的 `engines.agents.role.models` 与 `engines.agents.config.models` MUST NOT 恢复。旧模型包 `engines/agents/models` MUST NOT 继续作为装载入口存在。

#### Scenario: 装载执行角色模型

- **WHEN** 装配执行角色（`build_ui_executor()` 或等价的角色装配入口）
- **THEN** 模型短名取自角色配置，模型实例由模型创建层按短名创建；角色装配代码里看不到连接参数，Agent 构造只接收已建好的模型

#### Scenario: 模型数据仍在 config

- **WHEN** 检查模型数据的落点
- **THEN** 角色与模型数据仍由配置层读取，模型创建层内没有任何模型数据文件

#### Scenario: 角色装载只回传四分段

- **WHEN** 调用角色装载入口取某个角色的配置
- **THEN** 返回的是角色与三段 Harness 配置，模型连接参数不在返回值里

#### Scenario: 旧模块路径不再存在

- **WHEN** 检查 `engines/agents/config/models.py`、`engines/agents/role/models.py` 与 `engines/agents/models/`
- **THEN** 这些路径均不存在，且仓内没有对它们的导入

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

需要模型实例的模块 MUST 只经模型创建层的唯一出口按短名创建：MUST NOT 直接 import 该层的内部模块，MUST NOT 自行构造聊天、实时语音、嵌入或语音合成模型对象。同一类模型的构造逻辑 MUST 只有一处实现。查看规格 MUST 走只读视图，MUST NOT 为了读字段而创建实例。

聊天模型实例 SHALL 在同一进程内按「短名 + 流式开关」复用：这两项相同的两次创建 MUST 把同一聊天模型交给不同的新智能体。实时语音模型 MUST NOT 复用。创建层 MUST NOT 读取调用点传入的明文密钥来绕过配置层注入的密钥。

备用模型的连接参数 MUST NOT 再由模型创建层解析。重试与回退策略 MUST NOT 自行解析模型连接参数；只在调用方已经传入备用模型实例时使用该实例。嵌入模型的 token 用量计量 MUST 由检索调用方在创建之后自行记录，MUST NOT 作为模型创建出口的参数。

强制结构化交卷时关闭思考的行为 SHALL 保留，且 MUST 只生效一次：同一聊天模型被多次交给装配层时，不得叠加包装。该行为 MUST NOT 放在模型创建出口内。

#### Scenario: 角色装配只调门面取聊天模型

- **WHEN** 装配任一 LLM 角色
- **THEN** 代码按角色键经聊天创建出口取智能体，装配与工作流代码里不出现 provider、密钥、基础 URL 等连接参数

#### Scenario: 同配置复用同一实例

- **WHEN** 同一次运行内连续装配多个使用同一聊天短名、同一流式开关的角色
- **THEN** 这些角色拿到同一聊天模型对象，各自仍是新的智能体实例

#### Scenario: 配置变化即新实例

- **WHEN** 同一聊天短名一次要求流式、一次要求非流式
- **THEN** 两次拿到的聊天模型不是同一对象

#### Scenario: 跨事件循环不复用

- **WHEN** 两个任务在各自线程的事件循环里装配同一角色，且短名与流式开关相同
- **THEN** 聊天模型按短名与流式开关复用，不按事件循环拆分；两个智能体仍是新实例

#### Scenario: 备用模型由门面提供

- **WHEN** 主模型因瞬态故障用尽重试，且调用方没有传入备用模型实例
- **THEN** 重试模块不自行解析备用模型配置，也不尝试其它模型

#### Scenario: 非聊天模型同样走门面

- **WHEN** 需要 Omni 实时语音或嵌入模型实例
- **THEN** 经模型创建层按短名创建，调用方模块内不出现这些模型类的构造代码

#### Scenario: 实时语音模型构造只有一处

- **WHEN** 分别检查实时语音角色装配与会话路径取模型的方式
- **THEN** 两条路径走同一处实现，不存在两套并列的 Omni 模型构造

#### Scenario: 门面不被旁路

- **WHEN** 扫描 `engines/` 源码的 import
- **THEN** 包外模块没有模型创建层子模块形式的导入，也没有对聊天、嵌入、语音合成、实时语音模型类的直接构造

#### Scenario: 复用后的实例不被重复包装

- **WHEN** 同一聊天模型被多次交给装配层，并触发强制结构化交卷
- **THEN** 关闭思考的改写只生效一次，模型调用入口不发生叠加包装

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
