## ADDED Requirements

### Requirement: 删除被引用的 Agent 配置必须拒绝

运营删除 Agent 配置时，系统 MUST 先检查是否仍被助手名片引用。被引用时 MUST 拒绝删除并返回可读原因（列出占用该配置的名片显示名），MUST NOT 删除记录，MUST NOT 级联改动名片。

#### Scenario: 仍有名片使用时删不掉

- **WHEN** 运营删除一条仍被两个助手名片引用的 Agent 配置
- **THEN** 系统返回 400 并列出这两个名片名
- **AND** 配置与名片都保持原样

#### Scenario: 无引用时可以删除

- **WHEN** 运营删除一条没有任何名片引用的 Agent 配置
- **THEN** 删除成功
- **AND** 其它配置不受影响
