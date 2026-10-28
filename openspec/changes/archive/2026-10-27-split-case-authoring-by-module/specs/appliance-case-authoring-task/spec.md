## MODIFIED Requirements

### Requirement: Case-authoring runs the writer and verifier roles

后台执行 MUST 按 `Task.task_kind` 分流：`case_authoring` MUST 拼接任务文档为一个需求正文，先由模块规划角色切成多个需求区间，再逐模块调用用例编写角色与验收角色，把合并后的完整 Markdown 文档、历次判决、模块清单、截断标记、通过标记与摘要写入 `Task.result`。全部模块通过时任务状态 MUST 为 `completed`，任一模块未通过 MUST 为 `failed`；被用户关闭时 MUST 为 `cancelled` 且不得被后台线程回写成完成。

`Task.result.modules` MUST 为每个模块给出 `key`、`name`、`start_line`、`end_line`、`passed`、`truncated`、`document_length` 与 `message`。`Task.result.truncated` MUST 表示是否有模块因输出上限被截断且无法继续拆分。`Task.result.document` MUST 为按模块拼接的 Markdown。

#### Scenario: Accepted document completes task

- **WHEN** 所有模块的编写角色交付文档且验收角色判通过
- **THEN** 任务状态为 `completed`，`Task.result` 含 `passed=true`、合并后的 `document` 全文、`modules` 清单与判决列表

#### Scenario: Rejected document fails task

- **WHEN** 任一模块两次尝试都判不通过
- **THEN** 任务状态为 `failed`，`Task.result` 保留该模块的最后草稿、驳回意见与模块清单，其它已通过模块的文档仍保留

#### Scenario: Truncated module is split

- **WHEN** 某模块的编写输出达到单次上限
- **THEN** 后台执行把该模块拆成更小的模块继续生成，`Task.result.modules` 里能看到子模块与 `truncated` 标记
- **AND** 不再把半截文档送给验收角色
