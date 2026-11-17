# dashboard-chapter-boards Specification

## Purpose
定义仪表盘「章节钉板」信息架构：将平台概览、AI 用量、趋势动态收束为可扫描的三章节容器，以模块色方标、英文 eyebrow 与中文标题表达分区层级；平台概览章节同时承载设备、平台助手、工作流、运行中任务与任务数量五张入口卡，以及「测试用例」资产子区，使视觉与 Hand-Drawn Doodle 主题一致。

## Requirements

### Requirement: Dashboard content is organized into three chapter boards

仪表盘主内容区 SHALL 将原有同权多段分区收束为恰好三个章节钉板，顺序为：平台概览、AI 用量、趋势与动态。「平台概览」SHALL 在同一章节内同时承载平台运行指标组（在线设备、平台助手、工作流、运行中任务、任务数量）、仅运营可见的运营配置子区，以及测试用例资产子区（「测试用例」子标题 + 用例项目入口卡）。运行指标组、运营配置子区与用例子区之间 MUST 以子标题分隔，MUST NOT 拆成独立同权章节。每个章节 SHALL 使用页面级分区容器（`.doc-section` 或其 doodle 章节变体），MUST NOT 用 `AppCard` 充当章节外壳。「平台概览」的用例子区 MUST 只呈现用例类 KPI，MUST NOT 再呈现元素类 KPI 或元素统计卡（元素定位已退役）。系统 MUST NOT 再展示「活跃智能体」卡。

#### Scenario: Three chapters render in order

- **WHEN** 用户打开仪表盘且统计数据可展示（含全零占位）
- **THEN** 主内容区自上而下出现三个章节，标题文案分别为「平台概览」「AI 用量」「趋势与动态」
- **AND** 页面不再出现独立的「平台运营」或「测试资产」章节标题

#### Scenario: Overview chapter holds runtime metrics and case assets

- **WHEN** 用户查看「平台概览」章节
- **THEN** 章节内先出现在线设备、平台助手、工作流、运行中任务、任务数量五张运行指标卡
- **AND** 其下出现「测试用例」子标题与用例项目入口卡
- **AND** 不出现「活跃智能体」、元素类 KPI、元素统计卡或「Android元素」文案

### Requirement: Chapter headers expose hierarchy with doodle cues

每个章节头 SHALL 同时包含：模块色方标（或等价图标块）、英文 eyebrow、中文标题（可用 marker 高亮），MUST NOT 仅依赖灰色圆角 pill 作为主层级信号。

#### Scenario: Chapter head is scannable

- **WHEN** 用户浏览任一章节头
- **THEN** 可见英文 eyebrow、中文标题与彩色方标；章节容器带实线描边与硬色偏移阴影（钉板语义）

### Requirement: Existing KPI cards and APIs remain the data surface
章节重组 MUST NOT 把仪表盘改成可写运营台：KPI 入口卡、趋势 `AppCard`、活动时间线仍直映只读 stats/activities 接口。系统 MUST 继续只请求既有仪表盘统计与活动只读接口，MUST NOT 为展示测试资产而新增写操作或在前端推算业务指标。`cases.breakdown` SHALL 按当前用户的用例项目维度返回（每项含项目标识、名称与用例数）；MUST NOT 再要求该字段保持测试类型拆分或与重组前类型键一一对应。`cases.total` SHALL 仍为当前用户文档用例合计。元素类 KPI 的数据源字段随元素定位退役一并移除，统计响应 MUST NOT 再包含元素或元素页面计数。

#### Scenario: Stats endpoints unchanged
- **WHEN** 完成本变更后打开仪表盘
- **THEN** 仍只请求既有仪表盘统计与活动只读接口
- **AND** 测试用例子区的项目卡数值来自该次统计响应中的 `cases.breakdown` 项目项，而不是前端另行请求用例项目列表后再本地拼卡

#### Scenario: Case totals still match project rows
- **WHEN** 统计响应同时给出 `cases.total` 与项目维度 `cases.breakdown`
- **THEN** `cases.total` 等于各项目用例数之和（无项目时为 0）

### Requirement: Chapter headers omit summary chips

仪表盘章节头 MUST NOT 再呈现 chip 摘要行。「平台概览」章节头 MUST NOT 展示设备、智能体、任务、工作流汇总 chip；「AI 用量」章节头 MUST NOT 展示「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip。章节层级 MUST 由模块色方标、英文 eyebrow 与中文标题表达，MUST NOT 依赖灰色圆角 pill。`ai_usage.by_role` 仍可保留在统计接口中，但 MUST NOT 用于章节头 chip。「平台概览」章节头右侧的用例数 chip 不受本条约束，且 MUST 是该章节头唯一允许出现的 chip。

#### Scenario: 平台概览章节头不再有汇总 chip

- **WHEN** 用户打开仪表盘并查看「平台概览」章节头
- **THEN** 章节头只有模块色方标、中文标题与描述
- **AND** 不存在设备、智能体、任务或工作流数量的 chip

