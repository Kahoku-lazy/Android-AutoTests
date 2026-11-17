## MODIFIED Requirements

### Requirement: 步骤行标题与结果徽标

每个步骤行 MUST 是可折叠的卡片，步骤行 MUST 是唯一的折叠单位。标题 MUST 以行首数字序号开头，序号 MUST 取该步在用例里的步骤号；同一步骤的多次尝试 MUST 共用同一序号。标题 MUST 只含序号与动作，MUST NOT 出现中文步骤序号（「步骤一」…「步骤十」），MUST NOT 出现模型名，也 MUST NOT 出现角色类别文字。动作文本 MUST 只出现一次，MUST NOT 在执行子块或验收子块里重复。

步骤结果 MUST 以两处一致的方式表达：行首的状态方块用 `✓`（PASS）、`✗`（FAIL）、`△`（未完成）、`○`（未执行）之一；行尾 MUST 给出同名的文字标签 `PASS`、`FAIL`、`未完成`、`未执行` 之一。两处结果 MUST 对应，MUST NOT 出现方块与文字不一致。步骤行 MUST NOT 使用 emoji `✅` / `❌` 表达结果。

#### Scenario: 步骤行只写一次动作

- **WHEN** 第一步由 `executor_role` 执行，模型为 `deepseek-flash`，动作为「启动应用」
- **THEN** 该用例只有一行以「1.」开头并含「启动应用」的步骤行
- **AND** 展开后的执行子块与验收子块都不再重复「启动应用」，也不出现 `deepseek-flash` 与「执行模型」

#### Scenario: 结果只由步骤徽标表示

- **WHEN** 某步结果为 PASS
- **THEN** 步骤行左侧为 `✓`、右侧为 `PASS` 文字标签，两者一致
- **AND** 步骤行不出现 emoji `✅`
- **AND** 该步验收子块头部有 `✅`
