## ADDED Requirements

### Requirement: Case-authoring task records its creator

`Task` MUST 增加创建人快照，提交用例编写任务时 MUST 写入当前请求用户编号；重跑 MUST 继承原任务的创建人。创建人 MUST 与 Agent-02 的 owner 分离：共享 Agent-02 被普通用户使用时，任务创建人 MUST 是该普通用户，MUST NOT 是 Agent-02 的 owner。历史任务没有创建人时 MAY 回退到 Agent-02 的 owner。

#### Scenario: 普通用户提交共享 Agent-02 任务

- **WHEN** 普通用户选择超管共享的 Agent-02 并提交任务
- **THEN** 该任务的创建人是该普通用户
- **AND** 任务仍按 Agent-02 的既有可见性规则对该用户可见

#### Scenario: 重跑继承创建人

- **WHEN** 用户对一个失败任务执行重跑
- **THEN** 新任务的创建人与原任务相同

### Requirement: Accepted case-authoring results are written to the case library

任务终态为 `completed` 且 `Task.result.passed=true`、`Task.result.document` 非空时，后台执行 MUST 把该文档导入当前用户「AI 生成用例」项目的用例文件。导入 MUST 在任务结果落库前完成，导入结论 MUST 写入 `Task.result.case_import`。导入失败 MUST NOT 改变任务状态或验收结论，MUST NOT 清空 `Task.result.document`。

#### Scenario: 通过验收后自动入库

- **WHEN** 一个 Agent-02 任务所有模块通过验收
- **THEN** 任务结果包含 `case_import.status=imported`、项目编号、文件编号与用例条数
- **AND** 用例管理对应文件下可以查到这些用例

#### Scenario: 导入异常不影响任务完成

- **WHEN** 导入过程抛出异常
- **THEN** 任务仍为 `completed`
- **AND** `Task.result.case_import.status=failed` 并带失败原因
- **AND** `Task.result.document` 仍保留完整 Markdown

### Requirement: Report links to imported cases

测试报告列表 MUST 包含用例编写任务，并下发 `task_kind` 供前端显示「类型」。任务详情报告 `GET /api/tasks/{id}/report/` 对用例编写任务 MUST 返回 `case_import`（导入结论）、`documents`（上传文档名）与 `conclusion.verdicts`（判决列表），MUST NOT 再返回完整 `document`，MUST NOT 伪造设备用例轮次。

`case_import` MUST 至少包含 `status`（`imported` / `skipped` / `failed`）、`project_id`、`file_id`、`path`、`case_count` 与 `message`；只有 `status=imported` 时 `path` 才是可点击地址。任务详情页 MUST 展示「用例已写入用例管理」结果卡与用例条数，点击 MUST 跳转 `/cases/projects/:projectId/files/:fileId`；MUST NOT 在报告页渲染生成的 Markdown 文档。导入未成功时 MUST 展示提示文案，MUST NOT 渲染空链接。

#### Scenario: Report links to imported cases

- **WHEN** 用户点击一个已完成且已导入的用例编写任务
- **THEN** 详情页展示「用例已写入用例管理」结果卡与用例条数
- **AND** 点击结果卡进入对应项目文件页
- **AND** 页面不显示「生成的测试用例」Markdown 文档

#### Scenario: Import failed shows message only

- **WHEN** 任务完成但 `case_import.status=failed` 或 `skipped`
- **THEN** 详情页展示失败或跳过原因
- **AND** MUST NOT 给出可点击的用例文件地址

#### Scenario: Report list distinguishes task kind

- **WHEN** 用户打开测试报告列表
- **THEN** 每行带「类型」列，用例编写任务显示「用例编写」，设备任务显示「设备执行」

## MODIFIED Requirements

### Requirement: 用例编写报告暴露模型事件流

`GET /api/tasks/{id}/report/` 对 `task_kind=case_authoring` 的任务 MUST 返回 `events` 列表，按事件 `seq` 升序。每条事件 MUST 含 `seq`、`event_type`、`label`、`detail`、`time`、`role_name`、`role_kind`、`model`、`status` 与 `count`。

`role_kind` MUST 把 `case_writer_role` 映射为 `case_writer`、把 `case_verifier_role` 映射为 `verifier`。单条 `detail` MAY 截断到 4000 字符；完整交付正文 MUST 只保留在任务结果 `Task.result.document`，MUST NOT 再经报告下发，也 MUST NOT 在事件流里重复整篇文档。

任务详情页 MUST 在「用例入库结果」之后渲染「模型事件流」，显示时间、角色、事件标签、模型、状态、次数与详情；长文本 MUST 在区块内滚动，不得撑破页面。

#### Scenario: 报告返回编写过程

- **WHEN** 用户打开一个已完成的 Agent-02 任务报告
- **THEN** 报告 `events` 按时间顺序包含 SOP 步骤、思考块、文本块、工具调用、模型调用与验收事件
- **AND** 页面在用例入库结果下方展示这些事件，角色显示为 `case_writer_role` / `case_verifier_role`

#### Scenario: 交付正文不重复传输

- **WHEN** 编写角色通过结构化输出交付完整用例文档
- **THEN** 事件流里的该条工具调用详情被截断
- **AND** 报告响应不含完整 `document` 字段，完整文档只留在任务结果里

## REMOVED Requirements

### Requirement: Report displays generated test cases

**Reason**: 报告不再渲染完整 Markdown 文档，改为展示用例管理入库结果与跳转地址，避免报告页承载无法编辑的整篇文档。

**Migration**: 使用同一次变更新增的「Report links to imported cases」；旧前端读取的 `document` 字段不再下发，完整文档保留在 `Task.result.document` 供审计与重导入。