#### Scenario: AI 用量章节头不再有角色 chip

- **WHEN** 用户打开仪表盘并查看「AI 用量」章节头
- **THEN** 页面不存在「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip

#### Scenario: 平台概览用例 chip 保留

- **WHEN** 用户查看「平台概览」章节头右侧
- **THEN** 用例数量 chip 仍然可见

### Requirement: Platform ops chapter includes task count card

仪表盘「平台概览」章节的运行指标组 SHALL 按顺序展示在线设备、平台助手、工作流、运行中任务、任务数量五张 KPI 卡。平台助手卡的主数值 MUST 为助手名片总数，工作流卡的主数值 MUST 为工作流总数；两张卡 MUST 整卡进入平台助手页（`/ai-assistant`）。运行中任务卡的主数值 MUST 只计状态为 `running` 的工作流任务，副标题 MUST 固定为「排队 N」，其中 N 为状态为 `pending` 的工作流任务数（含 0）；该卡 MUST 整卡进入任务清单页（`/tasks`）。任务数量卡的主数值 MUST 为工作流任务累计数量，副标题 MUST 为今日新建的工作流任务数，MUST 整卡进入任务清单页。这五张卡 MUST NOT 渲染独立「进入」按钮或同类进入控件，跳转 MUST 只能由整卡激活触发。系统 MUST NOT 把已退役的设备执行或用例编写任务计入运行中、排队或任务数量。

#### Scenario: 平台概览五卡顺序

- **WHEN** 用户打开仪表盘并查看「平台概览」章节的运行指标组
- **THEN** 按顺序出现「在线设备」「平台助手」「工作流」「运行中任务」「任务数量」五张卡
- **AND** 不出现「活跃智能体」，且「任务数量」不再出现在「AI 用量」章节

#### Scenario: 任务数量卡无独立进入按钮

- **WHEN** 用户查看「任务数量」卡
- **THEN** 卡内不存在「进入」按钮，点击整卡仍可进入任务清单页
- **AND** 主数值不含已退役任务类型

#### Scenario: 其余四张运行指标卡同样无独立进入按钮

- **WHEN** 用户查看「在线设备」「平台助手」「工作流」「运行中任务」四张卡
- **THEN** 四张卡内均不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 点击卡面分别进入设备页、平台助手页、平台助手页、任务清单页

#### Scenario: 平台助手与工作流分别计数

- **WHEN** 平台上有 3 张助手名片和 2 条工作流
- **THEN** 「平台助手」显示 3，「工作流」显示 2
- **AND** 点击任一张卡进入平台助手页

#### Scenario: 运行中任务只计执行中并显示排队

- **WHEN** 工作流任务中有 1 条 `running`、2 条 `pending`，另有已退役类型的任务也在执行
- **THEN** 「运行中任务」主数值为 1，副标题为「排队 2」
- **AND** 点击整卡进入任务清单页

#### Scenario: 没有排队时仍显示零

- **WHEN** 工作流任务中没有 `pending`
- **THEN** 「运行中任务」副标题仍为「排队 0」

### Requirement: Overview inserts an operator-only configuration group

「平台概览」SHALL 在运行指标组与「测试用例」子区之间放置「运营配置」子区。该子区 MUST 只在当前用户为超级管理员或运营时渲染，MUST 以子标题与运行指标组、用例子区分隔。普通用户 MUST NOT 看到该子标题或其中任何卡片。

#### Scenario: 运营在运行指标与用例之间看到运营配置

- **WHEN** 超级管理员或运营打开仪表盘并查看「平台概览」
- **THEN** 「运营配置」子标题出现在五张运行指标卡之后、「测试用例」子标题之前

#### Scenario: 普通用户看不到运营配置子区

- **WHEN** 普通用户打开仪表盘并查看「平台概览」
- **THEN** 不出现「运营配置」子标题
- **AND** 运行指标组之后直接是「测试用例」子区

### Requirement: Chapter shells are solid while metric cards stay dashed

仪表盘三个章节板（平台概览 / AI 用量 / 趋势与动态）的外壳描边 SHALL 为墨色实线，MUST NOT 覆写全局 `.doc-section` 的实线线型；章节头分隔线与子标题分隔线 SHALL 同为实线。

章节外壳内的 KPI 指标卡、智能体用量卡与趋势 `AppCard` SHALL 保留既有手绘虚线卡壳，MUST NOT 因章节外壳改线型而一起变成实线。

#### Scenario: Chapter shells render solid borders

- **WHEN** 用户打开仪表盘并查看三个章节板
- **THEN** 每个章节外壳为墨色实线描边，仍保留模块色硬偏移阴影
- **AND** 章节头与子标题的分隔线为实线

#### Scenario: Metric cards keep their dashed shells

- **WHEN** 用户查看「平台概览」的在线设备、平台助手等运行指标卡与用例项目卡，或「AI 用量」的账单卡与智能体用量卡
- **THEN** 这些卡片仍呈现虚线描边、近直角与硬偏移色阴影
