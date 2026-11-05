## REMOVED Requirements

### Requirement: Case-authoring runs the writer and verifier roles

**Reason**: 执行编排从「模块规划 + 逐模块编写/验收 + 截断拆分」收敛为一条目标流水线、两个角色；`Task.result.modules` 与 `truncated` 不再存在。

**Migration**: 改用「Case-authoring runs a single goal pipeline」；历史任务的 `modules` 字段保持只读兼容，新任务不再写入。

### Requirement: Accepted case-authoring results are written to the case library

**Reason**: 入库来源从「解析 Markdown 文档」改为「直接读结构化产物 `artifact.cases`」，步骤断言由自然语言预期变为状态名。

**Migration**: 改用「Accepted case-authoring artifacts are written to the case library」。

## ADDED Requirements

### Requirement: Case-authoring runs a single goal pipeline

后台执行 MUST 按 `Task.task_kind` 分流：`case_authoring` MUST 把任务文档拼成一个需求正文，交给一条目标流水线（执行者=用例编写、验证者=用例验收）运行，MUST NOT 调用模块规划角色，MUST NOT 按行号切分需求。

每个任务最多 3 轮驳回：任一轮 `pass` 时任务状态 MUST 为 `completed`；3 轮仍 `fail` 或执行者连续 3 次未产出合法结构化输出时 MUST 为 `failed`，并保留最后一次产物、预检结论与全部判决；被用户关闭时 MUST 为 `cancelled` 且不得被后台线程回写成完成。

#### Scenario: 首轮通过即完成

- **WHEN** 编写角色写入完整三段产物，验证者取预检后判 `pass`
- **THEN** 任务状态为 `completed`
- **AND** `Task.result` 含 `passed=true`、`artifact`、`facts`、一条 `verdicts` 与渲染后的 `document`

#### Scenario: 三轮驳回后失败

- **WHEN** 三轮验收都判 `fail`
- **THEN** 任务状态为 `failed`
- **AND** `Task.result` 保留最后一次 `artifact`、`facts` 与三条判决，`reason` 为最后一轮驳回意见

#### Scenario: 结构化输出持续失败

- **WHEN** 执行者连续 3 次没有给出符合 schema 的结构化输出
- **THEN** 任务状态为 `failed`，`reason` 写明「未产出合法结构化输出」
- **AND** MUST NOT 把空 `artifact` 判成通过

#### Scenario: 不再出现模块清单

- **WHEN** 任意一次用例编写任务结束
- **THEN** `Task.result` 里没有 `modules` 与 `truncated`
- **AND** 报告接口不返回模块清单

### Requirement: Case-authoring result payload

`Task.result` MUST 含 `passed`、`summary`、`phase`、`artifact`（`states` / `transitions` / `scenarios` / `cases` / `diagram`）、`facts`（`blocking` / `warnings`）、`verdicts`、`document`、`reason`。`modules` 与 `truncated` MUST NOT 再出现。历史任务缺 `artifact` 时报告 MUST 按空值兜底，MUST NOT 报错。

#### Scenario: 新任务带三段产物

- **WHEN** 一个新任务完成
- **THEN** `Task.result.artifact` 含四组结构化数据与 `diagram`
- **AND** `document` 是渲染后的 Markdown

#### Scenario: 历史任务兼容

- **WHEN** 打开一个旧任务（`result` 里只有 `modules`）
- **THEN** 报告正常返回，`artifact` 为空
- **AND** 页面不渲染产物区块，也不报错

### Requirement: Accepted case-authoring artifacts are written to the case library

任务终态为 `completed` 且 `Task.result.passed=true`、`Task.result.artifact.cases` 非空时，后台执行 MUST 把产物用例导入当前用户「AI 生成用例」项目的用例文件，MUST NOT 再解析 Markdown。导入 MUST 在任务结果落库前完成，结论 MUST 写入 `Task.result.case_import`；导入失败 MUST NOT 改变任务状态或验收结论，MUST NOT 清空 `Task.result.artifact`。

每条用例的步骤 MUST 以「动作 → 期望状态」成对落库：`action` 取该步 `action`，`assertion` 取该步 `expect_state` 对应的状态名（可附 `observe_by`）。`module` MUST 取所属场景标题，取不到时回退首个状态名。用例的 `source` MUST 随任务产物保留在 `Task.result.artifact`，MUST NOT 因为导入而丢字段；用例库本次不新增 `source` 列。

#### Scenario: 通过验收后自动入库

- **WHEN** 产物含 30 条用例且验收 `pass`
- **THEN** `case_import.status=imported`，含项目编号、文件编号与用例条数 30
- **AND** 用例管理对应文件下可查到这 30 条用例，每条步骤的期望侧是状态名

#### Scenario: 产物与文档不一致时以产物为准

- **WHEN** `document` 里的用例条数与 `artifact.cases` 不一致
- **THEN** 入库条数以 `artifact.cases` 为准
- **AND** MUST NOT 因此判失败

#### Scenario: 导入异常不影响任务完成

- **WHEN** 导入过程抛出异常
- **THEN** 任务仍为 `completed`
- **AND** `case_import.status=failed` 带失败原因，`artifact` 仍完整
