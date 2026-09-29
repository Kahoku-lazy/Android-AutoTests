# ai-engine-protocol — 提示词随引擎走

## MODIFIED Requirements

### Requirement: 系统提示词随引擎走
规划 / 执行 / 验收三份系统提示词 MUST 由引擎侧的提示词常量（`engines/ai/agents/config.py`）提供，MUST NOT 经 `TaskRequest` 由 Django 注入，MUST NOT 从数据库读取。引擎装配 Agent 时 MUST 取该角色自己声明的提示词常量。`TaskRequest` MUST NOT 存在系统提示词字段；装配工厂 MUST NOT 接受提示词入参。

#### Scenario: 角色提示词来自引擎常量
- **WHEN** 引擎装配任一角色
- **THEN** 该角色的 `system_prompt` 等于引擎该角色的提示词常量
- **AND** 无需 Django 传入任何提示词

#### Scenario: TaskRequest 无提示词通道
- **WHEN** Django 组装 `TaskRequest`
- **THEN** 该对象不含系统提示词字段，引擎侧也无从外部覆盖提示词的入参

#### Scenario: 三份常量均非空
- **WHEN** 读取引擎三份提示词常量
- **THEN** 规划 / 执行 / 验收三份均非空且为 Markdown 正文

## REMOVED Requirements

### Requirement: TaskRequest 携带三角色系统提示词
（收回：提示词不再由 Django 注入，改由引擎常量提供，见上条。）

### Requirement: 系统提示词装配 fail-fast
（收回：库中已无提示词字段，装配期不再需要校验提示词非空；三份常量由测试守护非空。）
