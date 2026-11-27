## MODIFIED Requirements

### Requirement: Step input names the milestone and the required outcome

工作流 MUST 把每一步的输入收成两项：`subject` 是执行角色这一步要做的动作，`description` 是验收角色这一步要核对的结果。缺少任一项，或步骤列表为空时，MUST 拒绝装配。装配完成后，交给执行角色的步骤提示 MUST 包含该步 `subject`，且 MUST NOT 包含该步 `description`。交给验收角色的步骤提示 MUST 包含该步 `description`，且 MUST NOT 包含该步 `subject`。驳回后的重试说明只追加给执行角色。

把用例编译成步骤时，`subject` MUST 取该步动作本身：去掉「动作：」前缀，并把换行与连续空白压成单个空格。`subject` MUST NOT 拼接用例标题，MUST NOT 拼接步骤序号。用例标题 MAY 写进 `description` 的首行（形如 `用例：<标题>`），MUST NOT 占用 `subject`。

#### Scenario: A complete step is accepted

- **WHEN** 调用方提交至少一步，且每一步同时给出动作和要核对的结果
- **THEN** 装配成功，步骤顺序与提交顺序一致，动作与结果分别落在 `subject` 与 `description`

#### Scenario: An incomplete step is rejected

- **WHEN** 某一步缺少动作或缺少要核对的结果，或步骤列表为空
- **THEN** 装配失败，并且不产生可运行流程

#### Scenario: Each role is asked only its own text

- **WHEN** 一步的动作是「点击开关」，要核对的结果是「日志出现关闭成功」，并且这一步开始提问
- **THEN** 执行角色收到的步骤提示含有「点击开关」且不含「日志出现关闭成功」；验收角色收到的步骤提示含有「日志出现关闭成功」且不含「点击开关」

#### Scenario: 编译出的步骤 subject 就是动作

- **WHEN** 平台用例里某一步的动作是「删除快照」，该用例标题是「H705F 快照功能测试（UI 验证）」，这是第 3 步
- **THEN** 编译出的该步 `subject` 为「删除快照」
- **AND** `subject` 里不含用例标题，也不含 `第 3 步`

#### Scenario: 用例标题留在 description

- **WHEN** 同上一条
- **THEN** 该步 `description` 首行是「用例：H705F 快照功能测试（UI 验证）」
- **AND** 其后的动作、断言与页面锚点一条不少
