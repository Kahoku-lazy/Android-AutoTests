# appliance-case-authoring-task Specification

## Purpose
把家电测试用例编写做成 AI 助手里可选的 Agent-02 任务：选择 Agent-02 后上传 PRD/Word 文档，后台解析并调用用例编写/验收流程，生成结果进入任务清单与测试报告。

## Requirements

### Requirement: Agent-02 is visible in the assistant board

`AIAgent` MUST 增加 `task_kind` 字段，取值 `device_control`（设备执行）或 `case_authoring`（用例编写）。系统 MUST 通过迁移创建名为 `Agent-02` 的角色，`task_kind` 为 `case_authoring`，职责为「测试用例编写」。AI 助手看板 MUST 为每个用户可见 Agent 渲染一张卡，Agent-02 卡片 MUST 显示 `职责：测试用例编写`，配置页 MUST 显示 `case_authoring_workflow`。

#### Scenario: Assistant board shows both agents

- **WHEN** 用户打开 `/ai-assistant/agents`，且可见 Agent-01 与 Agent-02
- **THEN** 页面渲染两张卡，分别显示 `职责：UI自动化` 与 `职责：测试用例编写`

#### Scenario: Agent-02 config page shows case workflow

- **WHEN** 超管打开 Agent-02 的配置页
- **THEN** 职责显示「测试用例编写」，工作流显示 `case_authoring_workflow`

### Requirement: Case-authoring task accepts PRD and Word documents

`Task` MUST 增加 `task_kind` 快照。任务提交 MUST 按所选 Agent 的 `task_kind` 分流：`device_control` 保持原 YAML + 设备 + 用例标题契约；`case_authoring` MUST 只要求标题与至少一份 PRD/Word 文档，MUST NOT 要求设备与 YAML。文档 MUST 支持 `.docx`、`.pdf`、`.md`，解析后以 `document` 附件落库，单份上限 20MB，一次最多 5 份。

#### Scenario: Agent-02 submits documents

- **WHEN** 用户选择 Agent-02，填写标题并上传 `prd.md`
- **THEN** 创建的任务 `task_kind=case_authoring`、`device_serial` 为空，附件为 `document`，并立即进入后台执行

#### Scenario: Missing documents rejected

- **WHEN** 用户选择 Agent-02 但没有上传任何文档
- **THEN** 提交返回 400，提示需要 PRD 或 Word 文档，且不创建任务

#### Scenario: Device task unchanged

- **WHEN** 用户选择设备执行 Agent 并提交 YAML 与设备
- **THEN** 任务 `task_kind=device_control`，按原设备队列调度，行为不变

### Requirement: Case-authoring runs the writer and verifier roles

后台执行 MUST 按 `Task.task_kind` 分流：`case_authoring` MUST 拼接任务文档为一个需求正文，先由模块规划角色切成多个需求区间，再逐模块调用用例编写角色与验收角色，把合并后的完整 Markdown 文档、历次判决、模块清单、截断标记、通过标记与摘要写入 `Task.result`。每个模块最多三次尝试；全部模块通过时任务状态 MUST 为 `completed`，任一模块三次尝试都未通过 MUST 为 `failed`；被用户关闭时 MUST 为 `cancelled` 且不得被后台线程回写成完成。

`Task.result.modules` MUST 为每个模块给出 `key`、`name`、`start_line`、`end_line`、`passed`、`truncated`、`document_length` 与 `message`。`Task.result.truncated` MUST 表示是否有模块因输出上限被截断且无法继续拆分。`Task.result.document` MUST 为按模块拼接的 Markdown。

#### Scenario: Accepted document completes task

- **WHEN** 所有模块的编写角色交付文档且验收角色判通过
- **THEN** 任务状态为 `completed`，`Task.result` 含 `passed=true`、合并后的 `document` 全文、`modules` 清单与判决列表

#### Scenario: Rejected document fails task

- **WHEN** 任一模块三次尝试都判不通过
- **THEN** 任务状态为 `failed`，`Task.result` 保留该模块的最后草稿、驳回意见与模块清单，其它已通过模块的文档仍保留

#### Scenario: Truncated module is split

- **WHEN** 某模块的编写输出达到单次上限
- **THEN** 后台执行把该模块拆成更小的模块继续生成，`Task.result.modules` 里能看到子模块与 `truncated` 标记
- **AND** 不再把半截文档送给验收角色

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

### Requirement: 用例编写过程在运行中可见

用例编写流程 MUST 在每条事件交给接收方后立即 flush，使运行中的任务报告能读到已发生的 SOP 步骤、思考块、工具调用与模型调用事件。设备执行任务 MUST 保持原有的批量落库行为。

任务详情页对 `task_kind=case_authoring` 且状态为 `running` / `pending` 的任务 MUST 自动刷新报告（约 3 秒一次），显示「运行中，自动刷新…」；进入 `completed` / `failed` / `cancelled` / `interrupted` 后 MUST 停止轮询。运行中暂无事件时 MUST 显示等待提示，不得呈现空白区块。

`POST /api/tasks/{id}/rerun/` MUST 允许 `failed` 与 `interrupted` 两种终态任务重跑；重跑生成的新任务沿用原 `task_kind` 与附件。

#### Scenario: 运行中打开报告

- **WHEN** 用户打开一个正在执行的 Agent-02 任务报告
- **THEN** 页面显示「运行中，自动刷新…」，事件流随任务推进自动出现新事件
- **AND** 任务结束后停止刷新，保留完整事件流

#### Scenario: 中断任务可重跑

- **WHEN** 任务因后端重启被标记为 `interrupted`
- **THEN** 任务卡提供「重新执行」，点击后克隆附件并重新进入执行

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
