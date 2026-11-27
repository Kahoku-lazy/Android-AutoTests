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

任务清单页的单张任务卡 MUST 展示标题（无标题时用目标）、状态、创建时间、设备、助手名、费用、耗时与附件名。失败任务卡 MUST 提供「重新执行」，运行中任务卡 MUST 提供「关闭」。任务卡 MUST NOT 提供「详情」入口，也 MUST NOT 跳转 `/tasks/:id`——该路由已下线，与 `dashboard-agent-tasks` 的「MUST NOT 进入已下线的 `/tasks/:id`」口径一致。任务卡 MUST NOT 展示目标全文。

#### Scenario: Card fields

- **WHEN** 用户查看任务清单中的一张任务卡
- **THEN** 卡面可见标题、状态、创建时间、设备、助手、费用、耗时与附件名，且不展示目标全文

#### Scenario: Failed and running actions

- **WHEN** 任务卡状态为失败或运行中
- **THEN** 失败卡可见「重新执行」，运行中卡可见「关闭」

#### Scenario: Detail navigation

- **WHEN** 用户查看任务卡并尝试进入详情
- **THEN** 卡面没有「详情」入口，页面不跳转 `/tasks/:id`
- **AND** 任务卡的激活点击只停留在 `/tasks`

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

### Requirement: 任务行展示冻结的编排与种类

任务清单表格的一行 MUST 展示该任务创建时冻结的编排与种类。编排文案 MUST 分别为「SOP」「目标」「团队」。种类文案 MUST 分别为「UI 自动化」「用例编写」「需求拆解」。系统 MUST NOT 用工作流当前配置覆盖历史行。Goal 与 Team 没有设备时，设备列 MUST 显示「—」。需求拆解没有用户上传附件时，附件列 MUST 显示「—」；平台用例编译出的执行 YAML 仍 MUST 在 UI 自动化行显示其文件名。

#### Scenario: 三种任务各显示自己的种类

- **WHEN** 表格同时有 UI 自动化、用例编写和需求拆解三条记录
- **THEN** 三行分别显示对应的编排与种类文案

#### Scenario: 拆解行不显示设备和附件

- **WHEN** 用户查看一条没有设备、也没有用户附件的需求拆解记录
- **THEN** 设备列与附件列都显示「—」

### Requirement: 已结束任务都可以重新执行

任务清单 SHALL 在成功、失败、取消和已中断的行提供「重新执行」。待执行与执行中的行 MUST NOT 提供该操作。运行中的行 MUST 仍提供「关闭」。

#### Scenario: 成功和取消可以再执行

- **WHEN** 用户查看状态为成功或取消的任务行
- **THEN** 行内可见「重新执行」

#### Scenario: 执行中不能重新执行

- **WHEN** 用户查看状态为执行中的任务行
- **THEN** 行内可见「关闭」
- **AND** 不可见「重新执行」

### Requirement: 失败任务可打开本次运行的报告

任务行状态为 `failed` 且结果里带 `report_run` 与 `report_name` 时，任务清单 MUST 在该行提供「报告」入口，点击 MUST 直接打开本次运行的 HTML 报告，MUST NOT 要求先进入任务详情页。

结果里缺少任一定位时，该行 MUST NOT 显示「报告」入口，MUST NOT 报错，也 MUST NOT 留下点击无反应的空白操作。

#### Scenario: 异常中断的失败任务可打开报告

- **WHEN** 一条任务因运行中异常中断进入 `failed`，结果里带 `report_run` 与 `report_name`
- **THEN** 该行显示「报告」入口，点击打开本次运行的 HTML 报告

#### Scenario: 没有报告的失败任务不显示入口

- **WHEN** 一条任务在起跑前就失败，结果里没有报告定位
- **THEN** 该行不显示「报告」入口
- **AND** 页面其余行与操作保持可用

### Requirement: 任务行展示创建人

