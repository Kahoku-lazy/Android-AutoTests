## ADDED Requirements

### Requirement: 实验展示与平台入账分开

实验角色日志中的 4 位 DeepSeek 费用展示 MUST 继续只覆盖 `deepseek-flash` 与 `deepseek-v4-pro`，其它模型在该日志中的三项展示费用 MUST 为 0。该展示 MUST NOT 作为平台账本、仪表盘或任务费用的计算来源。平台入账 MUST 按模型名基数计价，MUST NOT 因提供商不是 DeepSeek 就把费用记为 0。

#### Scenario: 非 DeepSeek 模型仍可入账

- **WHEN** 一次平台调用的模型为 `grok-4.7`，且基数表有该模型
- **THEN** 账本按该模型基数写出人民币费用
- **AND** 实验角色日志若展示该模型，仍可显示三项 0，且不影响账本

#### Scenario: 平台费用不读取实验日志

- **WHEN** 实验日志中的 4 位费用与账本 8 位费用不一致
- **THEN** 仪表盘与任务费用采用账本金额
