## Purpose

把家电测试用例编写做成 AI 助手里可选的 Agent-02 任务：选择 Agent-02 后上传 PRD/Word 文档，后台解析并调用用例编写/验收流程，生成结果进入任务清单与测试报告。

## ADDED Requirements

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

后台执行 MUST 按 `Task.task_kind` 分流：`case_authoring` MUST 拼接任务文档为一个需求正文，调用用例编写角色与验收角色组成的一步 SOP（最多两次尝试），把生成的完整 Markdown 文档、历次判决、通过标记与摘要写入 `Task.result`。全部通过时任务状态 MUST 为 `completed`，否则 MUST 为 `failed`；被用户关闭时 MUST 为 `cancelled` 且不得被后台线程回写成完成。

#### Scenario: Accepted document completes task

- **WHEN** 编写角色交付文档且验收角色判通过
- **THEN** 任务状态为 `completed`，`Task.result` 含 `passed=true`、`document` 全文与判决列表

#### Scenario: Rejected document fails task

- **WHEN** 验收角色两次都判不通过
- **THEN** 任务状态为 `failed`，`Task.result` 保留最后一次草稿与驳回意见

### Requirement: Report displays generated test cases

测试报告列表 MUST 包含用例编写任务，并下发 `task_kind` 供前端显示「类型」。任务详情报告 `GET /api/tasks/{id}/report/` 对用例编写任务 MUST 返回 `document`（完整 Markdown）、`documents`（上传文档名）与 `conclusion.verdicts`（判决列表），MUST NOT 伪造设备用例轮次。任务详情页 MUST 在渲染 Markdown 前做 HTML 净化。

#### Scenario: Report detail shows the document

- **WHEN** 用户点击一个已完成的用例编写任务
- **THEN** 详情页展示「生成的测试用例」Markdown 文档与「验收意见」，不显示设备执行用例轮次

#### Scenario: Report list distinguishes task kind

- **WHEN** 用户打开测试报告列表
- **THEN** 每行带「类型」列，用例编写任务显示「用例编写」，设备任务显示「设备执行」
