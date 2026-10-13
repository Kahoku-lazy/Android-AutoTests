## MODIFIED Requirements

### Requirement: Step input names the milestone and the required outcome

工作流 MUST 把每一步的输入收成两项：`subject` 是执行角色这一步要做的动作，`description` 是验收角色这一步要核对的结果。缺少任一项，或步骤列表为空时，MUST 拒绝装配。装配完成后，交给执行角色的步骤提示 MUST 包含该步 `subject`，且 MUST NOT 包含该步 `description`。交给验收角色的步骤提示 MUST 包含该步 `description`，且 MUST NOT 包含该步 `subject`。驳回后的重试说明只追加给执行角色。

#### Scenario: A complete step is accepted

- **WHEN** 调用方提交至少一步，且每一步同时给出动作和要核对的结果
- **THEN** 装配成功，步骤顺序与提交顺序一致，动作与结果分别落在 `subject` 与 `description`

#### Scenario: An incomplete step is rejected

- **WHEN** 某一步缺少动作或缺少要核对的结果，或步骤列表为空
- **THEN** 装配失败，并且不产生可运行流程

#### Scenario: Each role is asked only its own text

- **WHEN** 一步的动作是「点击开关」，要核对的结果是「日志出现关闭成功」，并且这一步开始提问
- **THEN** 执行角色收到的步骤提示含有「点击开关」且不含「日志出现关闭成功」；验收角色收到的步骤提示含有「日志出现关闭成功」且不含「点击开关」

## ADDED Requirements

### Requirement: The manual entry loads one case file

手工运行入口 MUST 从命令行收到一个 YAML 路径；未提供路径时 MUST 拒绝运行并说明用法。根节点 MUST 是含 `title` 与 `steps` 的映射，或由这样的映射组成的非空列表。每条用例的 `title` MUST 作为该次流程名称。`steps` 中每一项的 `action` MUST 作为该步动作，`assert` MUST 作为该步要核对的结果，顺序与文件一致。文件中有多条用例时，入口 MUST 按文件顺序各跑一遍 SOP，后一条 MUST NOT 复用前一条的角色对话。文件不存在、根节点不是上述两种形状、列表为空、缺少 `title` / `steps` / `action` / `assert`，或任一步动作、结果为空时，MUST 拒绝运行，并且 MUST NOT 装配流程。每条用例的重试上限 MUST 为 2。开场输入不从该文件读取。

#### Scenario: One case file becomes the step list

- **WHEN** 调用方传入一份根为单条用例的 YAML，标题为「H6810 详情页开关测试」，且 `steps` 含两步，每步都有非空 `action` 与 `assert`
- **THEN** 流程名称等于该标题，两步的动作与结果按文件顺序装入，重试上限为 2

#### Scenario: Two cases run as two SOPs

- **WHEN** 调用方传入一份含两条用例的 YAML，标题依次为「甲」和「乙」
- **THEN** 按该顺序装配两份流程，名称分别为「甲」和「乙」，每份的重试上限都为 2

#### Scenario: A missing or unusable case file is refused

- **WHEN** 未提供路径，或路径不存在，或某步缺少 `action` 或 `assert`
- **THEN** 运行在装配之前结束，并且不产生可运行流程

### Requirement: A refused attempt stays on the same step until the budget is spent

验收结论为不通过时，若该步已用次数尚未达到装配时给出的上限，工作流 MUST 让同一步再试，并把驳回说明交给执行角色。次数达到上限时，工作流 MUST 把该步与整次运行标为失败，并且 MUST NOT 开始后续步骤。验收结论为通过时，工作流 MUST 结束该步并开始下一步（若存在）。

#### Scenario: The first refusal retries the same step

- **WHEN** 某步重试上限为 2，且第一次验收结论为不通过
- **THEN** 整次运行尚未失败，同一步进入下一次尝试，执行角色能看到该次驳回说明，下一步尚未开始

#### Scenario: The second refusal stops the run

- **WHEN** 同一步第二次验收结论仍为不通过
- **THEN** 该步与整次运行都为失败，文件中排在后面的步骤不会开始

### Requirement: The manual entry reports each case

全部用例结束后，手工入口 MUST 按文件顺序逐条输出该用例的 `title`，以及 PASS 或 FAIL。运行阶段为完成时 MUST 输出 PASS。运行阶段不是完成时 MUST 输出 FAIL，并在该标题下列出失败点。失败点 MUST 包含阶段为失败、或最后结论为不通过的步骤，并写出步序、动作和驳回说明。尚未开始的后续步骤 MUST NOT 算作失败点。没有这类步骤时，失败点 MUST 写出运行阶段。汇总末尾 MUST 给出全部用例的总耗时，以及合计的模型调用次数、输入 token、输出 token、缓存命中 token 和费用。

#### Scenario: One case fails and the next passes

- **WHEN** 第一条标题为「H6810 短卡片页开关测试」且未完成，失败步是第 2 步，驳回说明为「没看到样式栏」；第二条标题为「H6810 详情页亮度、颜色与场景模式测试」且已完成
- **THEN** 汇总先写出第一条标题和 FAIL，其下失败点含第 2 步与「没看到样式栏」；随后写出第二条标题和 PASS

#### Scenario: Totals follow the per-case results

- **WHEN** 全部用例已经跑完
- **THEN** 汇总在各条 PASS 或 FAIL 之后给出总耗时和合计用量与费用
