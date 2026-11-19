## REMOVED Requirements

### Requirement: 角色经 AgentRoleFactory 装配

**Reason**: `engines/agents` 已退役。聊天与语音不再分两个出口，也没有按模型族选择智能体类型的混合出口。
**Migration**: 可运行智能体只经 `ae_harness.agents.create_agent` 创建，角色装配放在 `backend_bridge`。实时语音不再提供。

### Requirement: 提示词唯一配置入口

**Reason**: 引擎不再保存角色提示词文件，也不再按 token 解析。
**Migration**: 调用方把系统提示词正文传给 `create_agent`。平台正文来自运营库。

### Requirement: 模型配置唯一装载入口

**Reason**: 没有模型表、没有短名、没有角色四分段。连接参数由调用方传入。
**Migration**: 用 `create_model(provider, api_key_env, model_name, base_url)`。密钥仍只从仓库根 `.env` 再查进程环境。

### Requirement: 工具唯一分配入口

**Reason**: `tools_config.py` 与 `tool_*.py` 命名已随 `engines/agents` 删除。
**Migration**: 工具放 `ae_harness/tools/<域>/`，由 `catalog.py` 列出；调用方按勾选挂载。

### Requirement: Harness 底座经工具暴露

**Reason**: 工具不再经 `tools_config` 装配，OCR 也不再是角色的内置工具。
**Migration**: 设备动作经 `ae_harness/tools/adb/` 暴露。串口与 OCR 仍在各自的引擎包，上层不得绕过 `device.action`。

### Requirement: 创建清单可追溯

**Reason**: 清单引用的 `engines/agents/AGENTS.md` 已不存在。
**Migration**: 新增能力对照 `dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`、`engines/ae_harness/AGENTS.md` 与 `engines/backend_bridge/AGENTS.md`。

### Requirement: 模型实例只经单一门面获取

**Reason**: 创建不再按短名，也不按「短名 + 流式开关」复用实例。实时语音、备用模型解析与交卷包装都已删除。
**Migration**: 聊天模型只经 `create_model`；嵌入模型只由 `ae_harness/knowledge` 自建。每次 `create_agent` 都是新的智能体。

### Requirement: 角色装配配置严格校验

**Reason**: `agent_config.yaml` 与角色四分段已删除，没有可校验的分段键。
**Migration**: 连接参数由 `create_model` 校验；提示词为空时 `create_agent` 拒绝。

### Requirement: 基本角色创建清单与复杂度可追溯

**Reason**: 该需求约束的是已完成的旧包重构，引用的创建链不存在。
**Migration**: 不再单列。新能力的范围以对应变更的 proposal 为准。

### Requirement: Harness 四分段留在配置层且 skills 延后

**Reason**: 四分段配置已删除，技能目录也不再存在。
**Migration**: 角色只有名称、提示词正文、模型三样。工具由调用方在创建后挂载。

## ADDED Requirements

### Requirement: 智能体只经 create_agent 创建

可运行智能体 MUST 经 `ae_harness.agents.create_agent` 创建。调用方 MUST 传入名称、系统提示词正文，以及 `provider`、`api_key_env`、`model_name`。`base_url` 为空时 MUST 使用该厂商的默认地址。每次调用 MUST 返回新的智能体，MUST NOT 跨任务共享对话状态。创建出口 MUST NOT 读取提示词文件，MUST NOT 接收模型短名。

业务代码 MUST NOT 直接构造 `Agent`。`ae_harness` MUST NOT 定义具体角色或保存流程。

#### Scenario: 传入正文与连接参数

- **WHEN** 调用方传入非空提示词正文和一组合法连接参数
- **THEN** 返回的智能体使用该正文，工具包为空，并带出本次密钥环境变量名

#### Scenario: 提示词为空

- **WHEN** 系统提示词去空白后为空
- **THEN** 创建失败，不返回智能体

#### Scenario: 旧入口不再存在

- **WHEN** 检查 `engines/agents/`、`AgentRoleFactory`、`build_*` 与模型短名表
- **THEN** 这些入口不存在，仓内 Python 代码没有对它们的导入

### Requirement: 提示词由调用方传入

系统提示词 MUST 由调用方以正文传入。`ae_harness` MUST NOT 保存角色提示词文件，MUST NOT 按 token 或文件名解析提示词。业务代码 MUST NOT 在 `backend/apps` 或 View 内绕过调用方配置写死一段角色提示词。

#### Scenario: 文件名不被当作提示词

- **WHEN** 调用方把一个形如文件名的字符串作为系统提示词传入
- **THEN** 智能体使用该字符串本身，不打开任何文件

### Requirement: 连接参数由调用方传入

聊天模型 MUST 只经 `ae_harness.agents.create_model` 创建，参数为 `provider`、`api_key_env`、`model_name` 与可选的 `base_url`。创建层 MUST NOT 读取模型表或角色配置。密钥 MUST 先查仓库根 `.env`，再查进程环境，且只以环境变量名出现在返回值、日志和异常里。

`provider` 与 `api_key_env` 不匹配、密钥未配置，或参数校验失败时，创建 MUST 失败。

#### Scenario: 显式参数创建

- **WHEN** 调用方传入 `provider=govee`、`api_key_env=GOVEE_API_KEY` 和模型名
- **THEN** 返回的模型可用，且密钥环境变量名为 `GOVEE_API_KEY`，返回值不含密钥明文

#### Scenario: 厂商与密钥名不匹配

- **WHEN** `provider` 为 `deepseek` 而 `api_key_env` 不是 `DEEPSEEK_API_KEY`
- **THEN** 创建失败

### Requirement: 工具按域登记并由调用方挂载

工具实现 MUST 放在 `ae_harness/tools/<域>/`。`catalog.py` MUST 列出域、全部预设与只读预设，且 MUST NOT 执行工具。调用方 MUST 在 `create_agent` 之后自行挂载。业务代码 MUST NOT 直接 import 工具实现绕过目录绑定到角色。

验收侧 MUST 只挂勾选与只读目录的交集。写操作工具 MUST NOT 标为只读。

#### Scenario: 目录不含实现

- **WHEN** 读取工具目录
- **THEN** 每个工具只有名称、一句说明和是否只读，没有可执行对象

#### Scenario: 验收侧过滤写操作

- **WHEN** 验收勾选里同时有只读工具和写操作工具
- **THEN** 挂到验收者上的只有只读工具

### Requirement: 底座不绕过引擎

设备动作 MUST 经 `engines.device.action` 或 `ae_harness/tools/adb/` 使用。上层 MUST NOT 直接 import `engines.device.android`、`uiautomator2` 或 `airtest` 来完成业务动作。`engines/**` MUST NOT import `django`、`apps.*` 或 `backend.apps.*`。

#### Scenario: 静态边界

- **WHEN** 扫描 `engines/` 的 Python 导入
- **THEN** 不存在对 `django`、`apps`、`backend.apps` 的导入

### Requirement: 新增能力对照现行清单

新增 Agent 能力的变更说明 MUST 能定位到 `dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md`。能力落在 `ae_harness`，角色与流程落在 `backend_bridge`。变更 MUST NOT 在 `ae_harness` 新增角色脚本或提示词文件。

#### Scenario: 新增一个工具

- **WHEN** 合并一个新增工具的变更
- **THEN** 工具位于 `ae_harness/tools/<域>/`，并登记进目录；角色装配没有回到 `ae_harness`
