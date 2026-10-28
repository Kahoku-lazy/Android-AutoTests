## MODIFIED Requirements

### Requirement: 步骤标题标明模型在做什么

每一轮 MUST 可折叠，且默认收起。标题 MUST 以行首数字序号标出该轮在本用例内的次序，MUST NOT 再出现中文步骤序号（「步骤一」…「步骤十」），也 MUST NOT 出现模型名。标题 MUST 含角色类别（执行模型 / 验收模型 / 规划模型）与该步要做的动作或要达成的结果；重试轮 MUST 标明是第几次。角色名 MUST 以徽章形式呈现，与判决徽章同一视觉族，MUST NOT 与类别、动作混排成一段无区分的纯文本。验收轮在有判决时 MUST 在标题上标 PASS 或 FAIL。角色名为空的存量轮次 MUST NOT 渲染角色徽章，标题其余部分保持完整。

#### Scenario: 执行轮标题带动作

- **WHEN** 第一步由 `executor_role` 执行，模型为 `deepseek-flash`，动作为「启动应用」
- **THEN** 该轮标题的行首是数字序号，正文含「执行模型」、`executor_role` 徽章与「启动应用」，且不含「步骤一」，也不含 `deepseek-flash`

#### Scenario: 角色名以徽章呈现

- **WHEN** 该轮的 `role` 为 `verifier_role`，且该轮判 PASS
- **THEN** 该轮标题同时出现 `verifier_role` 角色徽章与 PASS 判决徽章，两者同为徽章样式，角色名不再以纯文本出现

#### Scenario: 重试轮标明次数

- **WHEN** 某轮是同一用例内该步的第 2 次尝试
- **THEN** 该轮标题含「第 2 次」

#### Scenario: 存量轮次没有角色名

- **WHEN** 该轮的 `role` 为空且动作文本为「点击开关」
- **THEN** 该轮不渲染角色徽章，标题仍含数字序号、「执行模型」与「点击开关」