任务清单表格的一行 MUST 展示提交该任务的账号名，供多人共用平台时分辨任务归属。账号名 MUST 在读取时按该任务记录的提交人解析，系统 MUST NOT 为此新增或改写任务表字段，MUST NOT 冻结提交时的账号名。提交人标识为空、或该账号已注销导致解析不出账号名时，该行 MUST 显示「—」，MUST NOT 显示原始用户标识、MUST NOT 留空、MUST NOT 报错或让该行其余字段与操作失效。该列 MUST 为只读展示。

#### Scenario: 工作流提交的任务显示提交人账号名

- **WHEN** 用户以账号 `admin` 登录并通过工作流提交一条任务，随后打开任务清单
- **THEN** 该任务行的「创建人」显示 `admin`

#### Scenario: 多账号提交的任务各显示自己的创建人

- **WHEN** 任务清单里同时有 `admin` 与 `Kahoku` 两个账号提交的任务
- **THEN** 各行「创建人」分别显示各自提交账号名，不出现串行或成片的空白

#### Scenario: 没有提交人或账号已注销

- **WHEN** 一条任务的提交人标识为空，或提交人账号已注销
- **THEN** 该行「创建人」显示「—」，该行其余字段与操作（重新执行、关闭、报告）仍然可用

#### Scenario: 账号改名后历史行跟随当前账号名

- **WHEN** 某账号改名后，用户查看该账号此前提交的任务
- **THEN** 这些任务行的「创建人」显示改名后的账号名

### Requirement: 创建人以渐变标签呈现

任务行的创建人 MUST 以标签形态呈现，MUST NOT 只显示纯文本。标签底色 MUST 为同色系两档渐变，边框、底色与前景 MUST 引用既有设计令牌，MUST NOT 直接写色值字面量，MUST NOT 为本次改动新增颜色令牌。标签内 MUST 同时包含账号名文本与一个同色圆点标记，MUST NOT 只显示色块——颜色 MUST NOT 成为区分账号的唯一手段。账号名超出列宽时 MUST 在标签内省略展示并保留可查看完整名称的悬浮提示，MUST NOT 撑破表格列或挤掉相邻列。没有账号名时 MUST NOT 渲染彩色标签，按原口径显示「—」。

#### Scenario: 标签带渐变底色与同色圆点

- **WHEN** 用户查看任务清单中一条有创建人的任务行
- **THEN** 该行「创建人」是一个带渐变色底与同色圆点的标签，标签内可读到账号名

#### Scenario: 长账号名不撑破列

- **WHEN** 创建人账号名超过列宽
- **THEN** 标签内文本省略显示，鼠标悬浮可看到完整账号名，表格列宽与相邻列不受影响

#### Scenario: 没有创建人时不套彩色标签

- **WHEN** 一条任务没有可解析的创建人
- **THEN** 该行「创建人」是纯文本「—」，不出现彩色标签、不出现孤立圆点

### Requirement: 不同账号的创建人标签取不同彩笔色

创建人标签的颜色 MUST 由账号名确定性映射到平台既有彩笔令牌：同一账号名 MUST 恒定映射同一颜色（忽略大小写与首尾空白），MUST NOT 因刷新、翻页、其它账号增减而改变。不同账号 SHOULD 取到不同颜色；颜色池为平台 9 支彩笔，出现映射碰撞时 MUST 仍以账号名文本为准，MUST NOT 影响可读与识别。映射 MUST NOT 新增或改写设计令牌。

#### Scenario: 两个账号显示两种颜色

- **WHEN** 任务清单里同时有 `admin` 与 `kahoku` 提交的任务
- **THEN** 两行的创建人标签底色不同，可直接凭颜色分辨账号

#### Scenario: 同一账号颜色稳定

- **WHEN** 用户刷新页面、切换分页，或重新登录后再看
- **THEN** 同一账号的创建人标签始终是同一颜色

#### Scenario: 大小写与首尾空白不影响配色

- **WHEN** 同一账号在不同数据里出现为 `kahoku`、`Kahoku` 或 ` kahoku `
- **THEN** 三者映射到同一颜色
