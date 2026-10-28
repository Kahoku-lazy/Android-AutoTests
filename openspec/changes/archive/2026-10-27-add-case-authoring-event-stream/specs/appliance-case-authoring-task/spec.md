## ADDED Requirements

### Requirement: 用例编写报告暴露模型事件流

`GET /api/tasks/{id}/report/` 对 `task_kind=case_authoring` 的任务 MUST 返回 `events` 列表，按事件 `seq` 升序。每条事件 MUST 含 `seq`、`event_type`、`label`、`detail`、`time`、`role_name`、`role_kind`、`model`、`status` 与 `count`。

`role_kind` MUST 把 `case_writer_role` 映射为 `case_writer`、把 `case_verifier_role` 映射为 `verifier`。单条 `detail` MAY 截断到 4000 字符；完整交付正文 MUST 仍只放在 `document`，不得在事件流里重复整篇文档。

任务详情页 MUST 在「生成的测试用例」之后渲染「模型事件流」，显示时间、角色、事件标签、模型、状态、次数与详情；长文本 MUST 在区块内滚动，不得撑破页面。

#### Scenario: 报告返回编写过程

- **WHEN** 用户打开一个已完成的 Agent-02 任务报告
- **THEN** 报告 `events` 按时间顺序包含 SOP 步骤、思考块、文本块、工具调用、模型调用与验收事件
- **AND** 页面在用例文档下方展示这些事件，角色显示为 `case_writer_role` / `case_verifier_role`

#### Scenario: 交付正文不重复传输

- **WHEN** 编写角色通过结构化输出交付完整用例文档
- **THEN** 事件流里的该条工具调用详情被截断，完整文档只在 `document` 字段出现
