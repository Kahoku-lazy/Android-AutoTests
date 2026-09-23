## Purpose

定义仪表盘「测试资产」章节中测试用例子区的可见行为：入口卡按当前用户的用例项目逐张展示，计数与项目增删同源，不再按 Android / Web / API / 功能业务等测试类型切分。

## ADDED Requirements

### Requirement: Case KPI cards are one per case-manager project
仪表盘「测试资产」章节的测试用例子区 SHALL 为当前用户可见的每一个用例项目渲染一张 KPI 入口卡。卡片标题 SHALL 为项目名称，主数值 SHALL 为该项目下文档用例条数（含 0）。系统 MUST NOT 再以 Android用例、Web用例、API用例、功能业务（或语义等价的固定类型标签）作为该子区的入口卡。

#### Scenario: Projects render as case cards
- **WHEN** 当前用户拥有至少一个用例项目，且仪表盘统计已成功返回
- **THEN** 测试用例子区出现与项目数量相同的入口卡
- **AND** 每张卡的标题为对应项目名称，主数值为该项目用例数
- **AND** 页面上不可见文案「Android用例」「Web用例」「功能业务」作为该子区入口卡标题

#### Scenario: Zero-case project still has a card
- **WHEN** 用户刚创建了一个尚无用例的项目，并再次打开或刷新仪表盘
- **THEN** 测试用例子区出现以该项目名称命名的入口卡，主数值为 0

### Requirement: Case card enters the matching project workspace
测试用例子区每张项目卡 SHALL 导航到该项目的用例工作台。MUST NOT 把所有项目卡统一指向无项目上下文的通用 `/cases` 列表（可作为空态入口，不得作为已有项目卡的目标）。

#### Scenario: Clicking a project card opens that project
- **WHEN** 用户点击名称为某已存在项目的用例入口卡
- **THEN** 进入该项目工作台（路径含该项目 id）

### Requirement: Cards stay in sync with project create and delete
测试用例子区的卡片集合 SHALL 与当前用户的用例项目集合一致：新增项目后再次加载仪表盘统计 MUST 出现对应卡片；删除项目后再次加载 MUST 不再出现该项目卡片。同步 SHALL 通过既有仪表盘只读统计接口完成，MUST NOT 依赖前端在仪表盘页额外请求用例项目列表接口，MUST NOT 新增 WebSocket 写通道。

#### Scenario: New project appears after dashboard reload
- **WHEN** 用户在用例模块新建项目，随后打开或刷新仪表盘且统计请求成功
- **THEN** 测试用例子区包含该新建项目的入口卡

#### Scenario: Deleted project card disappears
- **WHEN** 用户删除某用例项目，随后打开或刷新仪表盘且统计请求成功
- **THEN** 测试用例子区不再出现以该已删项目为标题的入口卡

### Requirement: Empty project set shows empty state without type placeholders
当当前用户没有任何用例项目时，测试用例子区 SHALL 展示空态（可引导前往用例模块），MUST NOT 渲染四张类型占位卡。

#### Scenario: No projects
- **WHEN** 当前用户用例项目数为 0，且仪表盘可展示
- **THEN** 测试用例子区无 Android / Web / API / 功能业务入口卡
- **AND** 可见空态说明，并可进入用例模块
