## MODIFIED Requirements

### Requirement: 步骤标题标明模型在做什么

每一轮 MUST 可折叠，且默认收起。**执行轮**的标题 MUST 以行首数字序号开头，序号 MUST 按该用例内的**执行步骤**计：同一执行步骤的重试 MUST 共用同一个序号，换页后 MUST 不跳号。**验收轮**的标题 MUST NOT 带序号。标题 MUST NOT 出现中文步骤序号（「步骤一」…「步骤十」），MUST NOT 出现模型名，也 MUST NOT 出现「执行模型 / 验收模型 / 规划模型」这类角色类别文字。标题 MUST 含该步要做的动作或要达成的结果；重试轮 MUST 标明是第几次。

角色名 MUST 以徽章形式呈现，且 MUST 按角色区分配色——执行角色与验收角色 MUST 使用不同底色。角色徽章之前 MUST 有一个固定标记：执行轮为 `➡️`，验收轮按其判决为 `✅`（PASS）或 `❌`（FAIL）；尚无判决的验收轮 MUST NOT 给该标记。验收轮的判决 MUST 只由该标记表示：MUST NOT 另渲染 PASS / FAIL 徽章，也 MUST NOT 另写判决文字。角色名为空的存量轮次 MUST NOT 渲染角色徽章，标题其余部分保持完整。

#### Scenario: 执行轮标题带动作

- **WHEN** 第一步由 `executor_role` 执行，模型为 `deepseek-flash`，动作为「启动应用」
- **THEN** 该轮标题为「1.」+ `➡️` + `executor_role` 徽章 + 「：启动应用」，且不含「执行模型」，不含「步骤一」，也不含 `deepseek-flash`

#### Scenario: 验收轮不占序号并以结果标记开头

- **WHEN** 该轮的 `role` 为 `verifier_role` 且判 PASS，动作为「前台为 govee」
- **THEN** 该轮标题不以数字序号开头，而是以 `✅` 开头，随后是 `verifier_role` 徽章与「：前台为 govee」，且标题里没有 PASS 徽章

#### Scenario: 验收轮失败标记

- **WHEN** 验收轮的判决为不通过
- **THEN** 该轮标题以 `❌` 开头，且标题里没有 FAIL 徽章

#### Scenario: 尚无判决的验收轮

- **WHEN** 验收轮还没有判决，动作文本为「前台为 govee」
- **THEN** 该轮标题不带 `✅` 或 `❌`，也不带序号，仍渲染 `verifier_role` 徽章与「：前台为 govee」

#### Scenario: 角色名以徽章呈现

- **WHEN** 同一用例里既有 `executor_role` 轮也有 `verifier_role` 轮
- **THEN** 两个角色名都以徽章出现，且执行角色与验收角色的徽章底色不同，角色名不再以纯文本出现

#### Scenario: 重试轮标明次数

- **WHEN** 同一执行步骤的第 2 次尝试
- **THEN** 该轮标题含「第 2 次」，且序号与首次尝试相同

#### Scenario: 存量轮次没有角色名

- **WHEN** 该轮的 `role` 为空且动作文本为「点击开关」
- **THEN** 该轮不渲染角色徽章，标题仍含 `➡️` 与「：点击开关」
