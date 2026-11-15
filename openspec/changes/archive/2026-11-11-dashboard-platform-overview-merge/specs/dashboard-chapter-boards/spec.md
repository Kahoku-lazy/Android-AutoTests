## RENAMED Requirements

- FROM: `### Requirement: Dashboard content is organized into four chapter boards`
- TO: `### Requirement: Dashboard content is organized into three chapter boards`

## MODIFIED Requirements

### Requirement: Dashboard content is organized into three chapter boards

仪表盘主内容区 SHALL 将原有同权多段分区收束为恰好三个章节钉板，顺序为：平台概览、AI 用量、趋势与动态。「平台概览」SHALL 在同一章节内同时承载平台运行指标组（在线设备、活跃智能体、运行中任务、任务数量、工作流）与测试用例资产子区（「测试用例」子标题 + 用例项目入口卡），两组之间 MUST 以子标题分隔，MUST NOT 拆成两个独立同权章节。每个章节 SHALL 使用页面级分区容器（`.doc-section` 或其 doodle 章节变体），MUST NOT 用 `AppCard` 充当章节外壳。「平台概览」的用例子区 MUST 只呈现用例类 KPI，MUST NOT 再呈现元素类 KPI 或元素统计卡（元素定位已退役）。

#### Scenario: Four chapters render in order

- **WHEN** 用户打开仪表盘且统计数据可展示（含全零占位）
- **THEN** 主内容区自上而下出现三个章节，标题文案分别为「平台概览」「AI 用量」「趋势与动态」
- **AND** 页面不再出现独立的「平台运营」或「测试资产」章节标题

#### Scenario: Cases and elements share one asset chapter

- **WHEN** 用户查看「平台概览」章节
- **THEN** 章节内先出现在线设备、活跃智能体、运行中任务、任务数量、工作流五张运行指标卡
- **AND** 其下出现「测试用例」子标题与用例项目入口卡
- **AND** 不出现元素类 KPI、元素统计卡或「Android元素」文案

### Requirement: Chapter headers omit summary chips

仪表盘章节头 MUST NOT 再呈现 chip 摘要行。「平台概览」章节头 MUST NOT 展示设备、智能体、任务、工作流汇总 chip；「AI 用量」章节头 MUST NOT 展示「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip。章节层级 MUST 由模块色方标、英文 eyebrow 与中文标题表达，MUST NOT 依赖灰色圆角 pill。`ai_usage.by_role` 仍可保留在统计接口中，但 MUST NOT 用于章节头 chip。「平台概览」章节头右侧的用例数 chip 不受本条约束，且 MUST 是该章节头唯一允许出现的 chip。

#### Scenario: 平台运营章节头不再有汇总 chip

- **WHEN** 用户打开仪表盘并查看「平台概览」章节头
- **THEN** 章节头只有模块色方标、中文标题与描述
- **AND** 不存在设备、智能体、任务或工作流数量的 chip

#### Scenario: AI 用量章节头不再有角色 chip

- **WHEN** 用户打开仪表盘并查看「AI 用量」章节头
- **THEN** 页面不存在「角色·累计」「角色·今日」或语义等价的分角色 Token 摘要 chip

#### Scenario: 测试资产用例 chip 保留

- **WHEN** 用户查看「平台概览」章节头右侧
- **THEN** 用例数量 chip 仍然可见

### Requirement: Platform ops chapter includes task count card

仪表盘「平台概览」章节的运行指标组 SHALL 按顺序展示在线设备、活跃智能体、运行中任务、任务数量、工作流五张 KPI 卡。任务数量卡的数据 MUST 取自当前用户可见任务的累计数量，MUST 保留整卡点击进入任务清单页（`/tasks`）。该卡 MUST 同时展示今日任务数作为副标题。这五张卡 MUST NOT 渲染独立「进入」按钮或同类进入控件，跳转 MUST 只能由整卡激活触发。

#### Scenario: 平台运营五卡顺序

- **WHEN** 用户打开仪表盘并查看「平台概览」章节的运行指标组
- **THEN** 按顺序出现「在线设备」「活跃智能体」「运行中任务」「任务数量」「工作流」五张卡，且「任务数量」不再出现在「AI 用量」章节

#### Scenario: 任务数量卡无独立进入按钮

- **WHEN** 用户查看「任务数量」卡
- **THEN** 卡内不存在「进入」按钮，点击整卡仍可进入任务清单页

#### Scenario: 其余四张平台运营卡同样无独立进入按钮

- **WHEN** 用户查看「在线设备」「活跃智能体」「运行中任务」「工作流」四张卡
- **THEN** 四张卡内均不存在「进入」按钮（`.kpi-card__enter`）
- **AND** 点击卡面仍分别进入设备页、智能体页、报告页、工作流页

### Requirement: Chapter shells are solid while metric cards stay dashed

仪表盘三个章节板（平台概览 / AI 用量 / 趋势与动态）的外壳描边 SHALL 为墨色实线，MUST NOT 覆写全局 `.doc-section` 的实线线型；章节头分隔线与子标题分隔线 SHALL 同为实线。

章节外壳内的 KPI 指标卡、智能体用量卡与趋势 `AppCard` SHALL 保留既有手绘虚线卡壳，MUST NOT 因章节外壳改线型而一起变成实线。

#### Scenario: Chapter shells render solid borders

- **WHEN** 用户打开仪表盘并查看三个章节板
- **THEN** 每个章节外壳为墨色实线描边，仍保留模块色硬偏移阴影
- **AND** 章节头与子标题的分隔线为实线

#### Scenario: Metric cards keep their dashed shells

- **WHEN** 用户查看「平台概览」的在线设备、活跃智能体等运行指标卡与用例项目卡，或「AI 用量」的账单卡与智能体用量卡
- **THEN** 这些卡片仍呈现虚线描边、近直角与硬偏移色阴影
