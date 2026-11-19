## MODIFIED Requirements

### Requirement: BUG 单分类与任务关联

系统 SHALL 为每张 BUG 单持久化分类、标题、错误正文、处理状态、来源任务编号、任务标题快照、任务类型、Agent 编号与创建人。分类 MUST 有 `ui_automation`（UI 自动化）、`case_authoring`（测试用例编写）与 `requirement_breakdown`（需求拆解）三种。带冻结种类的任务 MUST 按冻结种类映射：`ui_automation`、`case_authoring`、`requirement_breakdown` 分别对应同名 BUG 分类。没有冻结种类的历史任务 MUST 继续按 `task_kind` 映射：`device_control` → `ui_automation`，`case_authoring` → `case_authoring`。每张 BUG 单 MUST 带非空 `task_id`，并 MUST 提供稳定的 BUG 编号用于展示。

#### Scenario: UI 自动化任务生成 UI 自动化 BUG

- **WHEN** 一个冻结种类为 `ui_automation` 的任务进入失败终态
- **THEN** 生成的 BUG 单分类为 `ui_automation`
- **AND** BUG 单的 `task_id` 等于该任务编号，任务标题快照等于该任务标题

#### Scenario: 用例编写任务生成用例编写问题

- **WHEN** 一个冻结种类为 `case_authoring` 的任务验收未通过
- **THEN** 生成的 BUG 单分类为 `case_authoring`
- **AND** BUG 单的 `task_id` 等于该任务编号

#### Scenario: 需求拆解失败使用新分类

- **WHEN** 一个冻结种类为 `requirement_breakdown` 的任务失败
- **THEN** 生成的 BUG 单分类为 `requirement_breakdown`
- **AND** 该单不归入 UI 自动化或测试用例编写

#### Scenario: BUG 编号稳定且可读

- **WHEN** 用户打开 BUG 单列表或详情
- **THEN** 每张 BUG 单显示形如 `BUG-0001` 的编号
- **AND** 同一张 BUG 单在列表、详情与刷新后编号不变

### Requirement: 任务错误自动登记为 BUG 单

系统 SHALL 在任务终态落库后自动登记 BUG 单。当前工作流任务状态为 `failed` 或 `interrupted` 时 MUST 只登记一张任务级 BUG 单，MUST NOT 按步骤名、用例标题或模块名再拆多张。UI 自动化单 MUST 保存失败步骤快照：至少包含序号、步骤名、期望结果、实际结果、尝试次数与原因类别。多个步骤没通过时 MUST 全部写入同一张单，标题 MUST 使用第一个失败步骤名。

需求拆解只在没有形成合法模块清单或运行中断时登记一张。模块清单合法时 MUST NOT 因某个模块内容不受认可而登记。用例编写保持验收未通过、中断和入库失败三类登记。

历史 `device_control` 任务状态为 `failed` 且没有失败步骤快照时，MUST 继续按 `Task.result.failed` 中的每个失败用例各登记一张；该列表为空时 MUST 登记一张任务级 BUG 单。`interrupted` 且没有失败步骤快照时 MUST 登记一张任务级 BUG 单。用例编写任务状态为 `failed` 时 MUST 登记一张任务级 BUG 单；任务为 `completed` 但 `Task.result.case_import.status=failed` 时 MUST 登记一张入库失败 BUG 单。

`cancelled` 任务 MUST NOT 登记。登记失败 MUST NOT 改变任务状态、任务结果或验收结论。登记 MUST NOT 回读 HTML 报告或已删除任务来补全失败步骤。

#### Scenario: 工作流多步失败只登记一张

- **WHEN** 一条 UI 自动化任务失败，且结果里有两个没通过的步骤
- **THEN** BUG 台账只新增一张关联该任务的 BUG 单
- **AND** 标题含第一个失败步骤名
- **AND** 该单同时保存两个步骤的序号、步骤名、期望结果、实际结果与尝试次数

#### Scenario: 抛错仍能看出停在哪一类

- **WHEN** 一条运行中的工作流任务因模型拒绝结束，且终态里没有已完成的步骤结论
- **THEN** 新增一张 BUG 单
- **AND** 失败步骤的原因类别为模型拒绝
- **AND** 实际结果是给人读的短句，不是网关原文或堆栈

#### Scenario: 中断任务登记

- **WHEN** 任务因进程退出被标记为 `interrupted`
- **THEN** 新增一张对应分类的 BUG 单
- **AND** 失败步骤写明中断原因
- **AND** 正文不出现「服务重启」

#### Scenario: 多个失败用例逐条登记

- **WHEN** 一条没有失败步骤快照的 UI 自动化任务失败，且 `result.failed` 包含两个用例标题
- **THEN** BUG 台账新增两张 `ui_automation` BUG 单，分别对应用例标题
- **AND** 两张 BUG 单都关联同一个任务编号

#### Scenario: 没有失败用例明细时登记任务级 BUG

- **WHEN** 一条没有失败步骤快照的 UI 自动化任务进入 `failed` 且 `result.failed` 为空
- **THEN** 新增一张任务级 `ui_automation` BUG 单，正文包含任务结果中的原因

#### Scenario: 用例入库失败登记

- **WHEN** 用例编写任务为 `completed` 且 `case_import.status=failed`
- **THEN** 新增一张 `case_authoring` BUG 单，正文包含入库失败原因
- **AND** 任务仍保持 `completed`，验收结论不变

#### Scenario: 合法拆解不登记

- **WHEN** 需求拆解任务成功，并且结果含至少一个合法模块
- **THEN** BUG 台账不新增该任务的 BUG 单

#### Scenario: 取消任务不登记

- **WHEN** 任务被用户取消并进入 `cancelled`
- **THEN** BUG 台账不新增该任务的 BUG 单
