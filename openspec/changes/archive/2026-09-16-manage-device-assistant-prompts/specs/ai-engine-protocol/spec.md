## ADDED Requirements

### Requirement: TaskRequest 携带三角色系统提示词
Django SHALL 通过 `TaskRequest` 传入规划 / 执行 / 验收三份系统提示词（Markdown 源码字符串）。引擎装配 Agent 时 MUST 使用请求中的对应提示词作为该角色 `system_prompt`。引擎内置提示词常量 MUST 为空字符串，MUST NOT 在运行时作为回退填入 Agent。

#### Scenario: 注入库中提示词
- **WHEN** Django 组装 `TaskRequest` 且平台智能体三份提示词均非空
- **THEN** 引擎三个角色的系统提示词分别等于库中对应正文

#### Scenario: 引擎常量不再回退
- **WHEN** 请求已携带系统提示词
- **THEN** 引擎不得用内置常量覆盖或补全请求中的提示词

### Requirement: 系统提示词装配 fail-fast
Django 侧组装任务时 SHALL 校验规划 / 执行 / 验收三份系统提示词去空白后均非空。任一份缺失或为空时 SHALL 在装配阶段抛出可读错误（指明角色），任务以失败终态结束，MUST NOT 以空系统提示词进入工作流。

#### Scenario: 某角色提示词为空
- **WHEN** 平台智能体某角色系统提示词去空白后为空
- **THEN** 任务在装配阶段失败，错误文案指明该角色，不进入工作流
