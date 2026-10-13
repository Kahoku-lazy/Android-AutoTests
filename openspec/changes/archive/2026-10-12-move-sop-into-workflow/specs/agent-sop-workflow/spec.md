## Purpose

把设备检查的步骤输入装配成可运行流程，并用调用方已经启动的执行角色与验收角色推进这次运行。角色自身的提示词、工具和技能保持在角色侧。

## ADDED Requirements

### Requirement: Step input names the milestone and the required outcome

工作流 MUST 把每一步的输入收成两项：`subject` 是步骤短名，`description` 只写这一步必须达成的结果。缺少任一项，或步骤列表为空时，MUST 拒绝装配。

#### Scenario: A complete step is accepted

- **WHEN** 调用方提交至少一步，且每一步同时给出短名和必须达成的结果
- **THEN** 装配成功，步骤顺序与提交顺序一致，短名与结果分别落在对应字段

#### Scenario: An incomplete step is rejected

- **WHEN** 某一步缺少短名或缺少必须达成的结果，或步骤列表为空
- **THEN** 装配失败，并且不产生可运行流程

### Requirement: Assembly uses the supplied roles

装配 MUST 使用调用方提供的执行角色与验收角色。这两个角色 MUST 已经启动。工作流 MUST NOT 在装配时替换角色的系统提示词、工具包或技能。角色尚未启动时，装配 MUST 失败并说明哪一个角色还不能使用。

#### Scenario: Started roles are bound to every step

- **WHEN** 执行角色与验收角色都已启动，并且步骤输入完整
- **THEN** 每一步都由这两个角色执行和验收，重试上限沿用本次装配给出的次数

#### Scenario: A role that has not started cannot be assembled

- **WHEN** 执行角色或验收角色尚未启动
- **THEN** 装配失败，错误说明指向尚未启动的那个角色

### Requirement: The runner receives the assembled flow

运行入口 MUST 接收已经装配好的流程，而不是未处理的步骤原文。给定开场输入后，运行入口 MUST 把流程推进到完成、挂起或失败三者之一，并返回该阶段。

#### Scenario: An opening message starts the assembled flow

- **WHEN** 调用方把装配结果和一条开场输入交给运行入口
- **THEN** 运行入口推进该流程，并返回完成后的阶段

### Requirement: Empty device log is one engine refusal

运行期间工具报告日志为空时，这一次尝试 MUST 作为引擎的一次驳回记下：结论为未通过，说明为该报告。驳回 MUST 消耗该步的一次重试。次数尚未用尽时，引擎 MUST 把该步退回待重做，并把这条说明交给执行者；次数用尽时，引擎 MUST 把该步与整次运行标为失败。运行入口 MUST NOT 在次数用尽前自行把该步标为失败。没有正在执行的步骤时，MUST 保持原阶段。

#### Scenario: Attempts remain after an empty log

- **WHEN** 当前步骤正在执行，重试次数尚未用尽，并且工具报告日志为空
- **THEN** 该步新增一条未通过结论，说明为日志为空，该步回到待重做，整次运行尚未失败

#### Scenario: The attempt budget is spent on empty logs

- **WHEN** 同一步连续因为日志为空被驳回，直到驳回次数达到该步上限
- **THEN** 该步与整次运行都为失败，结论条数等于该上限，最后一条说明为日志为空

### Requirement: A run can be saved and continued

运行入口 MUST 能导出当前运行的 `SOPRunState`。这份状态 MUST 只包含流程自身的输入、每一步的阶段、交付与历次结论。它 MUST NOT 包含执行者或验收者的对话上下文。用同一份已装配流程和导出的状态 MUST 能重建运行入口并继续步骤顺序。重建所使用的智能体上下文以调用方重新传入的角色为准，不从这份状态恢复。

#### Scenario: Saved state restores the flow without agent context

- **WHEN** 调用方导出一次尚未结束的运行状态，并用同一份装配结果与新的已启动角色重建运行入口
- **THEN** 步骤顺序、阶段、交付与历次结论与导出前一致，新角色不带有导出前的对话上下文
