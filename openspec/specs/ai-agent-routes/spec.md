# ai-agent-routes Specification

## Purpose
TBD - created by archiving change refactor-ai-two-routes-task-publishing. Update Purpose after archive.
## Requirements
### Requirement: 智能体支持多线路模型配置

系统 SHALL 允许管理员为单一智能体配置多条能力线路，每条线路包含独立的规划模型与执行模型配置。

#### Scenario: 配置控制设备线路

- **WHEN** 管理员在智能体配置页为「控制设备」线路填写规划模型与执行模型
- **THEN** 系统保存该线路的规划模型与执行模型配置，并在平台助手栏展示线路摘要

#### Scenario: 平台任务线路占位

- **WHEN** 管理员查看「平台任务」线路配置
- **THEN** 系统展示该线路入口（可配置但本期不执行 reasoning）

### Requirement: 线路配置内 API Key 加密与脱敏

系统 SHALL 对每条线路模型配置中的 api_key 进行加密存储，并在响应中脱敏展示。

#### Scenario: API Key 脱敏返回

- **WHEN** 非超级管理员读取智能体详情
- **THEN** 系统不返回 api_key 明文（脱敏或空字符串）

