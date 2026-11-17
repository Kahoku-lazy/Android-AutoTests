## MODIFIED Requirements

### Requirement: 任务错误自动登记为 BUG 单

系统 SHALL 在任务终态落库后自动登记 BUG 单。UI 自动化任务状态为 `failed` 且 `failure_kind` 为 `verdict` 时，MUST 按 `Task.result.failed` 中的每个失败用例各登记一张 BUG 单；该列表为空时 MUST 登记一张任务级 BUG 单。`failure_kind` 为 `provider`、`device` 或 `platform` 时，MUST 各登记一张任务级 BUG 单，来源键 MUST 区分这三类，正文 MUST 使用结果中的 `reason`。状态为 `interrupted` 时 MUST 登记一张任务级 BUG 单，正文 MUST 按 `cause` 说明是停机超时、进程退出或预算超限，MUST NOT 一律写成服务重启。用例编写任务状态为 `failed` 时 MUST 登记一张任务级 BUG 单；任务为 `completed` 但 `Task.result.case_import.status=failed` 时 MUST 登记一张入库失败 BUG 单。`cancelled` 任务 MUST NOT 登记。同一任务、同一失败类别的重复收口 MUST NOT 再建一张来源键相同的 BUG 单。登记失败 MUST NOT 改变任务状态、任务结果或验收结论。

#### Scenario: 多个失败用例逐条登记

- **WHEN** UI 自动化任务失败，`failure_kind` 为 `verdict`，且 `result.failed` 包含两个用例标题
- **THEN** BUG 台账新增两张 `ui_automation` BUG 单，分别对应用例标题
- **AND** 两张 BUG 单都关联同一个任务编号

#### Scenario: 模型拒绝只登记一张

- **WHEN** UI 自动化任务进入 `failed`，且 `failure_kind` 为 `provider`
- **THEN** 新增一张任务级 `ui_automation` BUG 单
- **AND** 正文是结果中的 `reason`，不是网关返回的整段错误
- **AND** 再次收口同一任务不新增第二张同类 BUG 单

#### Scenario: 没有失败用例明细时登记任务级 BUG

- **WHEN** UI 自动化任务进入 `failed`，`failure_kind` 为 `verdict`，且 `result.failed` 为空
- **THEN** 新增一张任务级 `ui_automation` BUG 单，正文包含任务结果中的原因

#### Scenario: 中断任务登记

- **WHEN** 任务因进程退出被标记为 `interrupted`，且 `cause` 为 `process_lost`
- **THEN** 新增一张对应分类的 BUG 单，正文说明进程退出导致终态未写回
- **AND** 正文不写「服务重启」

#### Scenario: 用例入库失败登记

- **WHEN** 用例编写任务为 `completed` 且 `case_import.status=failed`
- **THEN** 新增一张 `case_authoring` BUG 单，正文包含入库失败原因
- **AND** 任务仍保持 `completed`，验收结论不变

#### Scenario: 取消任务不登记

- **WHEN** 任务被用户取消并进入 `cancelled`
- **THEN** BUG 台账不新增该任务的 BUG 单
