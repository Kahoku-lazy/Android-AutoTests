## ADDED Requirements

### Requirement: 角色经 create_agent 统一装配

新增或修改可运行的 **LLM** 智能体角色时，创建实现 MUST 经唯一创建出口 `engines.ae_harness.agents.creator.create_agent`，并只接受聊天模型；该出口 SHALL 每次返回独立实例（`AgentBundle.agent`），不跨任务共享对话状态。角色 MUST 只由「名字 + 提示词短名 + 模型短名」三样装配，MUST NOT 恢复四分段配置作为构造契约。交予智能体的模型 SHALL 为已创建的模型对象，MUST NOT 将模型配置对象作为构造参数。实时语音角色的创建能力 MUST NOT 存在。

#### Scenario: 新增设备类角色

- **WHEN** 开发者新增一个可运行的设备操作角色
- **THEN** 角色经 `create_agent` 以名字、提示词短名与模型短名装配，返回独立实例

#### Scenario: 不存在第二个创建出口

- **WHEN** 扫描 `engines/` 与 `backend/` 的智能体构造代码
- **THEN** 不存在绕过 `create_agent` 直接构造智能体的位置

#### Scenario: 语音角色不再可创建

- **WHEN** 检索仓内语音智能体的创建入口
- **THEN** 找不到任何语音或实时语音角色的创建能力

### Requirement: 模型配置与实例由 ae_harness 单点提供

模型连接参数的**数据** SHALL 集中在 `engines/ae_harness/agents/config/models.yaml`（按短名给出模型名、族、密钥环境变量名等），**代码** SHALL 集中在 `engines/ae_harness/agents/models.py`。模型配置 MUST NOT 散落在业务模块或后端视图里；密钥 MUST 只以环境变量名形式出现，MUST NOT 写入配置文件；实例 MUST NOT 跨事件循环复用。

#### Scenario: 装配角色取模型

- **WHEN** 装配任一可运行角色
- **THEN** 模型短名取自 `models.yaml`，经 `models.py` 造实例，装配代码里看不到密钥、基础 URL 或 provider 细节

#### Scenario: 模型数据只有一份

- **WHEN** 检查模型配置落点
- **THEN** 只有 `engines/ae_harness/agents/config/models.yaml`，不存在第二份模型表

#### Scenario: 缺密钥时可读失败

- **WHEN** 配置引用的密钥环境变量缺失
- **THEN** 报错点名缺失的变量名，且不打印任何密钥值

#### Scenario: 跨事件循环不复用

- **WHEN** 两个任务在各自线程的事件循环里装配同一角色
- **THEN** 后起的循环拿到新实例，不复用先前循环建好的异步客户端

### Requirement: 工具经 ae_harness 门面分配

Agent 工具实现 SHALL 放在 `engines/ae_harness/tools/<域>/`；分配给角色 SHALL 经该域的门面函数（设备域为 `build_adb_tools()`，只读子集为 `build_adb_readonly_tools()`）。业务代码 MUST NOT 直接 import 工具实现以绑到角色；写操作工具 MUST NOT 挂给验收角色。

#### Scenario: 为执行者挂载设备工具

- **WHEN** 执行者需要设备动作工具
- **THEN** 工具经 `build_adb_tools()` 取得并逐个挂载

#### Scenario: 验收角色只有只读工具

- **WHEN** 装配验收角色
- **THEN** 只使用 `build_adb_readonly_tools()`，不含任何改设备状态的动作

### Requirement: 引擎能力经工具层暴露

设备控制、串口日志、OCR 能力 SHALL 分别落在 `engines/device`、`engines/uart_log`、`engines/vision`；其中设备控制经 `engines/ae_harness/tools/adb/` 暴露给角色。串口与 OCR 工具 MUST NOT 进入该目录——该目录只做手机 UI 执行与验收。上层 MUST NOT 为业务任务直接 import `uiautomator2` / `airtest` 或绕过 `action` 调用 `engines.device.android`。

#### Scenario: 设备动作调用链

- **WHEN** 角色需要一次设备动作
- **THEN** 工具经 `engines/device` 的对外入口执行，不直接调用底层库

#### Scenario: 能力边界

- **WHEN** 检查 `engines/ae_harness/tools/`
- **THEN** 只存在设备（adb）域工具，不存在串口、视觉或语音工具目录

## MODIFIED Requirements

### Requirement: 提示词唯一配置入口

