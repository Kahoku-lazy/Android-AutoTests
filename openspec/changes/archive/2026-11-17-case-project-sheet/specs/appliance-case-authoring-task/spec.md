## MODIFIED Requirements

### Requirement: Accepted case-authoring artifacts are written to the case library

任务终态为 `completed` 且 `Task.result.passed=true`、`Task.result.artifact.cases` 非空时，后台执行 MUST 把产物用例追加到当前用户的「AI 生成用例」功能项目，MUST NOT 再解析 Markdown，MUST NOT 为该任务新建用例文件。该项目不存在时 MUST 创建为功能库。导入 MUST 在任务结果落库前完成，结论 MUST 写入 `Task.result.case_import`；导入失败 MUST NOT 改变任务状态或验收结论，MUST NOT 清空 `Task.result.artifact`。

追加后超过 999 行时 MUST NOT 写入任何新行，`case_import.status` MUST 为 `failed`，并说明剩余可追加条数。每条用例的步骤 MUST 以「动作 → 期望状态」成对落库：`action` 取该步 `action`，`assertion` 取该步 `expect_state` 对应的状态名（可附 `observe_by`）。`module` MUST 取所属场景标题，取不到时回退首个状态名。产物步骤若带执行提示，入库时 MUST 丢弃执行提示，MUST NOT 因此失败。用例的 `source` MUST 随任务产物保留在 `Task.result.artifact`，MUST NOT 因为导入而丢字段。

#### Scenario: 通过验收后自动入库

- **WHEN** 产物含 30 条用例且验收 `pass`，用户的功能表尚有足够空位
- **THEN** `case_import.status=imported`，含项目编号与新增条数 30
- **AND** 这 30 条出现在该用户的「AI 生成用例」功能表，不产生新的用例文件

#### Scenario: 超过 999 时不写入

- **WHEN** 功能表已有 980 行，产物含 30 条用例且验收 `pass`
- **THEN** 任务仍为 `completed`
- **AND** `case_import.status=failed`，说明还可追加 19 条
- **AND** 功能表仍是 980 行

#### Scenario: 产物与文档不一致时以产物为准

- **WHEN** `document` 里的用例条数与 `artifact.cases` 不一致
- **THEN** 入库条数以 `artifact.cases` 为准
- **AND** MUST NOT 因此判失败

#### Scenario: 导入异常不影响任务完成

- **WHEN** 导入过程抛出异常
- **THEN** 任务仍为 `completed`
- **AND** `case_import.status=failed` 带失败原因，`artifact` 仍完整
