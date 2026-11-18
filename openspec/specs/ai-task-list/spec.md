# ai-task-list Specification

## Purpose
把 AI 任务卡片从「平台小助手」看板拆成独立的「任务清单」页，并在侧栏 AI任务 分组提供稳定入口；任务创建、筛选、重跑、关闭与详情沿用既有契约。

## Requirements

### Requirement: Task list page hosts the task board

系统 SHALL 在 `/tasks` 提供「任务清单」页，页头标题 MUST 为「任务清单」。该页 MUST 承载任务卡片区块，包含筛选标签、按状态分组、新建任务、调试清空、任务卡列表与详情入口。平台小助手页 MUST NOT 再渲染任务卡片区块，只保留小助手线路与身份看板。任务提交、重跑、关闭与清空的接口契约 MUST 保持不变。

#### Scenario: 打开任务清单页

- **WHEN** 用户访问 `/tasks`
- **THEN** 页头显示「任务清单」，页面包含任务卡片区块，可筛选、按状态分组、新建任务并进入详情

#### Scenario: 平台小助手不再承载任务卡片

- **WHEN** 用户打开平台小助手页
- **THEN** 页面只有小助手线路与身份看板，不出现任务卡片区块或「新建任务」入口

### Requirement: Sidebar AI task group exposes task list first

侧栏「AI任务」分组 SHALL 按顺序展示「任务清单」「用例管理」「BUG单管理」「测试报告」，路径 MUST 分别为 `/tasks`、`/cases`、`/bugs`、`/reports`。任务清单入口 MUST 只在 `/tasks` 高亮，MUST NOT 与「AI 助手」入口同时高亮。

#### Scenario: AI task group order

- **WHEN** 用户查看侧栏「AI任务」分组
- **THEN** 自上而下依次为「任务清单」「用例管理」「BUG单管理」「测试报告」

#### Scenario: Task list active state

- **WHEN** 用户位于 `/tasks`
- **THEN** 只有「任务清单」显示激活态，「AI 助手」不显示激活态

### Requirement: Task list card content and actions

任务清单页的单张任务卡 MUST 展示标题（无标题时用目标）、状态、创建时间、设备、助手名、费用、耗时与附件名。失败任务卡 MUST 提供「重新执行」，运行中任务卡 MUST 提供「关闭」，每张卡 MUST 提供「详情」，且「详情」MUST 进入 `/tasks/:id`。任务卡 MUST NOT 展示目标全文。

#### Scenario: Card fields

- **WHEN** 用户查看任务清单中的一张任务卡
- **THEN** 卡面可见标题、状态、创建时间、设备、助手、费用、耗时与附件名，且不展示目标全文

#### Scenario: Failed and running actions

- **WHEN** 任务卡状态为失败或运行中
- **THEN** 失败卡可见「重新执行」，运行中卡可见「关闭」

#### Scenario: Detail navigation

- **WHEN** 用户点击任务卡的「详情」
- **THEN** 路由进入 `/tasks/:id`

### Requirement: Task card names the SOP kind

任务清单页的任务卡 MUST 按任务类型显示三类文案：设备执行、用例编写、SOP。类型为 `assistant_sop` 时 MUST 显示「SOP」，MUST NOT 显示成设备执行。其它类型的既有文案 MUST 保持不变。

#### Scenario: SOP 任务显示 SOP

- **WHEN** 用户在任务清单查看一条 `assistant_sop` 任务
- **THEN** 该卡类型文案为「SOP」

#### Scenario: 设备任务不被改名

- **WHEN** 用户查看一条设备执行任务
- **THEN** 该卡类型文案仍为「设备执行」

### Requirement: SOP submit success offers a task list link

从工作流提交一条 SOP 任务成功后，系统 MUST 留在当前页，并在成功提示中提供进入 `/tasks` 的链接。系统 MUST NOT 因提交成功而自动离开当前页。提交字段与提交接口 MUST 保持不变。

#### Scenario: 成功后只给链接

- **WHEN** 用户在工作流任务弹窗提交成功
- **THEN** 当前页仍是助手页，成功提示含可进入任务清单的链接

#### Scenario: 不自动跳转

- **WHEN** 提交成功且用户没有点击该链接
- **THEN** 路由不进入 `/tasks`
