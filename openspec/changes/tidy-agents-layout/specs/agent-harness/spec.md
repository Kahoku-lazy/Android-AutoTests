## MODIFIED Requirements

### Requirement: 提示词唯一配置入口

角色系统提示词正文 SHALL 存放在 `engines/agents/config/data/prompts/*.md`。文件读取 MUST 经 `engines.agents.config` 的配置读取口完成；`engines.agents.role_sys_prompts` SHALL 继续解析 token 并导出常量。业务代码 MUST NOT 在 `backend/apps` 或 View 内硬编码整段角色 system prompt 以绕过该入口。已废弃路径 `engines/agents/prompts/`、`prompt_config.py`、`role/` 包 MUST NOT 再引入。应用短卡与日志关键词正文同样 MUST 经该配置读取口取得，消费模块 MUST NOT 自行打开这些配置文件。

#### Scenario: 角色读取提示词

- **WHEN** 角色构造需要 system prompt
- **THEN** YAML `RoleConfig.system_prompt` 为 token 时经 `role_sys_prompts.resolve_system_prompt` 读 md；或从 `role_sys_prompts` 导出常量取值
- **AND** 实际打开文件的实现位于配置读取口，不位于提示词导出模块

#### Scenario: 日志关键词缺失仍降级

- **WHEN** 验收步骤按型号取日志关键词，而对应文件缺失或型号名非法
- **THEN** 调用方得到空正文，步骤不因此失败

### Requirement: 工具唯一分配入口

Agent 工具实现 SHALL 放在 `engines/agents/tools/tool_*.py`；分配给角色 SHALL 经 `engines.agents.tools` 内的工具分配模块（如 `build_*_toolkit`）。根路径 `engines.agents.tools_config` MUST 继续再导出同一组符号，直到调用方完成迁移。技能目录 SHALL 落在 `engines/agents/config/data/skills/`，经该分配模块挂载。业务代码 MUST NOT 直接 import 工具模块以绑到角色。废弃文件名 `test_device.py` / `test_serial.py` MUST NOT 再使用。

#### Scenario: 为角色挂载设备工具

- **WHEN** executor 需要设备动作工具
- **THEN** 工具来自工具分配模块的 `build_executor_toolkit`（或同等 API）

#### Scenario: 旧分配路径仍可用

- **WHEN** 现有代码从 `engines.agents.tools_config` 导入分配函数
- **THEN** 导入成功，且得到与新位置相同的函数

### Requirement: 事件与语音演示入口可兼容迁移

过程事件的写入与接收方绑定 SHALL 由 `engines.agents.messaging` 提供。根路径 `engines.agents.event_log` 与 `engines.agents.event_sink` MUST 继续再导出原符号。语音演示入口 SHALL 落在 `engines.agents.realtime_vocie`，根路径 `engines.agents.realtime_vocie_agent` MUST 继续再导出原符号。用例角色的成对装配 SHALL 落在 `engines.agents.assistant`，根路径 `engines.agents.case_roles` MUST 继续再导出原符号。这些迁移 MUST NOT 改变事件内容、语音会话行为或角色工具绑定结果。

#### Scenario: 旧事件入口仍可导入

- **WHEN** 现有 workflow 或后端从 `engines.agents.event_sink` 导入接收方绑定
- **THEN** 导入成功，事件仍按原协议交给接收方

#### Scenario: 语音演示不另造智能体

- **WHEN** 运行语音演示入口
- **THEN** 智能体仍由语音创建出口产生，演示模块不直接构造实时语音智能体