角色系统提示词正文 SHALL 存放在 `engines/ae_harness/agents/config/prompts/*.md`，并由 `engines.ae_harness.agents.config` 提供读取。业务代码 MUST NOT 在 `backend/apps` 或 View 内硬编码整段角色 system prompt 以绕过该入口；执行者提示词可附加「被测应用短卡」，短卡正文 SHALL 存放在 `engines/ae_harness/agents/config/app_info/*.md`，按 token 读取。已退役的 `engines/agents/config/data/prompts/`、`prompt_config.py`、`role/` 包 MUST NOT 再引入。

#### Scenario: 角色读取提示词

- **WHEN** 角色构造需要 system prompt
- **THEN** 按提示词短名从 `engines/ae_harness/agents/config/prompts/` 读取正文，调用方不自己打开文件

#### Scenario: 执行者附加应用短卡

- **WHEN** 执行者角色需要被测应用的上下文
- **THEN** 按 token 从 `app_info/` 读取短卡并追加到系统提示词，token 缺失时报可读错误

## REMOVED Requirements

### Requirement: 角色经 AgentRoleFactory 装配

**Reason**: 该需求锚定 `engines/agents` 的聊天/语音双出口与实时语音角色，`engines/agents` 整包退役，语音能力整体下线。

**Migration**: 角色改由 `ae_harness.create_agent` 单出口装配，见新增需求「角色经 create_agent 统一装配」；语音创建能力无替代。

### Requirement: 模型配置唯一装载入口

**Reason**: 该需求指向 `engines/agents/models` 包与 `agent_config.yaml` 的 `ModelConfig` 段，二者随包删除。

**Migration**: 模型数据落到 `engines/ae_harness/agents/config/models.yaml`、代码落到 `agents/models.py`，见新增需求「模型配置与实例由 ae_harness 单点提供」。

### Requirement: 工具唯一分配入口

**Reason**: `engines/agents/tools/tool_*.py` 与 `tools_config.py` 随包删除。

**Migration**: 工具落到 `engines/ae_harness/tools/<域>/` 并经门面函数分配，见新增需求「工具经 ae_harness 门面分配」。

### Requirement: Harness 底座经工具暴露

**Reason**: 原需求以 `tools_config` 装配 OCR/串口工具为前提，该装配入口已删除。

**Migration**: 保留「底座能力经工具暴露、不直接调用底层库」的约束，落点改为 `engines/ae_harness/tools/adb/` 且明确不含串口与视觉工具，见新增需求「引擎能力经工具层暴露」。

### Requirement: 创建清单可追溯

**Reason**: 该需求引用的 `GUIDE-创建Agent清单.md` 与 `engines/agents/AGENTS.md` 统一流程随包退役。

**Migration**: 新增角色的自检清单改由 `engines/ae_harness/agents/AGENTS.md`「新增一个角色的标准路径」与 `engines/backend_bridge/AGENTS.md` 承担。

### Requirement: 模型实例只经单一门面获取

**Reason**: 该需求约束 `engines/agents/models` 的门面、会话内实例缓存与备用模型回退，门面与缓存实现随包删除；备用模型回退能力一并取消。

**Migration**: 实例只经 `agents/models.py` 取得，不做跨调用缓存，见新增需求「模型配置与实例由 ae_harness 单点提供」；未配置备用模型即不回退。

### Requirement: 角色装配配置严格校验

**Reason**: 该需求校验四分段配置装载与 `agent_builders.__all__`，四分段配置与 `agent_builders` 随包退役。

**Migration**: 角色入参收敛为三要素，配置错误由 `models.yaml` 字段校验与读取口报错；不提供四分段兼容层。

### Requirement: 基本角色创建清单与复杂度可追溯

**Reason**: 该需求锚定 `load_role_spec → Factory → build_*` 旧创建链与两份随包文档，链路已不存在。

**Migration**: 由新增需求「角色经 create_agent 统一装配」与 `engines/ae_harness/agents/AGENTS.md` 承担可追溯性。

### Requirement: Harness 四分段留在配置层且 skills 延后

**Reason**: 四分段（Role / Tools / Context / ReAct）是 `engines/agents` 的配置模型，随包退役；`ToolsConfig` 的 skills 扩展一并取消。

**Migration**: 角色只保留「提示词 + 模型 + 工具」三件事；`config/data/skills/` 的 vendored 脚手架随包删除，技能不再作为角色配置项。
